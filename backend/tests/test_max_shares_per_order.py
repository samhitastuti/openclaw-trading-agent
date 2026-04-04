"""
test_max_shares_per_order.py — Tests for the max_shares_per_order policy constraint.

Validates that the PolicyEnforcer correctly blocks trade orders whose quantity
exceeds the configured ``max_shares_per_order`` limit (2,500 shares by default)
and allows orders at or below the limit.

Run with:
    pytest backend/tests/test_max_shares_per_order.py -v
"""

from __future__ import annotations

import pytest
from unittest.mock import patch

from backend.layer2_enforcement.enforcer import PolicyEnforcer


# ─────────────────────────────────────────────
# Helpers: minimal stubs for parsed_intent and classification
# ─────────────────────────────────────────────


class _FakeClassification:
    """Minimal classification stub that always returns 'safe' risk."""

    risk_level = "safe"
    reasoning = "no risk detected"


class _FakeParsedIntent:
    """Minimal parsed-intent stub for trade orders."""

    def __init__(self, ticker: str, quantity: float, price: float = 0.0) -> None:
        self.ticker = ticker
        self.quantity = quantity
        self.price = price
        self.raw_input = f"buy {quantity} {ticker}"

    def is_trade(self) -> bool:
        return True


_POLICY_WITH_LIMIT = {
    "trade_policy": {
        "max_shares_per_order": 2500,
        "per_order_value_limit": 10_000_000,  # effectively unlimited for these tests
        "ai_risk_threshold": 0.8,
    },
    "adversarial_policy": {"forbidden_keywords": []},
}


# ─────────────────────────────────────────────
# Tests: over-limit quantities are blocked
# ─────────────────────────────────────────────


def test_buy_one_million_shares_is_blocked():
    """
    'buy 1000000 aapl' must be BLOCKED: 1,000,000 > 2,500 max.
    """
    enforcer = PolicyEnforcer()
    classification = _FakeClassification()
    intent = _FakeParsedIntent(ticker="AAPL", quantity=1_000_000, price=0.0)

    trade_policy = _POLICY_WITH_LIMIT["trade_policy"]
    with patch(
        "backend.layer2_enforcement.enforcer.get_trade_policy",
        return_value=trade_policy,
    ):
        decision = enforcer.enforce(intent, classification)

    assert decision.allowed is False
    assert "Exceeds maximum shares per order" in decision.reason


def test_buy_2501_shares_is_blocked():
    """
    A quantity of 2,501 (one above the limit) must be BLOCKED.
    """
    enforcer = PolicyEnforcer()
    classification = _FakeClassification()
    intent = _FakeParsedIntent(ticker="MSFT", quantity=2501, price=0.0)

    trade_policy = _POLICY_WITH_LIMIT["trade_policy"]
    with patch(
        "backend.layer2_enforcement.enforcer.get_trade_policy",
        return_value=trade_policy,
    ):
        decision = enforcer.enforce(intent, classification)

    assert decision.allowed is False
    assert "Exceeds maximum shares per order" in decision.reason


# ─────────────────────────────────────────────
# Tests: at-or-below-limit quantities are allowed
# ─────────────────────────────────────────────


def test_buy_2000_shares_is_allowed():
    """
    'buy 2000 aapl' must be ALLOWED: 2,000 < 2,500 max.
    """
    enforcer = PolicyEnforcer()
    classification = _FakeClassification()
    intent = _FakeParsedIntent(ticker="AAPL", quantity=2000, price=0.0)

    trade_policy = _POLICY_WITH_LIMIT["trade_policy"]
    with patch(
        "backend.layer2_enforcement.enforcer.get_trade_policy",
        return_value=trade_policy,
    ):
        decision = enforcer.enforce(intent, classification)

    assert decision.allowed is True


def test_buy_2500_shares_exactly_at_limit_is_allowed():
    """
    'buy 2500 aapl' must be ALLOWED: 2,500 == 2,500 (not strictly over).
    """
    enforcer = PolicyEnforcer()
    classification = _FakeClassification()
    intent = _FakeParsedIntent(ticker="AAPL", quantity=2500, price=0.0)

    trade_policy = _POLICY_WITH_LIMIT["trade_policy"]
    with patch(
        "backend.layer2_enforcement.enforcer.get_trade_policy",
        return_value=trade_policy,
    ):
        decision = enforcer.enforce(intent, classification)

    assert decision.allowed is True


# ─────────────────────────────────────────────
# Tests: constraint is recorded in constraints_checked
# ─────────────────────────────────────────────


def test_max_shares_check_appears_in_constraints_when_blocked():
    """
    When a trade is blocked by the shares limit, 'max_shares_check' must appear
    in the list of constraints checked.
    """
    enforcer = PolicyEnforcer()
    classification = _FakeClassification()
    intent = _FakeParsedIntent(ticker="AAPL", quantity=5000, price=0.0)

    trade_policy = _POLICY_WITH_LIMIT["trade_policy"]
    with patch(
        "backend.layer2_enforcement.enforcer.get_trade_policy",
        return_value=trade_policy,
    ):
        decision = enforcer.enforce(intent, classification)

    assert decision.allowed is False
    assert any("max_shares_check" in c for c in decision.constraints_checked)


def test_max_shares_check_appears_in_constraints_when_allowed():
    """
    When a trade passes the shares limit, 'max_shares_check: PASSED' must appear
    in the list of constraints checked.
    """
    enforcer = PolicyEnforcer()
    classification = _FakeClassification()
    intent = _FakeParsedIntent(ticker="AAPL", quantity=100, price=0.0)

    trade_policy = _POLICY_WITH_LIMIT["trade_policy"]
    with patch(
        "backend.layer2_enforcement.enforcer.get_trade_policy",
        return_value=trade_policy,
    ):
        decision = enforcer.enforce(intent, classification)

    assert any(
        "max_shares_check: PASSED" in c for c in decision.constraints_checked
    )
