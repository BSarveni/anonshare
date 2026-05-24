"""Anomaly detection with a persisted IsolationForest model."""

from __future__ import annotations

import logging
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

logger = logging.getLogger(__name__)

MODEL_DIR = Path(__file__).resolve().parent / "models"
MODEL_PATH = MODEL_DIR / "isolation_forest.joblib"

ANOMALY_SCORE_THRESHOLD = 0.7
FEATURE_NAMES = ("posts_per_hour", "messages_per_hour", "report_count")

_loaded_model: IsolationForest | None = None


def _sigmoid(raw: float) -> float:
    return float(1.0 / (1.0 + np.exp(-raw)))


def user_feature_vector(
    posts_per_hour: float,
    messages_per_hour: float,
    report_count: int,
) -> list[float]:
    return [float(posts_per_hour), float(messages_per_hour), float(report_count)]


def load_model() -> IsolationForest | None:
    global _loaded_model
    if _loaded_model is not None:
        return _loaded_model
    if not MODEL_PATH.exists():
        return None
    try:
        _loaded_model = joblib.load(MODEL_PATH)
        return _loaded_model
    except Exception as exc:
        logger.warning("Failed to load anomaly model: %s", exc)
        return None


def save_model(model: IsolationForest) -> Path:
    global _loaded_model
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    _loaded_model = model
    logger.info("Anomaly model saved to %s", MODEL_PATH)
    return MODEL_PATH


def retrain_model(feature_matrix: np.ndarray) -> IsolationForest | None:
    """Train IsolationForest on user behavior features and persist to disk."""
    if feature_matrix.size == 0 or len(feature_matrix) < 2:
        logger.warning("Not enough samples to retrain anomaly model (need >= 2)")
        return None

    contamination = min(0.25, max(0.05, 2.0 / len(feature_matrix)))
    model = IsolationForest(contamination=contamination, random_state=42)
    model.fit(feature_matrix)
    save_model(model)
    return model


def analyze_features(features: list[float]) -> dict:
    """
    Score a single feature vector against the trained model.

    Returns: anomaly_score, is_anomaly, reason
    """
    if not features:
        return {
            "anomaly_score": 0.0,
            "is_anomaly": False,
            "reason": "No features provided",
        }

    model = load_model()
    if model is None:
        return {
            "anomaly_score": 0.0,
            "is_anomaly": False,
            "reason": "Anomaly model not trained yet",
        }

    X = np.array(features, dtype=float).reshape(1, -1)
    raw = float(-model.score_samples(X)[0])
    anomaly_score = _sigmoid(raw)
    prediction = int(model.predict(X)[0])
    is_anomaly = prediction == -1 or anomaly_score >= ANOMALY_SCORE_THRESHOLD

    reason = ""
    if is_anomaly:
        reason = (
            f"Behavioral anomaly detected (score={anomaly_score:.2f}, "
            f"posts/hr={features[0]:.2f}, messages/hr={features[1]:.2f}, reports={features[2]:.0f})"
        )

    return {
        "anomaly_score": anomaly_score,
        "is_anomaly": is_anomaly,
        "reason": reason,
    }


def compute_anomaly_score(features: list[float]) -> float:
    """Backward-compatible helper returning only the score."""
    return analyze_features(features)["anomaly_score"]


def batch_anomaly_scores(rows: list[list[float]]) -> list[float]:
    return [analyze_features(row)["anomaly_score"] for row in rows]
