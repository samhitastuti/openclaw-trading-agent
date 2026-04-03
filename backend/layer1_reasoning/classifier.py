"""
classifier.py — AI-powered intent classification for Layer 1 Reasoning.

Wraps the IntentClassifier from backend/ai/intent_classifier.py and
returns structured Pydantic models for use in the trade pipeline.
"""

import logging
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from backend.ai.intent_classifier import IntentClassifier as _BaseClassifier

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Output model
# ─────────────────────────────────────────────


class IntentClassification(BaseModel):
    """Structured result from the AI intent classifier."""

    intent: str = Field(..., description="Classified intent type")
    risk_level: str = Field(
        ..., description="Risk level: safe | caution | high_risk | critical"
    )
    confidence: float = Field(..., description="Classification confidence (0–1)")
    risk_factors: List[str] = Field(
        default_factory=list, description="Detected risk factors"
    )
    reasoning: str = Field(default="", description="Human-readable explanation")
    ai_model: Optional[str] = Field(
        default=None, description="AI model used for classification"
    )
    extracted_data: Optional[Dict[str, Any]] = Field(
        default=None, description="Extracted structured data (ticker, qty, price, …)"
    )


# ─────────────────────────────────────────────
# Classifier
# ─────────────────────────────────────────────


class IntentClassifier:
    """
    Layer 1 AI-powered intent classifier.

    Classifies trade instructions, detects threats, and assigns risk levels.
    Uses OpenAI when available, falls back to local NLP.

    Usage::

        classifier = IntentClassifier()
        result = classifier.classify("Buy 2 shares of MSFT at $430")
        # IntentClassification(intent='buy_stock', risk_level='safe', ...)
    """

    def __init__(self) -> None:
        self._classifier = _BaseClassifier()
        logger.info("✅ Layer1 IntentClassifier initialized")

    def classify(self, instruction: str) -> IntentClassification:
        """
        Classify a trade instruction.

        Args:
            instruction: Natural-language trade instruction.

        Returns:
            IntentClassification with intent, risk_level, confidence, etc.
        """
        raw: Dict[str, Any] = self._classifier.classify(instruction)
        return IntentClassification(
            intent=raw.get("intent", "unknown"),
            risk_level=raw.get("risk_level", "safe"),
            confidence=float(raw.get("confidence", 0.5)),
            risk_factors=raw.get("risk_factors", []),
            reasoning=raw.get("reasoning", ""),
            ai_model=raw.get("ai_model"),
            extracted_data=raw.get("extracted_data"),
        )
