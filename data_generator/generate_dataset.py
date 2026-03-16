#!/usr/bin/env python3
"""
DocuFlow v2 — Générateur de données de test
Produit des documents synthétiques réalistes pour entraînement/test OCR :
- Factures légitimes et falsifiées
- Devis, attestations URSSAF, KBIS, RIB
- Scans simulés (flou, rotation, bruit, faible résolution)

Usage :
    pip install faker reportlab Pillow numpy requests
    python generate_dataset.py --count 50 --output ./dataset
"""
import os, random, json, argparse
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter, ImageDraw, ImageFont
from faker import Faker

fake = Faker("fr_FR")
random.seed(42)

# ─── Données INSEE simulées ────────────────────────────────────────
FORMES_JURIDIQUES = ["SAS", "SARL", "SA", "EURL", "SASU", "SNC", "EI"]
CODES_NAF = ["6201Z", "4771Z", "4711D", "4120A", "7112B", "6312Z", "6202A"]
TAUX_TVA = [20.0, 10.0, 5.5]


def gen_siren() -> str:
    while True:
        n = "".join([str(random.randint(0,9)) for _ in range(9)])
        if luhn_valid(n): return n


def gen_siret(siren: str) -> str:
    nic = "".join([str(random.randint(0,9)) for _ in range(5)])
    return siren + nic


def gen_tva(siren: str) -> str:
    key = (12 + 3 * (int(siren) % 97)) % 97
    return f"FR{key:02d}{siren}"


def luhn_valid(n: str) -> bool:
    t = 0
    for i, d in enumerate(reversed(n)):
        x = int(d)
        if i % 2 == 1:
            x *= 2
            if x > 9: x -= 9
        t += x
    return t % 10 == 0


def gen_iban() -> str:
    bban = "3000400003" + "".join([str(random.randint(0,9)) for _ in range(11)])
    return f"FR76{bban}"


def gen_company() -> dict:
    siren = gen_siren()
    return {
        "nom":    fake.company() + " " + random.choice(FORMES_JURIDIQUES),
        "siren":  siren,
        "siret":  gen_siret(siren),
        "tva":    gen_tva(siren),
        "iban":   gen_iban(),
        "adresse":fake.street_address(),
        "cp":     fake.postcode(),
        "ville":  fake.city(),
    }


# ─── Génération texte document ────────────────────────────────────

def make_facture(legitimate=True, with_anomaly=False) -> tuple[str, dict]:
    emetteur = gen_company()
    destinataire = gen_company()
    date = fake.date_between("-1y", "today")
    num  = f"FAC-{date.year}-{random.randint(1000,9999)}"
    taux = random.choice(TAUX_TVA)
    ht   = round(random.uniform(100, 50000), 2)
    tva  = round(ht * taux / 100, 2)
    ttc  = round(ht + tva, 2)

    # Injection d'anomalie
    siret_affiche = emetteur["siret"]
    tva_affichee  = emetteur["tva"]
    if with_anomaly and random.random() > 0.5:
        siret_affiche = gen_siret(gen_siren())  # SIRET incohérent
    if with_anomaly and random.random() > 0.5:
        ttc = round(ttc * random.uniform(1.1, 1.5), 2)  # Montant falsifié

    text = f"""
                    FACTURE

Émetteur :          {emetteur['nom']}
Adresse :           {emetteur['adresse']}, {emetteur['cp']} {emetteur['ville']}
SIREN :             {emetteur['siren']}
SIRET :             {siret_affiche}
N° TVA :            {tva_affichee}
IBAN :              {emetteur['iban']}

Destinataire :      {destinataire['nom']}
Adresse :           {destinataire['adresse']}, {destinataire['cp']} {destinataire['ville']}

Numéro facture :    {num}
Date d'émission :   {date.strftime('%d/%m/%Y')}
Date d'échéance :   {(date + timedelta(days=30)).strftime('%d/%m/%Y')}

Description :
  Prestation de services informatiques           {ht:.2f} €

Total H.T. :        {ht:.2f} €
TVA {taux:.1f}% :   {tva:.2f} €
Total T.T.C. :      {ttc:.2f} €

Conditions de paiement : Virement bancaire sous 30 jours
"""
    metadata = {
        "type": "facture", "legitimate": legitimate, "has_anomaly": with_anomaly,
        "siren": emetteur["siren"], "siret": siret_affiche, "tva": tva_affichee,
        "ht": ht, "tva_val": tva, "ttc": ttc, "taux_tva": taux,
        "date": date.strftime('%d/%m/%Y'), "num": num,
    }
    return text, metadata


def make_attestation_urssaf(expired=False) -> tuple[str, dict]:
    company = gen_company()
    date_emi = fake.date_between("-6m", "today")
    if expired:
        date_exp = fake.date_between("-2y", "-1d")  # Expirée !
    else:
        date_exp = date_emi + timedelta(days=180)

    text = f"""
        ATTESTATION DE VIGILANCE
        URSSAF Île-de-France

Nous attestons que l'entreprise :

Raison sociale :    {company['nom']}
SIREN :             {company['siren']}
SIRET :             {company['siret']}
Adresse :           {company['adresse']}, {company['cp']} {company['ville']}

Est à jour de ses obligations déclaratives et de paiement
au {date_emi.strftime('%d/%m/%Y')}.

Cette attestation est valable jusqu'au : {date_exp.strftime('%d/%m/%Y')}

Numéro d'attestation : ATT-{random.randint(100000,999999)}

URSSAF Île-de-France — www.urssaf.fr
"""
    metadata = {
        "type": "attestation_urssaf", "legitimate": not expired,
        "has_anomaly": expired,
        "siren": company["siren"], "siret": company["siret"],
        "date_exp": date_exp.strftime('%d/%m/%Y'),
        "expired": expired,
    }
    return text, metadata


def make_kbis() -> tuple[str, dict]:
    company = gen_company()
    date_creation = fake.date_between("-10y", "-1y")
    forme = random.choice(FORMES_JURIDIQUES)
    naf = random.choice(CODES_NAF)
    ca = round(random.uniform(50000, 5000000), 2)
    text = f"""
        EXTRAIT KBIS
        Registre du Commerce et des Sociétés

Dénomination sociale :  {company['nom']}
Forme juridique :       {forme}
SIREN :                 {company['siren']}
SIRET :                 {company['siret']}
Code NAF/APE :          {naf}
N° TVA :                {company['tva']}
Capital social :        {round(random.uniform(1000,100000),2):,.2f} €
Date de création :      {date_creation.strftime('%d/%m/%Y')}

Siège social :
  {company['adresse']}
  {company['cp']} {company['ville']}

Chiffre d'affaires :    {ca:,.2f} €
Effectif :              {random.randint(1,500)} salariés

Greffe du Tribunal de Commerce — Délivré le {datetime.today().strftime('%d/%m/%Y')}
"""
    metadata = {"type": "kbis", "legitimate": True, "has_anomaly": False,
                "siren": company["siren"], "siret": company["siret"]}
    return text, metadata


def make_rib() -> tuple[str, dict]:
    company = gen_company()
    bic = "BNPAFRPP" + "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=3))
    text = f"""
        RELEVÉ D'IDENTITÉ BANCAIRE (RIB)

Titulaire :         {company['nom']}
Adresse :           {company['adresse']}, {company['cp']} {company['ville']}
SIREN :             {company['siren']}

Banque :            BNP Paribas
IBAN :              {company['iban']}
BIC :               {bic}
"""
    metadata = {"type": "rib", "legitimate": True, "has_anomaly": False,
                "siren": company["siren"], "iban": company["iban"], "bic": bic}
    return text, metadata


# ─── Simulation dégradation scan ─────────────────────────────────

def degrade_image(img: Image.Image, level: str = "medium") -> Image.Image:
    """Simule un scan de mauvaise qualité : flou, rotation, bruit, faible résolution."""
    if level == "low":
        return img
    # Rotation légère
    angle = random.uniform(-3, 3) if level == "medium" else random.uniform(-8, 8)
    img = img.rotate(angle, fillcolor="white", expand=False)
    # Flou
    blur_r = random.uniform(0.3, 1.0) if level == "medium" else random.uniform(1.0, 2.5)
    img = img.filter(ImageFilter.GaussianBlur(radius=blur_r))
    # Bruit
    arr = np.array(img)
    noise_std = 10 if level == "medium" else 30
    noise = np.random.normal(0, noise_std, arr.shape).astype(np.int16)
    arr = np.clip(arr.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr)
    # Réduction résolution (simulation smartphone)
    if level == "hard":
        w, h = img.size
        img = img.resize((w//3, h//3), Image.LANCZOS).resize((w, h), Image.LANCZOS)
    return img


def text_to_image(text: str, degrade_level: str = "none") -> Image.Image:
    """Convertit du texte en image (simulation scan)."""
    W, H = 800, 1100
    img = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 13)
    except:
        font = ImageFont.load_default()
    y = 30
    for line in text.split("\n"):
        draw.text((40, y), line, fill="black", font=font)
        y += 18
    if degrade_level != "none":
        img = degrade_image(img, degrade_level)
    return img


# ─── Main ─────────────────────────────────────────────────────────

def generate_dataset(count: int, output_dir: str):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "images").mkdir(exist_ok=True)
    (out / "texts").mkdir(exist_ok=True)
    (out / "metadata").mkdir(exist_ok=True)

    generators = [
        lambda: make_facture(True, False),
        lambda: make_facture(False, True),
        lambda: make_attestation_urssaf(False),
        lambda: make_attestation_urssaf(True),
        lambda: make_kbis(),
        lambda: make_rib(),
    ]
    degrade_levels = ["none", "low", "medium", "hard"]
    all_meta = []

    print(f"\n🔧 Génération de {count} documents dans {output_dir}/\n")
    for i in range(count):
        gen = random.choice(generators)
        text, meta = gen()
        level = random.choice(degrade_levels)
        meta["degrade_level"] = level
        meta["index"] = i

        # Sauvegarder texte brut
        (out / "texts" / f"doc_{i:04d}.txt").write_text(text, encoding="utf-8")

        # Générer image
        img = text_to_image(text, level)
        img_path = out / "images" / f"doc_{i:04d}.png"
        img.save(img_path)

        # Métadonnées
        all_meta.append(meta)
        status = "✅ légitime" if meta["legitimate"] else "⚠️  anomalie"
        print(f"  [{i+1:3d}/{count}] {meta['type']:25s} | {level:6s} | {status}")

    # Sauvegarder manifest
    manifest_path = out / "metadata" / "manifest.json"
    manifest_path.write_text(json.dumps(all_meta, ensure_ascii=False, indent=2), encoding="utf-8")

    # Stats
    legit = sum(1 for m in all_meta if m["legitimate"])
    anomaly = sum(1 for m in all_meta if m["has_anomaly"])
    by_type = {}
    for m in all_meta:
        by_type[m["type"]] = by_type.get(m["type"], 0) + 1

    print(f"\n{'─'*50}")
    print(f"✅ {count} documents générés")
    print(f"   Légitimes  : {legit}")
    print(f"   Anomalies  : {anomaly}")
    print(f"   Par type   : {by_type}")
    print(f"   Output     : {out.resolve()}")
    print(f"{'─'*50}\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="DocuFlow Dataset Generator")
    ap.add_argument("--count",  type=int, default=100, help="Nombre de documents à générer")
    ap.add_argument("--output", type=str, default="./dataset", help="Dossier de sortie")
    args = ap.parse_args()
    generate_dataset(args.count, args.output)
