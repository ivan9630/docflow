#!/usr/bin/env python3
"""
DocuFlow v2 — Entraînement du classifieur de documents
TF-IDF + SVM (LinearSVC) sur texte brut généré par faker.

Produit :
  - ml/models/classifier.joblib   (modèle sérialisé)
  - ml/models/metrics.json        (accuracy, F1, matrice de confusion)
  - ml/models/confusion_matrix.png

Usage :
    pip install scikit-learn faker joblib matplotlib seaborn
    python ml/train_classifier.py --samples 300
"""
import sys, os, json, random, argparse
from pathlib import Path
from datetime import datetime, timedelta

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    classification_report, confusion_matrix, accuracy_score, f1_score
)
from sklearn.pipeline import Pipeline
import joblib

# ── Ajout du data_generator au path ─────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "data_generator"))
from generate_dataset import (
    make_facture, make_attestation_urssaf, make_kbis, make_rib,
    gen_company, gen_siren, gen_siret, gen_tva, gen_iban,
    fake, FORMES_JURIDIQUES, CODES_NAF, TAUX_TVA
)

# ── Types manquants dans le générateur : devis + attestation fiscale ──

def make_devis() -> tuple:
    emetteur = gen_company()
    destinataire = gen_company()
    date = fake.date_between("-1y", "today")
    num = f"DEV-{date.year}-{random.randint(1000, 9999)}"
    taux = random.choice(TAUX_TVA)
    ht = round(random.uniform(500, 80000), 2)
    tva = round(ht * taux / 100, 2)
    ttc = round(ht + tva, 2)
    validite = random.randint(15, 90)
    text = f"""
                    DEVIS

Emetteur :          {emetteur['nom']}
Adresse :           {emetteur['adresse']}, {emetteur['cp']} {emetteur['ville']}
SIREN :             {emetteur['siren']}
SIRET :             {emetteur['siret']}
N TVA :             {emetteur['tva']}

Client :            {destinataire['nom']}
Adresse :           {destinataire['adresse']}, {destinataire['cp']} {destinataire['ville']}

Numero devis :      {num}
Date :              {date.strftime('%d/%m/%Y')}
Validite :          {validite} jours

Description des prestations :
  Developpement application web sur mesure         {ht:.2f} EUR
  Maintenance annuelle incluse

Total H.T. :        {ht:.2f} EUR
TVA {taux:.1f}% :   {tva:.2f} EUR
Total T.T.C. :      {ttc:.2f} EUR

Conditions : Acompte de 30% a la signature.
Devis valable {validite} jours.
"""
    return text, {"type": "devis"}


def make_attestation_fiscale() -> tuple:
    company = gen_company()
    date_emi = fake.date_between("-6m", "today")
    date_exp = date_emi + timedelta(days=365)
    text = f"""
        ATTESTATION DE REGULARITE FISCALE
        Direction Generale des Finances Publiques

Nous soussignes, certifions que l'entreprise :

Raison sociale :    {company['nom']}
SIREN :             {company['siren']}
SIRET :             {company['siret']}
Adresse :           {company['adresse']}, {company['cp']} {company['ville']}

Est a jour de ses obligations fiscales au {date_emi.strftime('%d/%m/%Y')}.

Cette attestation est delivree pour servir et valoir ce que de droit.
Valable jusqu'au : {date_exp.strftime('%d/%m/%Y')}

Numero attestation : AFI-{random.randint(100000, 999999)}

Direction Generale des Finances Publiques
"""
    return text, {"type": "attestation_fiscale"}


def make_contrat() -> tuple:
    partie1 = gen_company()
    partie2 = gen_company()
    date = fake.date_between("-2y", "today")
    duree = random.choice([12, 24, 36])
    montant = round(random.uniform(5000, 200000), 2)
    text = f"""
        CONTRAT DE PRESTATION DE SERVICES
        N CONTRAT : CTR-{date.year}-{random.randint(1000, 9999)}

ENTRE LES SOUSSIGNES :

{partie1['nom']}
SIREN : {partie1['siren']} - SIRET : {partie1['siret']}
{partie1['adresse']}, {partie1['cp']} {partie1['ville']}
Ci-apres denomme "Le Prestataire"

ET

{partie2['nom']}
SIREN : {partie2['siren']} - SIRET : {partie2['siret']}
{partie2['adresse']}, {partie2['cp']} {partie2['ville']}
Ci-apres denomme "Le Client"

ARTICLE 1 - OBJET
Le present contrat a pour objet la realisation de prestations de conseil.

ARTICLE 2 - DUREE
Le contrat est conclu pour une duree de {duree} mois a compter du {date.strftime('%d/%m/%Y')}.

ARTICLE 3 - REMUNERATION
Le montant total de la prestation s'eleve a {montant:.2f} EUR HT.

ARTICLE 4 - CONDITIONS DE PAIEMENT
Paiement a 30 jours fin de mois.

Fait en deux exemplaires originaux.
Date : {date.strftime('%d/%m/%Y')}
"""
    return text, {"type": "contrat"}


def make_bon_commande() -> tuple:
    emetteur = gen_company()
    fournisseur = gen_company()
    date = fake.date_between("-1y", "today")
    num = f"BC-{date.year}-{random.randint(1000, 9999)}"
    nb_lignes = random.randint(1, 5)
    lignes = []
    total_ht = 0
    articles = [
        "Fournitures de bureau", "Cartouches imprimante", "Papier A4 ramette",
        "Ecran moniteur 27 pouces", "Clavier sans fil", "Licence logiciel annuelle",
        "Disque dur SSD 1To", "Cable Ethernet Cat6", "Souris ergonomique",
    ]
    for _ in range(nb_lignes):
        art = random.choice(articles)
        qty = random.randint(1, 50)
        pu = round(random.uniform(5, 500), 2)
        lt = round(qty * pu, 2)
        total_ht += lt
        lignes.append(f"  {art:40s} {qty:3d} x {pu:8.2f} = {lt:10.2f} EUR")
    taux = 20.0
    tva = round(total_ht * taux / 100, 2)
    ttc = round(total_ht + tva, 2)
    text = f"""
                BON DE COMMANDE

Emetteur :          {emetteur['nom']}
SIREN :             {emetteur['siren']}
SIRET :             {emetteur['siret']}
Adresse :           {emetteur['adresse']}, {emetteur['cp']} {emetteur['ville']}

Fournisseur :       {fournisseur['nom']}
SIREN :             {fournisseur['siren']}

Numero commande :   {num}
Date :              {date.strftime('%d/%m/%Y')}
Date livraison :    {(date + timedelta(days=random.randint(7, 30))).strftime('%d/%m/%Y')}

Articles commandes :
{chr(10).join(lignes)}

Total H.T. :        {total_ht:.2f} EUR
TVA {taux:.1f}% :   {tva:.2f} EUR
Total T.T.C. :      {ttc:.2f} EUR

Conditions : Livraison franco de port.
"""
    return text, {"type": "bon_commande"}


# ── Génération du dataset d'entraînement ────────────────────────

GENERATORS = {
    "facture":             lambda: make_facture(True, False),
    "facture_anomalie":    lambda: make_facture(False, True),
    "devis":               make_devis,
    "bon_commande":        make_bon_commande,
    "attestation_urssaf":  lambda: make_attestation_urssaf(False),
    "attestation_fiscale": make_attestation_fiscale,
    "kbis":                make_kbis,
    "rib":                 make_rib,
    "contrat":             make_contrat,
}

# Factures normales et avec anomalies ont le même label "facture"
LABEL_MAP = {
    "facture": "facture",
    "facture_anomalie": "facture",
    "devis": "devis",
    "bon_commande": "bon_commande",
    "attestation_urssaf": "attestation_urssaf",
    "attestation_fiscale": "attestation_fiscale",
    "kbis": "kbis",
    "rib": "rib",
    "contrat": "contrat",
}


def generate_training_data(samples_per_class: int) -> tuple:
    texts, labels = [], []
    for gen_name, gen_fn in GENERATORS.items():
        label = LABEL_MAP[gen_name]
        for _ in range(samples_per_class):
            text, _ = gen_fn()
            # Variations : parfois en majuscules, parfois avec du bruit
            r = random.random()
            if r < 0.15:
                text = text.upper()
            elif r < 0.25:
                # Simuler erreurs OCR : remplacer quelques caractères
                chars = list(text)
                for idx in random.sample(range(len(chars)), min(20, len(chars))):
                    chars[idx] = random.choice("aeiouxzw0123")
                text = "".join(chars)
            texts.append(text)
            labels.append(label)
    return texts, labels


def train(samples_per_class: int = 50, output_dir: str = "ml/models"):
    print(f"\n--- Generation de {samples_per_class} echantillons x {len(GENERATORS)} generateurs ---\n")

    random.seed(None)  # Pas de seed fixe pour la variabilite
    texts, labels = generate_training_data(samples_per_class)

    print(f"Dataset total : {len(texts)} documents")
    for lbl in sorted(set(labels)):
        print(f"  {lbl:25s} : {labels.count(lbl)}")

    # ── Split train/test 80/20 ──────────────────────────────────
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )
    print(f"\nTrain : {len(X_train)} | Test : {len(X_test)}")

    # ── Pipeline TF-IDF + LinearSVC ─────────────────────────────
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            max_features=10000,
            ngram_range=(1, 2),
            sublinear_tf=True,
            strip_accents="unicode",
            min_df=2,
        )),
        ("clf", LinearSVC(
            C=1.0,
            max_iter=5000,
            class_weight="balanced",
        )),
    ])

    # ── Cross-validation ────────────────────────────────────────
    print("\nCross-validation 5-fold...")
    cv_scores = cross_val_score(pipeline, X_train, y_train, cv=5, scoring="f1_macro")
    print(f"CV F1-macro : {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")

    # ── Entraînement final ──────────────────────────────────────
    print("\nEntrainement final...")
    pipeline.fit(X_train, y_train)

    # ── Évaluation ──────────────────────────────────────────────
    y_pred = pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average="macro")
    report = classification_report(y_test, y_pred, output_dict=True)
    cm = confusion_matrix(y_test, y_pred, labels=sorted(set(labels)))

    print(f"\n{'='*50}")
    print(f"Accuracy  : {acc:.4f}")
    print(f"F1-macro  : {f1:.4f}")
    print(f"{'='*50}")
    print(classification_report(y_test, y_pred))

    # ── Sauvegarde ──────────────────────────────────────────────
    out = Path(ROOT / output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Modele
    model_path = out / "classifier.joblib"
    joblib.dump(pipeline, model_path)
    print(f"\nModele sauvegarde : {model_path}")

    # Metriques
    label_names = sorted(set(labels))
    metrics = {
        "accuracy": round(acc, 4),
        "f1_macro": round(f1, 4),
        "cv_f1_mean": round(cv_scores.mean(), 4),
        "cv_f1_std": round(cv_scores.std(), 4),
        "samples_per_class": samples_per_class,
        "total_samples": len(texts),
        "train_size": len(X_train),
        "test_size": len(X_test),
        "labels": label_names,
        "classification_report": report,
        "confusion_matrix": cm.tolist(),
        "trained_at": datetime.now().isoformat(),
    }
    metrics_path = out / "metrics.json"
    metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Metriques sauvegardees : {metrics_path}")

    # Matrice de confusion (image)
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import seaborn as sns

        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                    xticklabels=label_names, yticklabels=label_names, ax=ax)
        ax.set_xlabel("Predit")
        ax.set_ylabel("Reel")
        ax.set_title(f"Matrice de confusion — Accuracy={acc:.2%}, F1={f1:.2%}")
        plt.tight_layout()
        fig_path = out / "confusion_matrix.png"
        fig.savefig(fig_path, dpi=150)
        plt.close()
        print(f"Matrice de confusion : {fig_path}")
    except ImportError:
        print("matplotlib/seaborn non installes — matrice de confusion non generee")

    return pipeline, metrics


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Train DocuFlow document classifier")
    ap.add_argument("--samples", type=int, default=300,
                    help="Nombre d'echantillons par classe (default: 300)")
    ap.add_argument("--output", type=str, default="ml/models",
                    help="Dossier de sortie pour le modele")
    args = ap.parse_args()
    train(args.samples, args.output)
