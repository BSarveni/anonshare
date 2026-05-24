"""Content moderation using Detoxify."""

import logging
from typing import Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)

TOXICITY_THRESHOLD = 0.7
THREAT_THRESHOLD = 0.6


def _extract_score(scores: dict, key: str) -> float:
    value = scores[key]
    if hasattr(value, "__getitem__") and not isinstance(value, (str, bytes)):
        return float(value[0])
    return float(value)


class ModerationResult(BaseModel):
    allowed: bool
    reason: Optional[str] = None


class ContentModerator:
    """Singleton Detoxify-backed text moderator."""

    _instance: "ContentModerator | None" = None

    def __new__(cls) -> "ContentModerator":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self._model = None
        self._load_failed = False
        self._load_model()

    def _load_model(self) -> None:
        try:
            from detoxify import Detoxify

            self._model = Detoxify("original")
            logger.info("Detoxify model loaded successfully")
        except Exception as exc:
            self._load_failed = True
            logger.warning(
                "Detoxify failed to load; content moderation disabled (%s: %s)",
                type(exc).__name__,
                exc,
            )

    def analyze_text(self, text: str) -> dict:
        """
        Analyze text and return moderation scores.

        Keys: harmful (bool), toxicity_score, threat_score, reason (str)
        """
        if not text or not text.strip():
            return {
                "harmful": False,
                "toxicity_score": 0.0,
                "threat_score": 0.0,
                "reason": "",
            }

        if self._load_failed or self._model is None:
            return {
                "harmful": False,
                "toxicity_score": 0.0,
                "threat_score": 0.0,
                "reason": "Moderation unavailable (model not loaded)",
            }

        try:
            scores = self._model.predict(text.strip())
            toxicity_score = _extract_score(scores, "toxicity")
            threat_score = _extract_score(scores, "threat")
        except Exception as exc:
            logger.warning("Detoxify prediction failed: %s", exc)
            return {
                "harmful": False,
                "toxicity_score": 0.0,
                "threat_score": 0.0,
                "reason": "Moderation unavailable (prediction error)",
            }

        harmful = toxicity_score > TOXICITY_THRESHOLD or threat_score > THREAT_THRESHOLD
        if harmful:
            parts = []
            if toxicity_score > TOXICITY_THRESHOLD:
                parts.append(f"toxicity {toxicity_score:.2f} > {TOXICITY_THRESHOLD}")
            if threat_score > THREAT_THRESHOLD:
                parts.append(f"threat {threat_score:.2f} > {THREAT_THRESHOLD}")
            reason = "Harmful content: " + ", ".join(parts)
        else:
            reason = ""

        return {
            "harmful": harmful,
            "toxicity_score": toxicity_score,
            "threat_score": threat_score,
            "reason": reason,
        }

    def analyze_image_caption(self, caption: str) -> dict:
        """Same analysis pipeline as plain text (post captions)."""
        return self.analyze_text(caption)

    def moderate(self, text: str | None) -> ModerationResult:
        if text is None or not str(text).strip():
            return ModerationResult(allowed=True)

        analysis = self.analyze_text(str(text))
        if analysis["harmful"]:
            return ModerationResult(
                allowed=False,
                reason=analysis["reason"] or "Harmful content detected",
            )
        return ModerationResult(allowed=True)


def get_moderator() -> ContentModerator:
    return ContentModerator()


def moderate(text: str | None) -> ModerationResult:
    """Moderate text before persisting. Empty/None text is always allowed."""
    if text is None or not str(text).strip():
        return ModerationResult(allowed=True)

    analysis = get_moderator().analyze_text(str(text))
    if analysis["harmful"]:
        return ModerationResult(allowed=False, reason=analysis["reason"] or "Harmful content detected")
    return ModerationResult(allowed=True)


# Backward-compatible helpers
def analyze_toxicity(text: str) -> dict[str, float]:
    analysis = get_moderator().analyze_text(text)
    return {
        "toxicity": analysis["toxicity_score"],
        "threat": analysis["threat_score"],
        "severe_toxicity": 0.0,
        "obscene": 0.0,
        "insult": 0.0,
    }


def toxicity_summary(text: str) -> float:
    analysis = get_moderator().analyze_text(text)
    return max(analysis["toxicity_score"], analysis["threat_score"])
