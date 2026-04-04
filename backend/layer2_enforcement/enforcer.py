"""
enforcer.py — Policy enforcement for Layer 2.

Validates parsed trade intents against declarative policy constraints
and AI risk classifications.  Returns structured PolicyDecision objects.
"""

import logging
from typing import List, Optional

from pydantic import BaseModel, Field

from backend.config.constants import SUSPICIOUS_KEYWORDS
from backend.layer2_enforcement.policy_models import get_trade_policy

logger = logging.getLogger(__name__)

# AI risk level → numeric score on a 4-level scale (0 = safest, 1 = most dangerous).
# Values are evenly spaced: safe=0/3, caution=1/3, high_risk=2/3, critical=3/3.
_RISK_ORDER: dict = {
    "safe": 0.0,
    "caution": round(1 / 3, 3),    # 0.333
    "high_risk": round(2 / 3, 3),  # 0.667
    "critical": 1.0,
}


# ─────────────────────────────────────────────
# Output model
# ─────────────────────────────────────────────


class PolicyDecision(BaseModel):
    """Result of a policy enforcement check."""

    allowed: bool = Field(..., description="Whether the action is permitted")
    reason: str = Field(..., description="Human-readable enforcement decision")
    constraints_checked: List[str] = Field(
        default_factory=list, description="Constraint checks performed (in order)"
    )


# ─────────────────────────────────────────────
# Enforcer
# ─────────────────────────────────────────────


class PolicyEnforcer:
    """
    Layer 2 policy enforcer.

    Validates a parsed intent against the configured trade policy,
    factoring in the AI classification risk score.

    Checks (in order):
    1. AI risk threshold
    2. Prohibited / suspicious patterns
    3. Ticker whitelist  (trade intents only)
    4. Max shares per order  (trade intents only)
    5. Per-order value limit  (trade intents only)

    Usage::

        enforcer = PolicyEnforcer()
        decision = enforcer.enforce(parsed_intent, classification)
        # PolicyDecision(allowed=True, reason='…', constraints_checked=[…])
    """

    def __init__(self) -> None:
        logger.info("✅ PolicyEnforcer initialized")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def enforce(self, parsed_intent, classification) -> PolicyDecision:
        """
        Enforce policy against a parsed intent and AI classification.

        Args:
            parsed_intent: Intent object from intent_parser (may be None).
            classification: IntentClassification from the AI classifier.

        Returns:
            PolicyDecision with allowed flag, reason, and constraints checked.
        """
        constraints_checked: List[str] = []
        trade_policy = get_trade_policy()

        # ── 1. AI risk threshold ──────────────────────────────────────
        ai_risk_threshold: float = float(
            trade_policy.get("ai_risk_threshold", 0.8)
        )
        risk_level: str = (classification.risk_level or "safe").lower()
        risk_score: float = _RISK_ORDER.get(risk_level, 0.0)

        constraints_checked.append(
            f"ai_risk_check: {risk_level} (score={risk_score:.3f}, threshold={ai_risk_threshold})"
        )

        if risk_score >= ai_risk_threshold:
            return PolicyDecision(
                allowed=False,
                reason=(
                    f"AI risk level '{risk_level}' exceeds threshold "
                    f"({ai_risk_threshold}): {classification.reasoning}"
                ),
                constraints_checked=constraints_checked,
            )

        # ── 2. Prohibited / suspicious patterns ───────────────────────
        raw_input: str = (
            parsed_intent.raw_input if parsed_intent else ""
        ) or ""
        raw_lower = raw_input.lower()

        for keyword in SUSPICIOUS_KEYWORDS:
            if keyword in raw_lower:
                constraints_checked.append(
                    f"prohibited_pattern_check: FAILED (keyword={keyword!r})"
                )
                return PolicyDecision(
                    allowed=False,
                    reason=f"Prohibited pattern detected: '{keyword}'",
                    constraints_checked=constraints_checked,
                )

        constraints_checked.append("prohibited_pattern_check: PASSED")

        # ── 3. Return blocked if intent could not be parsed ───────────
        if parsed_intent is None:
            return PolicyDecision(
                allowed=False,
                reason="Unrecognized intent or request could not be parsed.",
                constraints_checked=constraints_checked,
            )

        # ── 3b. If not a trade, skip remaining ────────────────────────
        if not parsed_intent.is_trade():
            return PolicyDecision(
                allowed=True,
                reason="Non-trade request passed all risk checks",
                constraints_checked=constraints_checked,
            )

        # ── 4. Ticker whitelist (omit or empty allowed_tickers = any symbol) ──
        raw_allowed = trade_policy.get("allowed_tickers") or []
        allowed_tickers: List[str] = (
            raw_allowed if isinstance(raw_allowed, list) else []
        )
        ticker: str = parsed_intent.ticker
        ticker_u = (ticker or "").upper()
        allowed_set = {str(t).upper() for t in allowed_tickers}

        constraints_checked.append(f"ticker_check: {ticker}")

        if allowed_tickers and ticker_u not in allowed_set:
            return PolicyDecision(
                allowed=False,
                reason=(
                    f"Ticker '{ticker}' is not in the allowed list: {allowed_tickers}"
                ),
                constraints_checked=constraints_checked,
            )

        if allowed_tickers:
            constraints_checked.append(
                f"ticker_check: PASSED ({ticker} on whitelist)"
            )
        else:
            constraints_checked.append("ticker_check: PASSED (no whitelist)")

        # ── 5. Max shares per order ───────────────────────────────────
        max_shares: float = float(
            trade_policy.get("max_shares_per_order", float("inf"))
        )
        quantity: float = parsed_intent.quantity

        logger.debug(
            "max_shares_check: quantity=%s, max_shares_per_order=%s",
            quantity,
            max_shares,
        )

        if quantity > max_shares:
            constraints_checked.append(
                f"max_shares_check: FAILED ({quantity:.0f} > limit {max_shares:.0f})"
            )
            return PolicyDecision(
                allowed=False,
                reason="Exceeds maximum shares per order",
                constraints_checked=constraints_checked,
            )

        constraints_checked.append(
            f"max_shares_check: PASSED ({quantity:.0f} <= limit {max_shares:.0f})"
        )

        # ── 6. Per-order value limit ──────────────────────────────────
        per_order_limit: float = float(
            trade_policy.get("per_order_value_limit", float("inf"))
        )
        price: float = parsed_intent.price or 0.0
        order_value: float = quantity * price

        constraints_checked.append(
            f"order_value_check: ${order_value:.2f} vs limit ${per_order_limit:.2f}"
        )

        if order_value > per_order_limit:
            return PolicyDecision(
                allowed=False,
                reason=(
                    f"Order value ${order_value:.2f} exceeds "
                    f"per-order limit ${per_order_limit:.2f}"
                ),
                constraints_checked=constraints_checked,
            )

        constraints_checked.append("order_value_check: PASSED")

        # ── All checks passed ─────────────────────────────────────────
        ticker_msg = (
            f"ticker '{ticker}' on whitelist"
            if allowed_tickers
            else f"ticker '{ticker}' allowed (no whitelist configured)"
        )
        return PolicyDecision(
            allowed=True,
            reason=(
                f"All policy checks passed: {ticker_msg}, "
                f"risk '{risk_level}' within threshold"
            ),
            constraints_checked=constraints_checked,
        )
