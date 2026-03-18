"""Service IA — Claude claude-opus-4-5 pour classification, fraude, enrichissement"""
import os, json, re
from typing import Optional
from datetime import date
import anthropic
import structlog

logger = structlog.get_logger()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))

MODEL = "claude-opus-4-5"


def _parse_json(text: str) -> dict:
    text = text.strip()
    for pattern in [r'```json\s*(.*?)\s*```', r'```\s*(.*?)\s*```']:
        m = re.search(pattern, text, re.DOTALL)
        if m: text = m.group(1).strip()
    return json.loads(text)


async def classify_document(text: str) -> dict:
    prompt = f"""Tu es expert en documents administratifs français.

Analyse ce texte et détermine :
1. TYPE (exactement un parmi) : facture, devis, bon_commande, attestation_urssaf, attestation_fiscale, kbis, rib, contrat, autre
2. CONFIANCE (0.0 à 1.0)
3. INDICES ayant guidé ta décision

Texte (extrait) :
{text[:3000]}

Réponds UNIQUEMENT en JSON :
{{"type_document":"facture","confidence":0.95,"indices":["mention FACTURE en en-tête","numéros HT/TTC présents"]}}"""

    try:
        msg = client.messages.create(model=MODEL, max_tokens=300,
                                     messages=[{"role":"user","content":prompt}])
        return _parse_json(msg.content[0].text)
    except Exception as e:
        logger.error(f"Classification error: {e}")
        return {"type_document":"autre","confidence":0.0,"indices":[]}


async def detect_anomalies(doc_type: str, entities: dict,
                            supplier: Optional[dict] = None,
                            related: Optional[list] = None) -> dict:
    today = date.today().isoformat()
    prompt = f"""Tu es expert en fraude documentaire et conformité réglementaire française.

DATE DU JOUR : {today}

TYPE DOCUMENT : {doc_type}
DONNÉES EXTRAITES :
{json.dumps(entities, ensure_ascii=False, indent=2)}

DONNÉES FOURNISSEUR EN BASE :
{json.dumps(supplier or {}, ensure_ascii=False)}

AUTRES DOCUMENTS DU FOURNISSEUR :
{json.dumps(related or [], ensure_ascii=False)}

Vérifie :
1. SIRET commence par SIREN (14 chiffres = SIREN 9 + NIC 5)
2. TVA FR : clé = (12 + 3*(SIREN mod 97)) mod 97
3. TTC ≈ HT × (1 + taux_TVA)  [tolérance 0.02€]
4. IBAN différent du référentiel fournisseur
5. Date expiration attestation dépassée (comparer avec la date du jour : {today})
6. Numéro document dupliqué
7. Montants aberrants (négatifs, > 10M€ sans justification)

Réponds UNIQUEMENT en JSON :
{{"score_fraude":0.05,"est_frauduleux":false,"anomalies":[{{"type":"incoherence_siret_siren","description":"Le SIRET 12345678900099 ne commence pas par SIREN 987654321","severite":"critique","champ":"siret","valeur_trouvee":"12345678900099","valeur_attendue":"98765432100XXX"}}],"recommandations":[]}}"""

    try:
        msg = client.messages.create(model=MODEL, max_tokens=1000,
                                     messages=[{"role":"user","content":prompt}])
        return _parse_json(msg.content[0].text)
    except Exception as e:
        logger.error(f"Anomaly detection error: {e}")
        return {"score_fraude":0.0,"est_frauduleux":False,"anomalies":[],"recommandations":[]}


async def enrich_for_crm(doc_type: str, entities: dict, fraud: dict) -> dict:
    prompt = f"""Tu es assistant comptabilité / conformité.

Enrichis ces données brutes pour les applications métier (CRM, conformité) :

TYPE : {doc_type}
ENTITÉS : {json.dumps(entities, ensure_ascii=False, indent=2)}
ANALYSE FRAUDE : {json.dumps(fraud, ensure_ascii=False)}

Produis un JSON enrichi avec :
- Normalisation montants (2 décimales)
- Formatage SIREN/SIRET/TVA/IBAN
- Catégorie comptable suggérée (ex: "Charges externes - Prestations de services")
- Tags conformité
- Score complétude (0-100)
- Champs_manquants importants
- Statut_fournisseur suggéré (nouveau / connu / suspect / blacklist)
- Prêt_CRM (bool)
- Prêt_conformité (bool)

Réponds UNIQUEMENT en JSON valide."""

    try:
        msg = client.messages.create(model=MODEL, max_tokens=1500,
                                     messages=[{"role":"user","content":prompt}])
        return _parse_json(msg.content[0].text)
    except Exception as e:
        logger.error(f"Enrichment error: {e}")
        return entities


# ── Validation locale (sans API) ─────────────────────────────────

def validate_tva_local(siren: str, tva: str) -> tuple[bool, str]:
    try:
        s = re.sub(r'\D', '', siren or "")
        t = re.sub(r'\s', '', tva or "").upper()
        if len(s) != 9 or not t.startswith("FR") or len(t) != 13:
            return False, "Format invalide"
        key_expected = (12 + 3 * (int(s) % 97)) % 97
        key_actual   = int(t[2:4])
        siren_in_tva = t[4:]
        if key_actual != key_expected:
            return False, f"Clé TVA incorrecte (attendu {key_expected:02d}, trouvé {key_actual:02d})"
        if siren_in_tva != s:
            return False, f"SIREN dans TVA ({siren_in_tva}) ≠ SIREN ({s})"
        return True, "TVA cohérente"
    except Exception as e:
        return False, str(e)


def validate_siret_siren(siren: str, siret: str) -> tuple[bool, str]:
    try:
        s = re.sub(r'\D', '', siren or "")
        t = re.sub(r'\D', '', siret or "")
        if len(s) != 9: return False, f"SIREN invalide ({len(s)} chiffres)"
        if len(t) != 14: return False, f"SIRET invalide ({len(t)} chiffres)"
        if not t.startswith(s): return False, f"SIRET ne commence pas par SIREN {s}"
        return True, "SIRET/SIREN cohérents"
    except Exception as e:
        return False, str(e)


def validate_amounts(ht: float, tva_val: float, ttc: float, taux: float = None) -> tuple[bool, str]:
    if not all(x is not None for x in [ht, ttc]):
        return True, "Données insuffisantes pour vérifier"
    if taux:
        expected = round(ht * (1 + taux/100), 2)
        if abs(expected - ttc) > 0.05:
            return False, f"TTC attendu {expected}€ (HT {ht} × {1+taux/100:.2f}), trouvé {ttc}€"
    else:
        for t in [0.20, 0.10, 0.055]:
            if abs(round(ht*(1+t), 2) - ttc) <= 0.05:
                return True, f"TTC cohérent avec TVA {t*100:.1f}%"
        return False, f"TTC {ttc}€ incohérent avec HT {ht}€ (aucun taux TVA standard ne correspond)"
    return True, "Montants cohérents"


def validate_iban_local(iban: str) -> tuple[bool, str]:
    """Vérifie la validité d'un IBAN (format + clé mod 97)."""
    if not iban:
        return True, "Pas d'IBAN"
    iban_clean = re.sub(r'\s', '', iban).upper()
    if len(iban_clean) < 15 or len(iban_clean) > 34:
        return False, f"IBAN longueur invalide ({len(iban_clean)} caractères)"
    if not iban_clean[:2].isalpha():
        return False, "IBAN doit commencer par un code pays (2 lettres)"
    # Vérification mod 97
    rearranged = iban_clean[4:] + iban_clean[:4]
    numeric = ""
    for c in rearranged:
        if c.isdigit():
            numeric += c
        else:
            numeric += str(ord(c) - 55)
    try:
        if int(numeric) % 97 != 1:
            return False, f"IBAN clé de contrôle invalide"
    except ValueError:
        return False, "IBAN contient des caractères invalides"
    return True, "IBAN valide"


def validate_expiration(date_exp: str) -> tuple[bool, str]:
    """Vérifie si une date d'expiration est dépassée."""
    if not date_exp:
        return True, "Pas de date d'expiration"
    from datetime import datetime
    today = date.today()
    for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d.%m.%Y"]:
        try:
            exp = datetime.strptime(date_exp, fmt).date()
            if exp < today:
                return False, f"Document expiré le {date_exp} (aujourd'hui : {today.isoformat()})"
            return True, f"Valide jusqu'au {date_exp}"
        except ValueError:
            continue
    return True, "Format de date non reconnu"


def validate_montants_aberrants(ht: float, ttc: float) -> tuple[bool, str]:
    """Détecte les montants aberrants."""
    if ht is not None and ht < 0:
        return False, f"Montant HT négatif : {ht}€"
    if ttc is not None and ttc < 0:
        return False, f"Montant TTC négatif : {ttc}€"
    if ttc is not None and ttc > 10_000_000:
        return False, f"Montant TTC supérieur à 10M€ : {ttc}€"
    return True, "Montants dans les limites normales"


def detect_anomalies_local(doc_type: str, entities: dict,
                           supplier: dict = None, skip_amounts: bool = False) -> dict:
    """Détection d'anomalies 100% locale, sans appel API."""
    anomalies = []
    score = 0.0

    siren = entities.get("siren")
    siret = entities.get("siret")
    tva = entities.get("tva_number")
    ht = entities.get("montant_ht")
    tva_val = entities.get("montant_tva")
    ttc = entities.get("montant_ttc")
    taux = entities.get("taux_tva")
    iban = entities.get("iban")
    date_exp = entities.get("date_expiration")

    # 1. SIRET / SIREN
    if siren and siret:
        ok, msg = validate_siret_siren(siren, siret)
        if not ok:
            anomalies.append({"type": "incoherence_siret_siren", "description": msg,
                              "severite": "critique", "champ": "siret",
                              "valeur_trouvee": siret, "valeur_attendue": f"{siren}XXXXX"})
            score += 0.3

    # 2. TVA
    if siren and tva:
        ok, msg = validate_tva_local(siren, tva)
        if not ok:
            anomalies.append({"type": "incoherence_tva", "description": msg,
                              "severite": "elevee", "champ": "tva",
                              "valeur_trouvee": tva, "valeur_attendue": "Clé TVA cohérente avec SIREN"})
            score += 0.2

    # 3. Montants HT/TVA/TTC (skip si OCR de mauvaise qualité)
    if not skip_amounts and ht and ttc:
        ok, msg = validate_amounts(ht, tva_val, ttc, taux)
        if not ok:
            anomalies.append({"type": "montant_incoherent", "description": msg,
                              "severite": "elevee", "champ": "montants",
                              "valeur_trouvee": f"HT={ht} TTC={ttc}",
                              "valeur_attendue": "TTC = HT × (1 + TVA%)"})
            score += 0.25

    # 4. Montants aberrants
    if not skip_amounts and (ht is not None or ttc is not None):
        ok, msg = validate_montants_aberrants(ht, ttc)
        if not ok:
            anomalies.append({"type": "montant_aberrant", "description": msg,
                              "severite": "critique", "champ": "montants"})
            score += 0.3

    # 5. IBAN
    if iban:
        ok, msg = validate_iban_local(iban)
        if not ok:
            anomalies.append({"type": "iban_invalide", "description": msg,
                              "severite": "elevee", "champ": "iban",
                              "valeur_trouvee": iban})
            score += 0.15

    # 6. IBAN vs fournisseur en base
    if iban and supplier and supplier.get("iban"):
        sup_iban = re.sub(r'\s', '', supplier["iban"])
        doc_iban = re.sub(r'\s', '', iban)
        if sup_iban and doc_iban and sup_iban != doc_iban:
            anomalies.append({"type": "iban_different_fournisseur",
                              "description": "IBAN différent du référentiel fournisseur",
                              "severite": "elevee", "champ": "iban",
                              "valeur_trouvee": doc_iban[:12] + "...",
                              "valeur_attendue": sup_iban[:12] + "..."})
            score += 0.2

    # 7. Date expiration
    if date_exp:
        ok, msg = validate_expiration(date_exp)
        if not ok:
            anomalies.append({"type": "document_expire", "description": msg,
                              "severite": "critique", "champ": "date_expiration",
                              "valeur_trouvee": date_exp,
                              "valeur_attendue": f"Date >= {date.today().isoformat()}"})
            score += 0.3

    score = min(score, 1.0)
    return {
        "score_fraude": round(score, 2),
        "est_frauduleux": score > 0.5,
        "anomalies": anomalies,
        "recommandations": [],
        "method": "local",
    }


def enrich_local(doc_type: str, entities: dict, fraud: dict) -> dict:
    """Enrichissement local pour CRM/conformité, sans appel API."""
    siren = entities.get("siren") or ""
    siret = entities.get("siret") or ""
    tva = entities.get("tva_number") or ""
    iban = entities.get("iban") or ""

    # Score complétude
    fields = ["siren", "siret", "tva_number", "company_name", "iban",
              "montant_ht", "montant_ttc", "date", "doc_number"]
    present = sum(1 for f in fields if entities.get(f))
    completude = round(present / len(fields) * 100)

    missing = [f for f in fields if not entities.get(f)]

    # Formatage
    formatted_siren = f"{siren[:3]} {siren[3:6]} {siren[6:]}" if len(siren) == 9 else siren
    formatted_siret = f"{siret[:3]} {siret[3:6]} {siret[6:9]} {siret[9:]}" if len(siret) == 14 else siret

    # Catégorie comptable
    categories = {
        "facture": "Charges externes - Prestations de services",
        "devis": "Engagement hors bilan - Devis en attente",
        "bon_commande": "Charges externes - Commandes en cours",
        "contrat": "Charges externes - Contrats de prestation",
        "attestation_urssaf": "Conformité sociale",
        "attestation_fiscale": "Conformité fiscale",
        "attestation_siret": "Identité entreprise",
        "kbis": "Identité entreprise",
        "rib": "Données bancaires fournisseur",
        "avoir": "Produits - Avoirs reçus",
        "note_frais": "Charges de personnel - Frais professionnels",
    }

    # Statut fournisseur
    nb_anomalies = len(fraud.get("anomalies", []))
    if fraud.get("est_frauduleux"):
        statut = "blacklist"
    elif nb_anomalies > 0:
        statut = "suspect"
    elif entities.get("company_name"):
        statut = "connu"
    else:
        statut = "nouveau"

    # Tags conformité
    tags = []
    if doc_type in ("attestation_urssaf",):
        tags.append("conformite_sociale")
    if doc_type in ("attestation_fiscale",):
        tags.append("conformite_fiscale")
    if doc_type in ("kbis", "attestation_siret"):
        tags.append("identite_verificee")
    if nb_anomalies == 0:
        tags.append("aucune_anomalie")
    else:
        tags.append(f"{nb_anomalies}_anomalie(s)")

    return {
        "siren_formate": formatted_siren,
        "siret_formate": formatted_siret,
        "tva_formate": tva,
        "iban_formate": iban,
        "categorie_comptable": categories.get(doc_type, "Autre"),
        "tags_conformite": tags,
        "score_completude": completude,
        "champs_manquants": missing,
        "statut_fournisseur": statut,
        "pret_crm": completude >= 60 and statut not in ("blacklist",),
        "pret_conformite": nb_anomalies == 0,
        "method": "local",
    }
