"""Service de classification locale — modèle TF-IDF + SVM entraîné"""
import os
from pathlib import Path
import structlog

logger = structlog.get_logger()

_pipeline = None
# En container : /app/ml/models/, en local : ../../ml/models/
_APP_DIR = Path(__file__).resolve().parent.parent.parent
MODEL_PATH = _APP_DIR / "ml" / "models" / "classifier.joblib"


def _load_model():
    global _pipeline
    if _pipeline is not None:
        return _pipeline
    if not MODEL_PATH.exists():
        logger.warning(f"Modèle classifieur non trouvé : {MODEL_PATH}")
        return None
    try:
        import joblib
        _pipeline = joblib.load(MODEL_PATH)
        logger.info(f"Classifieur local chargé : {MODEL_PATH}")
        return _pipeline
    except Exception as e:
        logger.error(f"Erreur chargement classifieur : {e}")
        return None


def classify_local(text: str) -> dict | None:
    """Classifie un document avec le modèle local.
    Retourne {"type_document": str, "confidence": float} ou None si le modèle n'est pas dispo."""
    model = _load_model()
    if model is None:
        return None
    try:
        prediction = model.predict([text])[0]
        # LinearSVC a decision_function, pas predict_proba
        scores = model.decision_function([text])[0]
        # Convertir en pseudo-probabilités via softmax
        import numpy as np
        exp_scores = np.exp(scores - np.max(scores))
        probs = exp_scores / exp_scores.sum()
        confidence = float(np.max(probs))
        return {
            "type_document": prediction,
            "confidence": round(confidence, 4),
            "method": "local_svm",
        }
    except Exception as e:
        logger.error(f"Classification locale erreur : {e}")
        return None
