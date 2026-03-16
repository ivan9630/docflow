"""Service IA — Claude claude-opus-4-5 pour classification, fraude, enrichissement"""
import os, json, re
from typing import Optional
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
    prompt = f"""Tu es expert en fraude documentaire et conformité réglementaire française.

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
5. Date expiration attestation dépassée
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
        # Taux standards FR : 20%, 10%, 5.5%
        for t in [0.20, 0.10, 0.055]:
            if abs(round(ht*(1+t), 2) - ttc) <= 0.05:
                return True, f"TTC cohérent avec TVA {t*100:.1f}%"
        return False, f"TTC {ttc}€ incohérent avec HT {ht}€ (aucun taux TVA standard ne correspond)"
    return True, "Montants cohérents"
