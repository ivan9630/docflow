"""
Service OCR + NER — DocuFlow v2
Pipeline : Prétraitement image → Tesseract → spaCy NER → Extraction regex
"""
import re, io, tempfile
from typing import Optional
import numpy as np
from PIL import Image, ImageEnhance
import cv2
import pytesseract
import pdfplumber
from pdf2image import convert_from_bytes
import structlog

logger = structlog.get_logger()

TESS_CONFIG = r'--oem 3 --psm 6 -l fra+eng'

# Charger spaCy NER (silencieux si non dispo)
try:
    import spacy
    nlp_fr = spacy.load("fr_core_news_sm")
    NLP_AVAILABLE = True
except Exception:
    NLP_AVAILABLE = False
    logger.warning("spaCy non disponible — NER désactivé")


# ── PRÉTRAITEMENT IMAGE ───────────────────────────────────────────

def preprocess(img: Image.Image) -> Image.Image:
    """Pipeline de prétraitement pour améliorer l'OCR sur docs scannés."""
    arr = np.array(img)
    # Niveaux de gris
    if len(arr.shape) == 3:
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    else:
        gray = arr
    # Débruitage
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    # Redressement (deskew léger)
    coords = np.column_stack(np.where(denoised < 200))
    if len(coords) > 100:
        angle = cv2.minAreaRect(coords)[-1]
        if abs(angle) < 45:
            (h, w) = denoised.shape
            M = cv2.getRotationMatrix2D((w//2, h//2), angle if angle < -45 else angle, 1.0)
            denoised = cv2.warpAffine(denoised, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    # Binarisation Otsu
    _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # Netteté
    kernel = np.array([[0,-1,0],[-1,5,-1],[0,-1,0]])
    sharp = cv2.filter2D(binary, -1, kernel)
    return Image.fromarray(sharp)


# ── EXTRACTION OCR ────────────────────────────────────────────────

def ocr_from_pdf(content: bytes) -> dict:
    """Extraction hybride : texte natif puis fallback OCR."""
    # Tentative texte natif
    try:
        tmp = _tmp_file(content, ".pdf")
        with pdfplumber.open(tmp) as pdf:
            pages = [p.extract_text() or "" for p in pdf.pages]
        text = "\n\n".join(pages)
        if len(text.strip()) > 100:
            return {"text": text, "pages": pages, "method": "pdfplumber", "confidence": 0.96}
    except Exception as e:
        logger.warning(f"pdfplumber: {e}")

    # Fallback OCR
    try:
        images = convert_from_bytes(content, dpi=300)
        pages, confs = [], []
        for img in images:
            pp = preprocess(img)
            data = pytesseract.image_to_data(pp, config=TESS_CONFIG, output_type=pytesseract.Output.DICT)
            conf_vals = [int(c) for c in data['conf'] if str(c) != '-1']
            confs.append(sum(conf_vals) / len(conf_vals) if conf_vals else 0)
            pages.append(pytesseract.image_to_string(pp, config=TESS_CONFIG))
        return {
            "text": "\n\n".join(pages), "pages": pages,
            "method": "tesseract", "confidence": sum(confs)/len(confs)/100 if confs else 0.5
        }
    except Exception as e:
        logger.error(f"OCR failed: {e}")
        return {"text": "", "pages": [], "method": "failed", "confidence": 0.0}


def ocr_from_image(content: bytes) -> dict:
    try:
        img = Image.open(io.BytesIO(content))
        pp = preprocess(img)
        data = pytesseract.image_to_data(pp, config=TESS_CONFIG, output_type=pytesseract.Output.DICT)
        confs = [int(c) for c in data['conf'] if str(c) != '-1']
        conf = sum(confs) / len(confs) / 100 if confs else 0.5
        text = pytesseract.image_to_string(pp, config=TESS_CONFIG)
        return {"text": text, "pages": [text], "method": "tesseract_img", "confidence": conf}
    except Exception as e:
        logger.error(f"Image OCR: {e}")
        return {"text": "", "pages": [], "method": "failed", "confidence": 0.0}


# ── NER SPACY ─────────────────────────────────────────────────────

def extract_ner(text: str) -> dict:
    """Extraction d'entités nommées avec spaCy."""
    if not NLP_AVAILABLE or not text:
        return {"organizations": [], "dates": [], "locations": [], "persons": []}
    doc = nlp_fr(text[:100000])
    return {
        "organizations": list({ent.text for ent in doc.ents if ent.label_ in ("ORG","MISC")}),
        "dates":         list({ent.text for ent in doc.ents if ent.label_ == "DATE"}),
        "locations":     list({ent.text for ent in doc.ents if ent.label_ in ("LOC","GPE")}),
        "persons":       list({ent.text for ent in doc.ents if ent.label_ == "PER"}),
    }


# ── EXTRACTEURS REGEX ─────────────────────────────────────────────

def extract_siren(text: str) -> Optional[str]:
    for p in [r'SIREN\s*:?\s*(\d{3}[\s]?\d{3}[\s]?\d{3})', r'\b(\d{9})\b']:
        m = re.search(p, text, re.I)
        if m:
            v = re.sub(r'\s','', m.group(1))
            if _luhn(v): return v
    return None


def extract_siret(text: str) -> Optional[str]:
    for p in [r'SIRET\s*:?\s*(\d{3}[\s]?\d{3}[\s]?\d{3}[\s]?\d{5})', r'\b(\d{14})\b']:
        m = re.search(p, text, re.I)
        if m:
            v = re.sub(r'\s','', m.group(1))
            if len(v) == 14: return v
    return None


def extract_tva(text: str) -> Optional[str]:
    m = re.search(r'(?:TVA|N°?\s*TVA)[^:]*:?\s*(FR\s*\d{2}\s*\d{9})', text, re.I)
    if m: return re.sub(r'\s','', m.group(1))
    m = re.search(r'\b(FR\s?\d{11})\b', text, re.I)
    if m: return re.sub(r'\s','', m.group(1))
    return None


def extract_amounts(text: str) -> dict:
    r = {"ht": None, "tva": None, "ttc": None, "taux_tva": None}
    patterns = {
        "ht":  [r'(?:total|montant|sous.total)\s+H\.?T\.?\s*:?\s*([\d\s,.]+)\s*(?:€|EUR)?', r'H\.T\.\s*:?\s*([\d\s,.]+)'],
        "tva": [r'(?:TVA|T\.V\.A\.)[^:]*:?\s*([\d\s,.]+)\s*(?:€|EUR)?'],
        "ttc": [r'(?:total|montant)\s+T\.?T\.?C\.?\s*:?\s*([\d\s,.]+)', r'Net\s+à\s+payer\s*:?\s*([\d\s,.]+)'],
        "taux_tva": [r'TVA\s+([\d,.]+)\s*%', r'Taux\s*:?\s*([\d,.]+)\s*%'],
    }
    for k, pats in patterns.items():
        for p in pats:
            m = re.search(p, text, re.I)
            if m:
                try: r[k] = float(re.sub(r'[\s]','', m.group(1)).replace(',','.')); break
                except: pass
    return r


def extract_iban(text: str) -> Optional[str]:
    m = re.search(r'IBAN\s*:?\s*([A-Z]{2}\d{2}[\s\w]{10,30})', text, re.I)
    if m: return re.sub(r'\s','', m.group(1))[:34]
    m = re.search(r'\b(FR\d{2}(?:\s?\d{4}){5}\s?\d{3})\b', text)
    if m: return re.sub(r'\s','', m.group(1))
    return None


def extract_date(text: str) -> Optional[str]:
    for p in [
        r'(?:Date|du|le)\s*:?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
        r'\b(\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})\b',
        r'\b(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})\b',
    ]:
        m = re.search(p, text, re.I)
        if m: return m.group(1)
    return None


def extract_date_expiration(text: str) -> Optional[str]:
    for p in [
        r'(?:expir|valid|échéance)[^:]*:?\s*(?:le\s+)?(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
        r'(?:valable\s+jusqu)[^:]*:?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
    ]:
        m = re.search(p, text, re.I)
        if m: return m.group(1)
    return None


def extract_doc_number(text: str) -> Optional[str]:
    for p in [
        r'(?:N°?|Numéro|Ref\.?)\s*(?:de\s+)?(?:facture|devis|commande)\s*:?\s*([A-Z0-9\-\/]{3,30})',
        r'(?:Facture|Devis|Bon)\s+N°?\s*:?\s*([A-Z0-9\-\/]{3,30})',
    ]:
        m = re.search(p, text, re.I)
        if m: return m.group(1).strip()
    return None


def extract_company(text: str) -> Optional[str]:
    for p in [
        r'(?:Société|Entreprise|Raison\s+sociale|Émetteur|Emetteur|Prestataire|Fournisseur)\s*:?\s*\n?\s*([^\n]{3,80})',
        r'^([A-Z][A-Z&\s\.\-]{5,60}(?:SAS|SARL|SA|EURL|SNC|EI|SASU))\s*$',
        r'(?:De|From)\s*:?\s*([^\n]{3,80})',
    ]:
        m = re.search(p, text, re.I | re.M)
        if m:
            name = m.group(1).strip()
            # Nettoyer : pas de lignes qui ressemblent à des adresses ou numéros
            if 3 < len(name) < 100 and not re.match(r'^\d', name):
                return name
    return None


def extract_address(text: str) -> dict:
    """Extrait adresse, code postal et ville."""
    addr = {"adresse": None, "code_postal": None, "ville": None}
    # Code postal + ville
    m = re.search(r'\b(\d{5})\s+([A-ZÀ-Ü][a-zà-ü\-\s]{2,40})\b', text)
    if m:
        addr["code_postal"] = m.group(1)
        addr["ville"] = m.group(2).strip()
    # Adresse (ligne avant le code postal)
    for p in [
        r'(?:Adresse|Siège|Domicil)\s*:?\s*\n?\s*([^\n]{5,100})',
        r'(\d{1,4}[\s,]+(?:rue|avenue|boulevard|place|chemin|impasse|allée|passage|route)[^\n]{3,80})',
    ]:
        m = re.search(p, text, re.I)
        if m:
            addr["adresse"] = m.group(1).strip()
            break
    return addr


def extract_all(text: str) -> dict:
    amounts = extract_amounts(text)
    ner = extract_ner(text)
    siren = extract_siren(text)
    siret = extract_siret(text)
    address = extract_address(text)

    # Déduire SIREN du SIRET si pas trouvé
    if not siren and siret and len(siret) == 14:
        siren = siret[:9]

    return {
        "siren":          siren,
        "siret":          siret,
        "tva_number":     extract_tva(text),
        "company_name":   extract_company(text) or (ner["organizations"][0] if ner["organizations"] else None),
        "iban":           extract_iban(text),
        "date":           extract_date(text),
        "date_expiration":extract_date_expiration(text),
        "doc_number":     extract_doc_number(text),
        "montant_ht":     amounts["ht"],
        "montant_tva":    amounts["tva"],
        "montant_ttc":    amounts["ttc"],
        "taux_tva":       amounts["taux_tva"],
        "adresse":        address["adresse"],
        "code_postal":    address["code_postal"],
        "ville":          address["ville"],
        "ner":            ner,
    }


# ── HELPERS ───────────────────────────────────────────────────────

def _luhn(n: str) -> bool:
    try:
        t = 0
        for i, d in enumerate(reversed(n)):
            x = int(d)
            if i % 2 == 1:
                x *= 2
                if x > 9: x -= 9
            t += x
        return t % 10 == 0
    except: return False


def _tmp_file(content: bytes, suffix: str) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
        f.write(content)
        return f.name
