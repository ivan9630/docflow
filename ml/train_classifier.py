#!/usr/bin/env python3
"""
DocuFlow v2 -- Entrainement du classifieur de documents
TF-IDF + SVM (LinearSVC) sur texte genere par faker + bruit OCR simule.

Produit :
  - ml/models/classifier.joblib   (modele serialise)
  - ml/models/metrics.json        (accuracy, F1, matrice de confusion)
  - ml/models/confusion_matrix.png

Usage :
    pip install scikit-learn faker joblib matplotlib seaborn numpy Pillow
    python ml/train_classifier.py --samples 200
"""
import sys, os, json, random, argparse, re
from pathlib import Path
from datetime import datetime

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    classification_report, confusion_matrix, accuracy_score, f1_score
)
from sklearn.pipeline import Pipeline
import joblib

# -- Import du generateur --
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "data_generator"))
from generate_dataset import (
    make_facture_legitime, make_facture_fake_siret, make_facture_fake_amounts,
    make_devis, make_bon_commande, make_contrat,
    make_attestation_urssaf, make_attestation_fiscale, make_attestation_siret,
    make_kbis, make_rib, make_avoir, make_note_frais,
    set_seed,
)

# -- Simulation bruit OCR --

OCR_SUBSTITUTIONS = {
    "e": ["c", "o", "a"],
    "a": ["o", "e"],
    "o": ["0", "c"],
    "i": ["1", "l", "j"],
    "l": ["1", "i", "|"],
    "0": ["O", "o"],
    "1": ["l", "i", "I"],
    "5": ["S", "s"],
    "S": ["5", "s"],
    "8": ["B", "3"],
    "B": ["8", "3"],
    "G": ["6", "C"],
    "t": ["f", "+"],
    "r": ["n", "v"],
    "n": ["m", "r"],
}


def simulate_ocr_noise(text: str, error_rate: float = 0.03) -> str:
    """Simule des erreurs OCR sur du texte : substitutions, insertions, suppressions."""
    chars = list(text)
    result = []
    for c in chars:
        r = random.random()
        if r < error_rate and c in OCR_SUBSTITUTIONS:
            result.append(random.choice(OCR_SUBSTITUTIONS[c]))
        elif r < error_rate * 1.3 and c.isalnum():
            pass  # suppression
        elif r < error_rate * 1.5 and c == " ":
            result.append("  " if random.random() < 0.5 else "")
        else:
            result.append(c)
    return "".join(result)


def simulate_tesseract_output(text: str) -> str:
    """Simule la sortie réelle de Tesseract : mise en page cassée, espaces, artefacts."""
    lines = text.split("\n")
    result = []
    for line in lines:
        if not line.strip():
            # Tesseract ajoute parfois des lignes vides en plus
            if random.random() < 0.3:
                result.append("")
            continue

        # Casser l'indentation (Tesseract ne la préserve pas)
        line = line.lstrip()

        # Espaces multiples aléatoires (Tesseract output)
        if random.random() < 0.4:
            words = line.split()
            line = ("  " if random.random() < 0.3 else " ").join(
                ("  ".join(w) if random.random() < 0.05 else w) for w in words
            )

        # Couper des mots en deux (OCR scan avec colonnes)
        if random.random() < 0.08:
            words = line.split()
            if len(words) > 3:
                idx = random.randint(1, len(words) - 2)
                words.insert(idx, "\n")
                line = " ".join(words)

        # Caractères parasites (artefacts de scan)
        if random.random() < 0.05:
            parasites = ["|", "~", "`", "}", "{", "\\", "_", "°"]
            pos = random.randint(0, max(0, len(line) - 1))
            line = line[:pos] + random.choice(parasites) + line[pos:]

        # Accents perdus (fréquent en OCR français)
        if random.random() < 0.15:
            line = line.replace("é", "e").replace("è", "e").replace("ê", "e")
            line = line.replace("à", "a").replace("â", "a")
            line = line.replace("ù", "u").replace("û", "u")
            line = line.replace("ô", "o").replace("î", "i")

        result.append(line)
    return "\n".join(result)


# -- Variantes de titres pour chaque type (simule docs reels) --

TITLE_VARIANTS = {
    "facture": ["FACTURE", "Facture n", "INVOICE", "Note d'honoraires", "FACTURE DE VENTE",
                "Facture commerciale", "FACTURE PROFORMA", "Facture de prestation"],
    "devis": ["DEVIS", "Devis n", "ESTIMATION", "PROPOSITION COMMERCIALE",
              "Devis estimatif", "OFFRE DE PRIX", "Proposition tarifaire"],
    "bon_commande": ["BON DE COMMANDE", "Bon de commande n", "PURCHASE ORDER",
                     "COMMANDE", "Ordre d'achat", "BC"],
    "contrat": ["CONTRAT", "CONTRAT DE PRESTATION", "CONVENTION", "ACCORD CADRE",
                "Contrat de service", "CONTRAT COMMERCIAL"],
    "attestation_urssaf": ["ATTESTATION DE VIGILANCE", "Attestation URSSAF",
                           "ATTESTATION DE REGULARITE SOCIALE", "Attestation de vigilance"],
    "attestation_fiscale": ["ATTESTATION DE REGULARITE FISCALE", "Attestation fiscale",
                            "ATTESTATION FISCALE", "Attestation de regularite fiscale DGFiP"],
    "attestation_siret": ["ATTESTATION SIRET", "AVIS DE SITUATION SIRENE",
                          "Attestation d'inscription au repertoire", "AVIS SIRENE INSEE"],
    "kbis": ["EXTRAIT KBIS", "Extrait K-bis", "KBIS", "Extrait du RCS",
             "Extrait Kbis du Registre du Commerce"],
    "rib": ["RELEVE D'IDENTITE BANCAIRE", "RIB / IBAN", "RIB",
            "Releve d'identite bancaire / IBAN", "COORDONNEES BANCAIRES"],
    "avoir": ["AVOIR", "NOTE DE CREDIT", "Avoir n", "CREDIT NOTE",
              "AVOIR COMMERCIAL", "Note de credit"],
    "note_frais": ["NOTE DE FRAIS", "Fiche de frais", "NDF", "RAPPORT DE DEPENSES",
                   "Note de frais professionnels"],
}

# -- Generateurs indexes par label --

GENERATORS = {
    "facture": [
        lambda i: make_facture_legitime(f"TRAIN-{i}"),
        lambda i: make_facture_fake_siret(f"TRAIN-{i}"),
        lambda i: make_facture_fake_amounts(f"TRAIN-{i}"),
    ],
    "devis": [
        lambda i: make_devis(f"TRAIN-{i}"),
    ],
    "bon_commande": [
        lambda i: make_bon_commande(f"TRAIN-{i}"),
    ],
    "contrat": [
        lambda i: make_contrat(f"TRAIN-{i}"),
    ],
    "attestation_urssaf": [
        lambda i: make_attestation_urssaf(f"TRAIN-{i}", expired=False),
        lambda i: make_attestation_urssaf(f"TRAIN-{i}", expired=True),
    ],
    "attestation_fiscale": [
        lambda i: make_attestation_fiscale(f"TRAIN-{i}"),
    ],
    "attestation_siret": [
        lambda i: make_attestation_siret(f"TRAIN-{i}"),
    ],
    "kbis": [
        lambda i: make_kbis(f"TRAIN-{i}"),
    ],
    "rib": [
        lambda i: make_rib(f"TRAIN-{i}"),
    ],
    "avoir": [
        lambda i: make_avoir(f"TRAIN-{i}"),
    ],
    "note_frais": [
        lambda i: make_note_frais(f"TRAIN-{i}"),
    ],
}


def augment_text(text: str, label: str) -> str:
    """Augmentation de donnees : variantes realistes pour l'entrainement."""

    # 1. Remplacer le titre par une variante aleatoire
    if label in TITLE_VARIANTS and random.random() < 0.5:
        variant = random.choice(TITLE_VARIANTS[label])
        lines = text.split("\n")
        # Trouver la premiere ligne non vide (le titre)
        for i, line in enumerate(lines):
            if line.strip():
                lines[i] = " " * random.randint(0, 20) + variant
                break
        text = "\n".join(lines)

    # 2. Melanger l'ordre de certains champs (20%)
    if random.random() < 0.20:
        lines = text.split("\n")
        # Trouver des blocs de champs (lignes avec ":")
        field_indices = [i for i, l in enumerate(lines) if ":" in l and len(l.strip()) > 5]
        if len(field_indices) >= 3:
            subset = random.sample(field_indices, min(3, len(field_indices)))
            contents = [lines[i] for i in subset]
            random.shuffle(contents)
            for i, idx in enumerate(subset):
                lines[idx] = contents[i]
            text = "\n".join(lines)

    # 3. Ajouter du texte parasite (headers, footers de scan)
    if random.random() < 0.15:
        parasites = [
            "--- Page 1/1 ---", "SCAN_001.pdf", "Numerise le 15/03/2026",
            "CONFIDENTIEL", "COPIE", "ORIGINAL", "NE PAS DIFFUSER",
            "Ref: ARCH-2026-001", "...", "|||||||||||||||",
        ]
        text = random.choice(parasites) + "\n\n" + text

    if random.random() < 0.10:
        text = text + "\n\n--- Fin du document ---\n"

    # 4. Tronquer (OCR partiel : debut, milieu ou fin)
    if random.random() < 0.20:
        lines = text.split("\n")
        total = len(lines)
        if total > 10:
            mode = random.choice(["start", "middle", "end"])
            keep = random.randint(total // 3, total * 2 // 3)
            if mode == "start":
                lines = lines[:keep]
            elif mode == "end":
                lines = lines[total - keep:]
            else:
                start = random.randint(0, total - keep)
                lines = lines[start:start + keep]
            text = "\n".join(lines)

    # 5. Simulation sortie Tesseract (60% des cas)
    if random.random() < 0.60:
        text = simulate_tesseract_output(text)

    # 6. Bruit OCR supplémentaire
    r = random.random()
    if r < 0.15:
        text = simulate_ocr_noise(text, error_rate=0.03)
    elif r < 0.30:
        text = simulate_ocr_noise(text, error_rate=0.07)
    elif r < 0.40:
        text = simulate_ocr_noise(text, error_rate=0.12)

    # 7. Majuscules
    if random.random() < 0.08:
        text = text.upper()

    return text


def generate_training_data(samples_per_class: int) -> tuple:
    texts, labels = [], []
    idx = 0
    for label, generators in GENERATORS.items():
        for _ in range(samples_per_class):
            gen = random.choice(generators)
            text, _ = gen(idx)
            idx += 1

            text = augment_text(text, label)

            texts.append(text)
            labels.append(label)
    return texts, labels


def train(samples_per_class: int = 200, output_dir: str = "ml/models"):
    print(f"\n--- Generation de {samples_per_class} echantillons x {len(GENERATORS)} classes ---\n")

    set_seed(None)  # pas de seed fixe pour variabilite
    texts, labels = generate_training_data(samples_per_class)

    print(f"Dataset total : {len(texts)} documents")
    for lbl in sorted(set(labels)):
        print(f"  {lbl:25s} : {labels.count(lbl)}")

    # -- Split train/test 80/20 --
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )
    print(f"\nTrain : {len(X_train)} | Test : {len(X_test)}")

    # -- Pipeline TF-IDF + LinearSVC --
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

    # -- Cross-validation --
    print("\nCross-validation 5-fold...")
    cv_scores = cross_val_score(pipeline, X_train, y_train, cv=5, scoring="f1_macro")
    print(f"CV F1-macro : {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")

    # -- Entrainement final --
    print("\nEntrainement final...")
    pipeline.fit(X_train, y_train)

    # -- Evaluation --
    y_pred = pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average="macro")
    report = classification_report(y_test, y_pred, output_dict=True)
    label_names = sorted(set(labels))
    cm = confusion_matrix(y_test, y_pred, labels=label_names)

    print(f"\n{'='*50}")
    print(f"Accuracy  : {acc:.4f}")
    print(f"F1-macro  : {f1:.4f}")
    print(f"{'='*50}")
    print(classification_report(y_test, y_pred))

    # -- Sauvegarde --
    out = Path(ROOT / output_dir)
    out.mkdir(parents=True, exist_ok=True)

    model_path = out / "classifier.joblib"
    joblib.dump(pipeline, model_path)
    print(f"\nModele sauvegarde : {model_path}")

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
        "ocr_noise_applied": True,
        "noise_levels": {"clean": "40%", "light_2pct": "25%", "medium_5pct": "20%", "heavy_8pct": "15%"},
        "classification_report": report,
        "confusion_matrix": cm.tolist(),
        "trained_at": datetime.now().isoformat(),
    }
    metrics_path = out / "metrics.json"
    metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Metriques : {metrics_path}")

    # Matrice de confusion
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
        ax.set_title(f"Matrice de confusion - Accuracy={acc:.2%}, F1={f1:.2%}")
        plt.tight_layout()
        fig_path = out / "confusion_matrix.png"
        fig.savefig(fig_path, dpi=150)
        plt.close()
        print(f"Matrice de confusion : {fig_path}")
    except ImportError:
        print("matplotlib/seaborn non installes - matrice non generee")

    return pipeline, metrics


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Train DocuFlow document classifier")
    ap.add_argument("--samples", type=int, default=200,
                    help="Nombre d'echantillons par classe (default: 200)")
    ap.add_argument("--output", type=str, default="ml/models",
                    help="Dossier de sortie")
    args = ap.parse_args()
    train(args.samples, args.output)
