#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DocuFlow v2 — Générateur de dataset synthétique administratif

Produit un dataset varié et annoté pour :
- OCR
- classification documentaire
- extraction d'entités
- détection de fraude

Documents générés :
- factures légitimes
- factures falsifiées (SIRET invalide, montants incohérents)
- devis
- attestations URSSAF valides
- attestations URSSAF expirées
- extraits KBIS
- RIB

Dégradations simulées :
- rotation 5° à 15°
- flou gaussien
- bruit
- faible résolution
- compression JPEG

Usage :
    pip install faker pillow numpy
    python generate_dataset.py --count 60 --output ./dataset --seed 42
"""

import os
import re
import json
import math
import random
import argparse
from pathlib import Path
from datetime import datetime, timedelta, date

import numpy as np
from faker import Faker
from PIL import Image, ImageFilter, ImageDraw, ImageFont, ImageEnhance

# Configuration globale

fake = Faker("fr_FR")

GROUP_MEMBERS = [
    "Jules Araud",
    "James MBA FONGANG",
    "Mathieu CHRETIEN",
    "Boubaker OMRI",
    "Romain PINTRE",
    "Ivan Noël",
    "Hajar MOUSSAOUI",
    "David CIRAKAZA",
]

FORMES_JURIDIQUES = ["SAS", "SARL", "SA", "EURL", "SASU", "SNC", "EI"]
CODES_NAF = ["6201Z", "4771Z", "4711D", "4120A", "7112B", "6312Z", "6202A"]
TAUX_TVA = [20.0, 10.0, 5.5]
BANQUES = [
    "BNP Paribas",
    "Société Générale",
    "Crédit Agricole",
    "Crédit Mutuel",
    "La Banque Postale",
    "Caisse d'Épargne",
]
GREFFES = [
    "Paris",
    "Lyon",
    "Marseille",
    "Toulouse",
    "Lille",
    "Bordeaux",
    "Nantes",
]
URSSAF_REGIONS = [
    "Île-de-France",
    "Auvergne-Rhône-Alpes",
    "Provence-Alpes-Côte d'Azur",
    "Occitanie",
    "Hauts-de-France",
]

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/Library/Fonts/Courier New.ttf",
    "C:/Windows/Fonts/consola.ttf",
    "C:/Windows/Fonts/arial.ttf",
]

DEFAULT_SCENARIO_DISTRIBUTION = {
    "facture_legitime": 15,
    "facture_fake_siret": 5,
    "facture_fake_amounts": 5,
    "devis": 10,
    "attestation_urssaf_valide": 8,
    "attestation_urssaf_expiree": 5,
    "kbis": 6,
    "rib": 6,
}

# Utilitaires divers

def set_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    fake.seed_instance(seed)


def pick_member(exclude=None):
    pool = [m for m in GROUP_MEMBERS if m != exclude]
    return random.choice(pool)


def euro(v: float) -> str:
    s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", " ")
    return f"{s} €"


def format_date_fr(d: date) -> str:
    return d.strftime("%d/%m/%Y")


def sanitize_filename(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^\w\-\.]+", "_", s, flags=re.UNICODE)
    s = re.sub(r"_+", "_", s)
    return s


def load_font(size=16):
    for path in FONT_CANDIDATES:
        try:
            if os.path.exists(path):
                return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


# Luhn / SIREN / SIRET / TVA / IBAN

def luhn_checksum(number: str) -> int:
    digits = [int(d) for d in number]
    checksum = 0
    parity = len(digits) % 2
    for i, digit in enumerate(digits):
        if i % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
    return checksum % 10


def luhn_valid(number: str) -> bool:
    return luhn_checksum(number) == 0


def complete_luhn(base_without_checkdigit: str) -> str:
    for d in range(10):
        candidate = base_without_checkdigit + str(d)
        if luhn_valid(candidate):
            return candidate
    raise RuntimeError("Impossible de calculer le check digit Luhn")


def gen_siren() -> str:
    base = "".join(str(random.randint(0, 9)) for _ in range(8))
    return complete_luhn(base)


def gen_siret(siren: str) -> str:
    nic_base = "".join(str(random.randint(0, 9)) for _ in range(4))
    first_13 = siren + nic_base
    return complete_luhn(first_13)


def gen_invalid_siret(valid_siren: str = None) -> str:
    if valid_siren is None:
        valid_siren = gen_siren()
    siret = gen_siret(valid_siren)
    idx = random.randint(0, 13)
    original = siret[idx]
    candidates = [str(i) for i in range(10) if str(i) != original]
    tampered = siret[:idx] + random.choice(candidates) + siret[idx + 1 :]
    if tampered[:9] == valid_siren and luhn_valid(tampered):
        # force l'invalidité
        last = tampered[-1]
        tampered = tampered[:-1] + str((int(last) + 1) % 10)
    return tampered


def gen_tva_fr(siren: str) -> str:
    key = (12 + 3 * (int(siren) % 97)) % 97
    return f"FR{key:02d}{siren}"


def iban_to_numeric(iban: str) -> str:
    rearranged = iban[4:] + iban[:4]
    out = []
    for c in rearranged:
        if c.isdigit():
            out.append(c)
        else:
            out.append(str(ord(c.upper()) - 55))
    return "".join(out)


def iban_valid(iban: str) -> bool:
    iban = iban.replace(" ", "").upper()
    if len(iban) < 15 or len(iban) > 34:
        return False
    numeric = iban_to_numeric(iban)
    return int(numeric) % 97 == 1


def compute_iban_check_digits(country_code: str, bban: str) -> str:
    temp = bban + country_code + "00"
    numeric = ""
    for c in temp:
        if c.isdigit():
            numeric += c
        else:
            numeric += str(ord(c.upper()) - 55)
    check = 98 - (int(numeric) % 97)
    return f"{check:02d}"


def gen_iban_fr() -> str:
    # Format simplifié FR : banque(5) + guichet(5) + compte(11 alnum) + clé(2)
    banque = "".join(str(random.randint(0, 9)) for _ in range(5))
    guichet = "".join(str(random.randint(0, 9)) for _ in range(5))
    compte = "".join(str(random.randint(0, 9)) for _ in range(11))
    cle_rib = "".join(str(random.randint(0, 9)) for _ in range(2))
    bban = banque + guichet + compte + cle_rib
    check = compute_iban_check_digits("FR", bban)
    return f"FR{check}{bban}"


def pretty_iban(iban: str) -> str:
    iban = iban.replace(" ", "")
    return " ".join(iban[i:i+4] for i in range(0, len(iban), 4))


def gen_bic() -> str:
    bank = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=4))
    country = "FR"
    location = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=2))
    branch = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=3))
    return bank + country + location + branch


# Génération entreprises / personnes / clients

def gen_company():
    siren = gen_siren()
    siret = gen_siret(siren)
    legal_form = random.choice(FORMES_JURIDIQUES)
    company_name = fake.company()
    if legal_form not in company_name.upper():
        company_name = f"{company_name} {legal_form}"

    manager = pick_member()
    iban = gen_iban_fr()
    return {
        "nom": company_name,
        "forme_juridique": legal_form,
        "siren": siren,
        "siret": siret,
        "tva": gen_tva_fr(siren),
        "iban": pretty_iban(iban),
        "iban_raw": iban,
        "bic": gen_bic(),
        "adresse": fake.street_address(),
        "cp": fake.postcode(),
        "ville": fake.city(),
        "email": fake.company_email(),
        "telephone": fake.phone_number(),
        "capital_social": round(random.uniform(1000, 200000), 2),
        "code_naf": random.choice(CODES_NAF),
        "greffe": random.choice(GREFFES),
        "representant_legal": manager,
        "date_creation": fake.date_between(start_date="-12y", end_date="-6m"),
        "effectif": random.randint(1, 300),
    }


def gen_client():
    return {
        "nom": fake.company() + " " + random.choice(FORMES_JURIDIQUES),
        "adresse": fake.street_address(),
        "cp": fake.postcode(),
        "ville": fake.city(),
        "contact": pick_member(),
    }


def gen_invoice_lines():
    catalogue = [
        ("Prestation de développement logiciel", (800, 6000)),
        ("Maintenance applicative", (300, 2500)),
        ("Audit de conformité documentaire", (700, 4500)),
        ("Intégration API et connecteurs", (900, 5000)),
        ("Licence SaaS mensuelle", (120, 900)),
        ("Formation équipe métier", (400, 2200)),
        ("Assistance technique", (250, 1800)),
        ("Paramétrage OCR & NER", (600, 3800)),
    ]
    nb = random.randint(1, 4)
    chosen = random.sample(catalogue, nb)
    lines = []
    total = 0.0
    for label, (mn, mx) in chosen:
        qty = random.randint(1, 5)
        unit = round(random.uniform(mn, mx), 2)
        line_total = round(qty * unit, 2)
        total += line_total
        lines.append({
            "label": label,
            "qty": qty,
            "unit_price": unit,
            "line_total": line_total,
        })
    return lines, round(total, 2)


# Génération de documents métier

def make_facture_legitime(doc_id: str):
    supplier = gen_company()
    client = gen_client()
    signer = pick_member()
    account_manager = pick_member(exclude=signer)

    issue_date = fake.date_between(start_date="-240d", end_date="today")  
    due_date = issue_date + timedelta(days=random.choice([15, 30, 45]))
    invoice_number = f"FAC-{issue_date.year}-{random.randint(1000, 9999)}"

    lines, ht = gen_invoice_lines()
    vat_rate = random.choice(TAUX_TVA)
    tva = round(ht * vat_rate / 100, 2)
    ttc = round(ht + tva, 2)

    detail_lines = []
    for line in lines:
        detail_lines.append(
            f"  - {line['label']} x{line['qty']} @ {euro(line['unit_price'])} = {euro(line['line_total'])}"
        )

    text = f"""
                                    FACTURE

Émetteur :
  {supplier['nom']}
  {supplier['adresse']}, {supplier['cp']} {supplier['ville']}
  SIREN : {supplier['siren']}
  SIRET : {supplier['siret']}
  N° TVA intracommunautaire : {supplier['tva']}
  IBAN : {supplier['iban']}
  BIC  : {supplier['bic']}
  Responsable dossier : {account_manager}

Destinataire :
  {client['nom']}
  {client['adresse']}, {client['cp']} {client['ville']}
  Contact : {client['contact']}

Numéro de facture : {invoice_number}
Date d'émission   : {format_date_fr(issue_date)}
Date d'échéance   : {format_date_fr(due_date)}

Détail des prestations :
{chr(10).join(detail_lines)}

Montant total H.T.        : {euro(ht)}
TVA {vat_rate:.1f}%               : {euro(tva)}
Montant total T.T.C.      : {euro(ttc)}

Conditions de règlement : virement bancaire à 30 jours fin de mois
Établi par : {signer}
""".strip("\n")

    label = {
        "doc_id": doc_id,
        "doc_type": "facture",
        "variant": "legitime",
        "expected_class": "facture",
        "expected_fraud": False,
        "fraud_reasons": [],
        "supplier_name": supplier["nom"],
        "supplier_siren": supplier["siren"],
        "supplier_siret": supplier["siret"],
        "supplier_tva": supplier["tva"],
        "iban": supplier["iban_raw"],
        "bic": supplier["bic"],
        "invoice_number": invoice_number,
        "issue_date": issue_date.isoformat(),
        "due_date": due_date.isoformat(),
        "amount_ht": ht,
        "vat_rate": vat_rate,
        "amount_tva": tva,
        "amount_ttc": ttc,
        "group_member_names_used": [signer, account_manager, client["contact"]],
    }
    return text, label


def make_facture_fake_siret(doc_id: str):
    supplier = gen_company()
    client = gen_client()
    signer = pick_member()

    issue_date = fake.date_between(start_date="-240d", end_date="today")
    due_date = issue_date + timedelta(days=30)
    invoice_number = f"FAC-{issue_date.year}-{random.randint(1000, 9999)}"

    lines, ht = gen_invoice_lines()
    vat_rate = random.choice(TAUX_TVA)
    tva = round(ht * vat_rate / 100, 2)
    ttc = round(ht + tva, 2)

    real_siret = supplier["siret"]
    fake_siret = gen_invalid_siret(supplier["siren"])

    detail_lines = []
    for line in lines:
        detail_lines.append(
            f"  - {line['label']} x{line['qty']} @ {euro(line['unit_price'])} = {euro(line['line_total'])}"
        )

    text = f"""
                                    FACTURE

Émetteur :
  {supplier['nom']}
  {supplier['adresse']}, {supplier['cp']} {supplier['ville']}
  SIREN : {supplier['siren']}
  SIRET : {fake_siret}
  N° TVA intracommunautaire : {supplier['tva']}
  IBAN : {supplier['iban']}
  BIC  : {supplier['bic']}

Destinataire :
  {client['nom']}
  {client['adresse']}, {client['cp']} {client['ville']}

Numéro de facture : {invoice_number}
Date d'émission   : {format_date_fr(issue_date)}
Date d'échéance   : {format_date_fr(due_date)}

Détail des prestations :
{chr(10).join(detail_lines)}

Montant total H.T.        : {euro(ht)}
TVA {vat_rate:.1f}%               : {euro(tva)}
Montant total T.T.C.      : {euro(ttc)}

Établi par : {signer}
""".strip("\n")

    label = {
        "doc_id": doc_id,
        "doc_type": "facture",
        "variant": "fake_siret",
        "expected_class": "facture",
        "expected_fraud": True,
        "fraud_reasons": ["siret_invalide"],
        "supplier_name": supplier["nom"],
        "supplier_siren": supplier["siren"],
        "supplier_siret_real": real_siret,
        "supplier_siret_displayed": fake_siret,
        "invoice_number": invoice_number,
        "issue_date": issue_date.isoformat(),
        "amount_ht": ht,
        "vat_rate": vat_rate,
        "amount_tva": tva,
        "amount_ttc": ttc,
        "group_member_names_used": [signer],
    }
    return text, label


def make_facture_fake_amounts(doc_id: str):
    supplier = gen_company()
    client = gen_client()
    signer = pick_member()

    issue_date = fake.date_between(start_date="-240d", end_date="today")
    due_date = issue_date + timedelta(days=30)
    invoice_number = f"FAC-{issue_date.year}-{random.randint(1000, 9999)}"

    lines, real_ht = gen_invoice_lines()
    vat_rate = random.choice(TAUX_TVA)
    real_tva = round(real_ht * vat_rate / 100, 2)
    real_ttc = round(real_ht + real_tva, 2)

    anomaly_type = random.choice(["wrong_ttc", "wrong_tva", "wrong_ht"])
    shown_ht = real_ht
    shown_tva = real_tva
    shown_ttc = real_ttc

    if anomaly_type == "wrong_ttc":
        delta = round(random.uniform(15, 250), 2)
        shown_ttc = round(real_ttc + delta, 2)
    elif anomaly_type == "wrong_tva":
        shown_tva = round(real_tva + random.uniform(10, 180), 2)
        shown_ttc = round(shown_ht + shown_tva, 2)
    elif anomaly_type == "wrong_ht":
        shown_ht = round(real_ht + random.uniform(20, 300), 2)
        shown_tva = real_tva
        shown_ttc = round(real_ttc, 2)

    detail_lines = []
    for line in lines:
        detail_lines.append(
            f"  - {line['label']} x{line['qty']} @ {euro(line['unit_price'])} = {euro(line['line_total'])}"
        )

    text = f"""
                                    FACTURE

Émetteur :
  {supplier['nom']}
  {supplier['adresse']}, {supplier['cp']} {supplier['ville']}
  SIREN : {supplier['siren']}
  SIRET : {supplier['siret']}
  N° TVA intracommunautaire : {supplier['tva']}

Destinataire :
  {client['nom']}
  {client['adresse']}, {client['cp']} {client['ville']}

Numéro de facture : {invoice_number}
Date d'émission   : {format_date_fr(issue_date)}
Date d'échéance   : {format_date_fr(due_date)}

Détail des prestations :
{chr(10).join(detail_lines)}

Montant total H.T.        : {euro(shown_ht)}
TVA {vat_rate:.1f}%               : {euro(shown_tva)}
Montant total T.T.C.      : {euro(shown_ttc)}

Règlement : virement bancaire
Établi par : {signer}
""".strip("\n")

    label = {
        "doc_id": doc_id,
        "doc_type": "facture",
        "variant": "fake_amounts",
        "expected_class": "facture",
        "expected_fraud": True,
        "fraud_reasons": ["montants_incoherents_ht_tva_ttc"],
        "supplier_name": supplier["nom"],
        "supplier_siren": supplier["siren"],
        "supplier_siret": supplier["siret"],
        "invoice_number": invoice_number,
        "issue_date": issue_date.isoformat(),
        "vat_rate": vat_rate,
        "real_amount_ht": real_ht,
        "real_amount_tva": real_tva,
        "real_amount_ttc": real_ttc,
        "shown_amount_ht": shown_ht,
        "shown_amount_tva": shown_tva,
        "shown_amount_ttc": shown_ttc,
        "anomaly_subtype": anomaly_type,
        "group_member_names_used": [signer],
    }
    return text, label


def make_devis(doc_id: str):
    supplier = gen_company()
    client = gen_client()
    consultant = pick_member()
    commercial = pick_member(exclude=consultant)

    issue_date = fake.date_between(start_date="-180d", end_date="today")
    valid_until = issue_date + timedelta(days=random.choice([15, 30, 45, 60]))
    quote_number = f"DEV-{issue_date.year}-{random.randint(1000, 9999)}"

    lines, ht = gen_invoice_lines()
    vat_rate = random.choice(TAUX_TVA)
    tva = round(ht * vat_rate / 100, 2)
    ttc = round(ht + tva, 2)

    detail_lines = []
    for line in lines:
        detail_lines.append(
            f"  - {line['label']} x{line['qty']} @ {euro(line['unit_price'])} = {euro(line['line_total'])}"
        )

    text = f"""
                                      DEVIS

Prestataire :
  {supplier['nom']}
  {supplier['adresse']}, {supplier['cp']} {supplier['ville']}
  SIREN : {supplier['siren']}
  SIRET : {supplier['siret']}
  N° TVA : {supplier['tva']}
  Conseiller commercial : {commercial}

Client :
  {client['nom']}
  {client['adresse']}, {client['cp']} {client['ville']}
  Contact projet : {client['contact']}

Numéro devis    : {quote_number}
Date d'émission : {format_date_fr(issue_date)}
Valable jusqu'au: {format_date_fr(valid_until)}

Prestations proposées :
{chr(10).join(detail_lines)}

Total H.T.      : {euro(ht)}
TVA {vat_rate:.1f}%       : {euro(tva)}
Total T.T.C.    : {euro(ttc)}

Bon pour accord :
Nom du consultant : {consultant}
Signature client : _______________________
""".strip("\n")

    label = {
        "doc_id": doc_id,
        "doc_type": "devis",
        "variant": "standard",
        "expected_class": "devis",
        "expected_fraud": False,
        "fraud_reasons": [],
        "quote_number": quote_number,
        "issue_date": issue_date.isoformat(),
        "valid_until": valid_until.isoformat(),
        "supplier_name": supplier["nom"],
        "supplier_siren": supplier["siren"],
        "supplier_siret": supplier["siret"],
        "amount_ht": ht,
        "vat_rate": vat_rate,
        "amount_tva": tva,
        "amount_ttc": ttc,
        "group_member_names_used": [consultant, commercial, client["contact"]],
    }
    return text, label


def make_attestation_urssaf(doc_id: str, expired=False):
    company = gen_company()
    signatory = pick_member()
    region = random.choice(URSSAF_REGIONS)

    issue_date = fake.date_between(start_date="-300d", end_date="today")
    if expired:
        valid_until = fake.date_between(start_date="-365d", end_date="-3d")
    else:
        valid_until = issue_date + timedelta(days=random.randint(90, 180))

    att_number = f"ATT-{random.randint(100000, 999999)}"

    text = f"""
                           ATTESTATION DE VIGILANCE
                               URSSAF {region}

Nous attestons que l'entreprise ci-dessous est à jour de ses obligations
déclaratives et de paiement au regard de la législation sociale.

Raison sociale  : {company['nom']}
SIREN           : {company['siren']}
SIRET           : {company['siret']}
Adresse         : {company['adresse']}, {company['cp']} {company['ville']}
Représentant    : {company['representant_legal']}

Date d'édition  : {format_date_fr(issue_date)}
Valable jusqu'au: {format_date_fr(valid_until)}
N° attestation  : {att_number}

Document édité par : {signatory}
Site de référence : www.urssaf.fr
""".strip("\n")

    label = {
        "doc_id": doc_id,
        "doc_type": "attestation_urssaf",
        "variant": "expiree" if expired else "valide",
        "expected_class": "attestation_urssaf",
        "expected_fraud": bool(expired),
        "fraud_reasons": ["attestation_expiree"] if expired else [],
        "attestation_number": att_number,
        "issue_date": issue_date.isoformat(),
        "valid_until": valid_until.isoformat(),
        "expired": expired,
        "supplier_name": company["nom"],
        "supplier_siren": company["siren"],
        "supplier_siret": company["siret"],
        "group_member_names_used": [signatory, company["representant_legal"]],
    }
    return text, label


def make_kbis(doc_id: str):
    company = gen_company()
    signatory = pick_member()
    issue_date = fake.date_between(start_date="-30d", end_date="today")
    capital = round(random.uniform(1000, 500000), 2)

    text = f"""
                                   EXTRAIT KBIS

Registre du Commerce et des Sociétés de {company['greffe']}

Dénomination sociale : {company['nom']}
Forme juridique      : {company['forme_juridique']}
Capital social       : {euro(capital)}
SIREN                : {company['siren']}
SIRET                : {company['siret']}
Code APE / NAF       : {company['code_naf']}
N° TVA intracom      : {company['tva']}

Siège social :
  {company['adresse']}
  {company['cp']} {company['ville']}

Date de création     : {format_date_fr(company['date_creation'])}
Représentant légal   : {company['representant_legal']}
Effectif             : {company['effectif']} salariés

Extrait délivré le   : {format_date_fr(issue_date)}
Agent ayant traité le dossier : {signatory}
""".strip("\n")

    label = {
        "doc_id": doc_id,
        "doc_type": "kbis",
        "variant": "standard",
        "expected_class": "kbis",
        "expected_fraud": False,
        "fraud_reasons": [],
        "supplier_name": company["nom"],
        "supplier_siren": company["siren"],
        "supplier_siret": company["siret"],
        "supplier_tva": company["tva"],
        "code_naf": company["code_naf"],
        "issue_date": issue_date.isoformat(),
        "date_creation": company["date_creation"].isoformat(),
        "group_member_names_used": [signatory, company["representant_legal"]],
    }
    return text, label


def make_rib(doc_id: str):
    company = gen_company()
    bank = random.choice(BANQUES)
    account_holder = pick_member()
    processing_agent = pick_member(exclude=account_holder)

    text = f"""
                     RELEVÉ D'IDENTITÉ BANCAIRE / IBAN

Titulaire du compte : {company['nom']}
Interlocuteur       : {account_holder}
Adresse             : {company['adresse']}, {company['cp']} {company['ville']}
SIREN               : {company['siren']}

Banque              : {bank}
IBAN                : {company['iban']}
BIC                 : {company['bic']}
Domiciliation       : Agence {company['ville']}
Référence dossier   : RIB-{random.randint(100000, 999999)}

Conseiller bancaire : {processing_agent}
""".strip("\n")

    label = {
        "doc_id": doc_id,
        "doc_type": "rib",
        "variant": "standard",
        "expected_class": "rib",
        "expected_fraud": False,
        "fraud_reasons": [],
        "supplier_name": company["nom"],
        "supplier_siren": company["siren"],
        "iban": company["iban_raw"],
        "bic": company["bic"],
        "bank_name": bank,
        "group_member_names_used": [account_holder, processing_agent],
    }
    return text, label


# Rendu image

def add_fake_stamp(draw, x, y, text="VALIDÉ"):
    draw.rectangle([x, y, x + 150, y + 38], outline="gray", width=2)
    font = load_font(20)
    draw.text((x + 12, y + 8), text, fill="gray", font=font)


def text_to_image(text: str, doc_type: str = "document"):
    W, H = 1654, 2339  
    img = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(img)

    title_font = load_font(30)
    body_font = load_font(20)
    small_font = load_font(16)

    # marge
    x0 = 90
    y = 80

    # en-tête visuel 
    draw.rectangle([70, 60, W - 70, H - 60], outline=(220, 220, 220), width=3)
    draw.line([90, 140, W - 90, 140], fill=(180, 180, 180), width=2)

    lines = text.splitlines()
    first_non_empty = ""
    for line in lines:
        if line.strip():
            first_non_empty = line.strip()
            break

    draw.text((x0, 90), first_non_empty[:80], fill="black", font=title_font)

    y = 170
    for line in lines[1:]:
        font = body_font if line.strip() and line.strip().endswith(":") else body_font
        draw.text((x0, y), line, fill="black", font=font)
        y += 29
        if y > H - 120:
            break

    footer = f"DocuFlow Dataset • {doc_type} • Généré automatiquement"
    draw.text((x0, H - 95), footer, fill=(80, 80, 80), font=small_font)

    # éléments visuels
    if doc_type in {"facture", "devis"} and random.random() < 0.7:
        add_fake_stamp(draw, W - 300, 180, random.choice(["PAYÉ", "VALIDÉ", "ARCHIVE"]))
    if doc_type == "attestation_urssaf" and random.random() < 0.8:
        add_fake_stamp(draw, W - 340, 190, "URSSAF")
    if doc_type == "rib" and random.random() < 0.6:
        add_fake_stamp(draw, W - 330, 190, "BANQUE")

    return img


# Dégradations

def add_gaussian_noise(img: Image.Image, std: float):
    arr = np.array(img).astype(np.int16)
    noise = np.random.normal(0, std, arr.shape).astype(np.int16)
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def add_salt_pepper_noise(img: Image.Image, amount=0.003):
    arr = np.array(img)
    out = arr.copy()
    num = int(amount * arr.shape[0] * arr.shape[1])

    coords = (
        np.random.randint(0, arr.shape[0], num),
        np.random.randint(0, arr.shape[1], num)
    )
    out[coords] = 255

    coords = (
        np.random.randint(0, arr.shape[0], num),
        np.random.randint(0, arr.shape[1], num)
    )
    out[coords] = 0
    return Image.fromarray(out)


def degrade_image(img: Image.Image, level: str):
    """
    level:
      - clean
      - medium
      - hard
    """
    applied = []

    if level == "clean":
        return img, applied

    # légère variation luminosité / contraste
    if random.random() < 0.8:
        brightness = ImageEnhance.Brightness(img)
        factor = random.uniform(0.9, 1.1) if level == "medium" else random.uniform(0.8, 1.2)
        img = brightness.enhance(factor)
        applied.append(f"brightness_{factor:.2f}")

    if random.random() < 0.8:
        contrast = ImageEnhance.Contrast(img)
        factor = random.uniform(0.9, 1.08) if level == "medium" else random.uniform(0.82, 1.15)
        img = contrast.enhance(factor)
        applied.append(f"contrast_{factor:.2f}")

    # rotation 5-15°
    angle_abs = random.uniform(5, 15)
    angle = angle_abs if random.random() < 0.5 else -angle_abs
    img = img.rotate(angle, fillcolor="white", resample=Image.Resampling.BICUBIC)
    applied.append(f"rotation_{angle:.1f}")

    # flou
    blur_radius = random.uniform(0.6, 1.4) if level == "medium" else random.uniform(1.4, 2.8)
    img = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    applied.append(f"gaussian_blur_{blur_radius:.2f}")

    # bruit
    if random.random() < 0.9:
        std = random.uniform(5, 14) if level == "medium" else random.uniform(14, 28)
        img = add_gaussian_noise(img, std)
        applied.append(f"gaussian_noise_{std:.1f}")

    if random.random() < 0.5:
        amount = random.uniform(0.001, 0.003) if level == "medium" else random.uniform(0.003, 0.006)
        img = add_salt_pepper_noise(img, amount=amount)
        applied.append(f"salt_pepper_{amount:.4f}")

    # basse résolution
    w, h = img.size
    if level == "medium":
        factor = random.uniform(0.65, 0.82)
    else:
        factor = random.uniform(0.35, 0.60)

    w2 = max(500, int(w * factor))
    h2 = max(700, int(h * factor))
    img = img.resize((w2, h2), Image.Resampling.BILINEAR).resize((w, h), Image.Resampling.BILINEAR)
    applied.append(f"low_resolution_{factor:.2f}")

    return img, applied


# Planification des scénarios

def build_plan(total_count: int):
    """
    Construit une liste de scénarios à partir de la distribution par défaut.
    Si total_count diffère du total nominal, on ajuste proportionnellement.
    """
    base_total = sum(DEFAULT_SCENARIO_DISTRIBUTION.values())
    if total_count <= 0:
        raise ValueError("Le nombre de documents doit être > 0")

    if total_count == base_total:
        plan = []
        for scenario, count in DEFAULT_SCENARIO_DISTRIBUTION.items():
            plan.extend([scenario] * count)
        random.shuffle(plan)
        return plan

    items = list(DEFAULT_SCENARIO_DISTRIBUTION.items())
    raw_counts = []
    for scenario, count in items:
        scaled = (count / base_total) * total_count
        raw_counts.append((scenario, scaled))

    floor_counts = {scenario: int(math.floor(v)) for scenario, v in raw_counts}
    current = sum(floor_counts.values())
    remaining = total_count - current

    remainders = sorted(
        ((scenario, scaled - floor_counts[scenario]) for scenario, scaled in raw_counts),
        key=lambda x: x[1],
        reverse=True,
    )

    for i in range(remaining):
        floor_counts[remainders[i % len(remainders)][0]] += 1

    plan = []
    for scenario, count in floor_counts.items():
        plan.extend([scenario] * count)

    random.shuffle(plan)
    return plan


def scenario_to_generator(scenario_name: str):
    mapping = {
        "facture_legitime": make_facture_legitime,
        "facture_fake_siret": make_facture_fake_siret,
        "facture_fake_amounts": make_facture_fake_amounts,
        "devis": make_devis,
        "attestation_urssaf_valide": lambda doc_id: make_attestation_urssaf(doc_id, expired=False),
        "attestation_urssaf_expiree": lambda doc_id: make_attestation_urssaf(doc_id, expired=True),
        "kbis": make_kbis,
        "rib": make_rib,
    }
    return mapping[scenario_name]


def pick_degradation_level():
    # 30% clean, 40% medium, 30% hard
    r = random.random()
    if r < 0.30:
        return "clean"
    if r < 0.70:
        return "medium"
    return "hard"


# -------------------------------------------------------------------
# README auto-généré
# -------------------------------------------------------------------

def build_dataset_readme(output_dir: Path, manifest: list):
    type_counts = {}
    fraud_count = 0
    scenario_counts = {}
    degradation_counts = {"clean": 0, "medium": 0, "hard": 0}

    for item in manifest:
        type_counts[item["doc_type"]] = type_counts.get(item["doc_type"], 0) + 1
        scenario_counts[item["variant"]] = scenario_counts.get(item["variant"], 0) + 1
        if item.get("expected_fraud"):
            fraud_count += 1
        degradation_counts[item["degradation_level"]] = degradation_counts.get(item["degradation_level"], 0) + 1

    total = len(manifest)
    group_str = ", ".join(GROUP_MEMBERS)

    content = f"""# Dataset DocuFlow v2

## Résumé
Ce dataset contient **{total} documents synthétiques** générés pour tester la pipeline DocuFlow v2 :
- OCR
- classification documentaire
- extraction d'entités
- vérifications de cohérence
- détection de fraude

## Répartition par type
""" + "\n".join([f"- **{k}** : {v}" for k, v in sorted(type_counts.items())]) + f"""

## Répartition par scénario
""" + "\n".join([f"- **{k}** : {v}" for k, v in sorted(scenario_counts.items())]) + f"""

## Documents suspects / frauduleux attendus
- **Nombre total attendu** : {fraud_count}

### Scénarios de fraude inclus
- factures avec **SIRET invalide**
- factures avec **montants HT / TVA / TTC incohérents**
- attestations URSSAF **expirées**

## Dégradations simulées
Les documents ont été dégradés pour simuler des scans ou photos smartphone :
- rotation aléatoire entre **5° et 15°**
- flou gaussien
- bruit gaussien
- bruit sel / poivre
- faible résolution
- variations légères de contraste / luminosité
- compression JPEG pour certains fichiers

### Répartition des niveaux
- **clean** : {degradation_counts.get("clean", 0)}
- **medium** : {degradation_counts.get("medium", 0)}
- **hard** : {degradation_counts.get("hard", 0)}

## Structure du dossier
- `images/` : documents rendus en PNG / JPG
- `texts/` : texte source utilisé pour fabriquer le document
- `labels/` : annotations JSON document par document
- `metadata/manifest.json` : index complet du dataset
- `README.md` : documentation du dataset

## Format des labels
Chaque fichier `labels/DOC-XXXX.json` contient notamment :
- `doc_id`
- `doc_type`
- `variant`
- `expected_class`
- `expected_fraud`
- `fraud_reasons`
- les champs métier attendus (SIREN, SIRET, montants, dates, IBAN, etc.)
- `degradation_level`
- `degradations_applied`
- `group_member_names_used`

## Personnalisation avec les noms du groupe
Les noms suivants ont été injectés dans certains champs :
- signataires
- responsables dossier
- conseillers commerciaux
- représentants légaux
- interlocuteurs / titulaires de compte

**Noms utilisés** :
{group_str}

## Notes
- Les documents sont **synthétiques** et destinés au test / démonstration.
- Les données sont plausibles mais ne correspondent pas à des pièces officielles réelles.
- Les annotations servent de **ground truth** pour évaluer les résultats OCR et IA.
"""
    (output_dir / "README.md").write_text(content, encoding="utf-8")


# Génération globale

def generate_dataset(count: int, output_dir: str, seed: int = 42):
    set_seed(seed)

    out = Path(output_dir)
    images_dir = out / "images"
    texts_dir = out / "texts"
    labels_dir = out / "labels"
    meta_dir = out / "metadata"

    for d in [out, images_dir, texts_dir, labels_dir, meta_dir]:
        d.mkdir(parents=True, exist_ok=True)

    plan = build_plan(count)
    manifest = []

    print(f"\n🔧 Génération de {count} documents dans : {out.resolve()}\n")

    for idx, scenario in enumerate(plan, start=1):
        doc_id = f"DOC-{idx:04d}"
        generator = scenario_to_generator(scenario)
        text, label = generator(doc_id)

        doc_type = label["doc_type"]
        degradation_level = pick_degradation_level()

        # rendu
        img = text_to_image(text, doc_type=doc_type)
        img, degradations_applied = degrade_image(img, degradation_level)

        # extension 
        base_name = sanitize_filename(f"{doc_id}_{doc_type}_{label['variant']}")
        if degradation_level == "hard" and random.random() < 0.8:
            ext = ".jpg"
        else:
            ext = ".png"

        image_filename = base_name + ext
        text_filename = base_name + ".txt"
        label_filename = f"{doc_id}.json"

        image_path = images_dir / image_filename
        text_path = texts_dir / text_filename
        label_path = labels_dir / label_filename

        # sauvegarde image
        if ext == ".jpg":
            img.save(image_path, format="JPEG", quality=random.randint(38, 68), optimize=True)
        else:
            img.save(image_path, format="PNG")

        # sauvegarde texte
        text_path.write_text(text, encoding="utf-8")

        # enrichir label
        label.update({
            "filename": image_filename,
            "text_source_file": text_filename,
            "label_file": label_filename,
            "degradation_level": degradation_level,
            "degradations_applied": degradations_applied,
            "scenario_name": scenario,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
        })

        label_path.write_text(json.dumps(label, ensure_ascii=False, indent=2), encoding="utf-8")
        manifest.append(label)

        fraud_icon = "⚠️" if label["expected_fraud"] else "✅"
        print(
            f"[{idx:03d}/{count}] "
            f"{doc_id} | {doc_type:20s} | {label['variant']:15s} | "
            f"{degradation_level:6s} | {fraud_icon}"
        )

    # manifest global
    (meta_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    # README
    build_dataset_readme(out, manifest)

    # stats console
    by_type = {}
    by_variant = {}
    fraud_count = 0
    for item in manifest:
        by_type[item["doc_type"]] = by_type.get(item["doc_type"], 0) + 1
        by_variant[item["variant"]] = by_variant.get(item["variant"], 0) + 1
        if item["expected_fraud"]:
            fraud_count += 1

    print("\n" + "─" * 70)
    print(f" Dataset généré : {count} documents")
    print(f" Dossier        : {out.resolve()}")
    print(f"  Frauduleux     : {fraud_count}")
    print(f" Par type       : {by_type}")
    print(f" Par scénario   : {by_variant}")
    print("─" * 70 + "\n")


# CLI

def main():
    parser = argparse.ArgumentParser(description="DocuFlow v2 Dataset Generator")
    parser.add_argument(
        "--count",
        type=int,
        default=60,
        help="Nombre total de documents à générer (défaut: 60)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="./dataset",
        help="Dossier de sortie du dataset"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Seed aléatoire pour reproductibilité"
    )
    args = parser.parse_args()



    generate_dataset(count=args.count, output_dir=args.output, seed=args.seed)


if __name__ == "__main__":
    main()