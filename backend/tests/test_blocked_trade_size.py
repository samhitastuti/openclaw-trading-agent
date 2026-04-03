"""
test_blocked_trade_size.py — Tests for trades that exceed the size limit.

These tests verify that the enforcement layer correctly rejects trade
requests whose total order value (quantity × price) exceeds the configured
per-trade maximum and that the block reason clearly communicates the size
violation.

A ``TradeSizePolicyEngine`` stub is used so these tests are fully
self-contained and independent of any Person-2 enforcement implementation.

Run with:
    pytest backend/tests/test_blocked_trade_size.py -v
"""

from __future__ import annotations

import pytest

from backend.intent.intent_models import (
    ActionSide,
    EnforcementResult,
    Intent,
    IntentType,
)
from backend.layer1_reasoning.agent import OpenClawAgent


# ─────────────────────────────────────────────
# Policy engine stub: per-trade size limit
# ─────────────────────────────────────────────


class TradeSizePolicyEngine:
    """
    Blocks any trade whose total order value (quantity × limit price) exceeds
    *max_trade_value*.

    Market orders (no limit price) cannot have their value calculated at
    submission time, so they are always allowed by this engine.
    """

    def __init__(self, max_trade_value: float = 500.0) -> None:
        self.max_trade_value = max_trade_value

    def _calculate_order_value(self, intent: Intent) -> float | None:
        """
        Return the total order value for a limit order, or *None* for a
        market order (price not known at submission time).
        """
        if intent.price is None:
            return None
        return intent.quantity * intent.price

    async def enforce(self, intent: Intent) -> EnforcementResult:
        if not intent.is_trade():
            return EnforcementResult(allowed=True, reason="")

        order_value = self._calculate_order_value(intent)

        if order_value is not None and order_value > self.max_trade_value:
            return EnforcementResult(
                allowed=False,
                reason=(
                    f"Order value ${order_value:.2f} exceeds the "
                    f"${self.max_trade_value:.2f} per-trade limit "
                    f"({intent.quantity:.0f} × ${intent.price:.2f})"
                ),
                details={
                    "order_value": order_value,
                    "max_trade_value": self.max_trade_value,
                    "quantity": intent.quantity,
                    "price": intent.price,
                },
            )

        return EnforcementResult(allowed=True, reason="")


# ─────────────────────────────────────────────
# Shared skill stub
# ─────────────────────────────────────────────


class EchoSkill:
    async def execute(self, intent: Intent) -> dict:
        return {"executed": True, "intent": intent.to_dict()}


def _make_agent(max_trade_value: float = 500.0) -> OpenClawAgent:
    sk = EchoSkill()
    engine = TradeSizePolicyEngine(max_trade_value=max_trade_value)
    return OpenClawAgent(
        policy_engine=engine,
        skills={
            "trading_skill": sk,
            "analysis_skill": sk,
            "market_data_skill": sk,
        },
    )


# ─────────────────────────────────────────────
# Test: Attempt to buy more shares than the limit allows
# ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_buy_too_many_shares_is_blocked():
    """
    Buying 10 shares of AAPL at $200 each ($2,000 total) exceeds the $500
    per-trade limit and must result in a BLOCKED response.
    """
    agent = _make_agent(max_trade_value=500.0)
    response = await agent.run("buy 10 AAPL at 200", user_id="tester")

    assert response.status == "blocked", (
        f"Expected 'blocked', got '{response.status}': {response.reason}"
    )
    assert response.intent is not None
    assert response.intent.ticker == "AAPL"
    assert response.intent.quantity == 10.0
    assert response.intent.price == 200.0


@pytest.mark.asyncio
async def test_sell_exceeding_limit_is_blocked():
    """
    A SELL order that exceeds the size limit is also blocked.

    Selling 5 shares of MSFT at $200 = $1,000 > $500 limit → BLOCKED.
    """
    agent = _make_agent(max_trade_value=500.0)
    response = await agent.run("sell 5 MSFT at 200", user_id="tester")

    assert response.status == "blocked"
    assert response.intent.side == ActionSide.SELL


@pytest.mark.asyncio
async def test_order_just_above_limit_is_blocked():
    """
    An order value of $501 (just over the $500 limit) must be blocked.
    """
    agent = _make_agent(max_trade_value=500.0)
    # 1 × $501 = $501 > $500
    response = await agent.run("buy 1 AAPL at 501", user_id="tester")

    assert response.status == "blocked", (
        "An order of $501 should be blocked by the $500 limit"
    )


@pytest.mark.asyncio
async def test_order_at_limit_is_allowed():
    """
    An order value exactly equal to the limit is ALLOWED (not strictly over).
    """
    agent = _make_agent(max_trade_value=500.0)
    # 1 × $500 = $500 == $500 → allowed
    response = await agent.run("buy 1 AAPL at 500", user_id="tester")

    assert response.status == "success", (
        f"An order of $500 should be allowed at the $500 limit, got: {response.reason}"
    )


# ─────────────────────────────────────────────
# Test: Blocks with a size-exceeded error message
# ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_blocked_reason_mentions_order_value():
    """
    The block reason must state the computed order value so the user knows
    exactly how far over the limit their order was.
    """
    agent = _make_agent(max_trade_value=500.0)
    response = await agent.run("buy 10 AAPL at 200", user_id="tester")

    assert response.status == "blocked"
    assert response.reason is not None
    # The computed value $2000 should appear in the reason
    assert "2000" in response.reason or "2,000" in response.reason, (
        f"Block reason should mention $2000 order value, got: {response.reason!r}"
    )


@pytest.mark.asyncio
async def test_blocked_reason_mentions_limit():
    """
    The block reason must reference the configured limit so the user
    understands the policy threshold.
    """
    agent = _make_agent(max_trade_value=500.0)
    response = await agent.run("buy 10 AAPL at 200", user_id="tester")

    assert response.status == "blocked"
    assert response.reason is not None
    assert "500" in response.reason, (
        f"Block reason should mention $500 limit, got: {response.reason!r}"
    )


@pytest.mark.asyncio
async def test_blocked_reason_mentions_size_exceeded():
    """
    The block reason must contain wording that indicates a size / value
    breach (e.g. "exceeds", "limit", "value").
    """
    agent = _make_agent(max_trade_value=500.0)
    response = await agent.run("buy 10 AAPL at 200", user_id="tester")

    assert response.status == "blocked"
    reason_lower = response.reason.lower()
    assert any(
        kw in reason_lower
        for kw in ("exceed", "limit", "value", "size", "max")
    ), f"Block reason lacks size-exceeded language: {response.reason!r}"


# ─────────────────────────────────────────────
# Test: Total order value is calculated correctly
# ─────────────────────────────────────────────


def test_calculate_order_value_correctly():
    """
    Unit test for ``TradeSizePolicyEngine._calculate_order_value``.

    Verifies that the engine multiplies quantity × price precisely and does
    not introduce floating-point rounding errors in simple cases.
    """
    engine = TradeSizePolicyEngine(max_trade_value=500.0)

    # Build minimal intent objects directly (not via agent/parser)
    intent_10x200 = Intent(
        type=IntentType.EXECUTE_TRADE,
        ticker="AAPL",
        quantity=10.0,
        side=ActionSide.BUY,
        price=200.0,
    )
    assert engine._calculate_order_value(intent_10x200) == pytest.approx(2000.0)

    intent_2x150 = Intent(
        type=IntentType.EXECUTE_TRADE,
        ticker="MSFT",
        quantity=2.0,
        side=ActionSide.BUY,
        price=150.0,
    )
    assert engine._calculate_order_value(intent_2x150) == pytest.approx(300.0)

    # Market order (no price) → None
    intent_market = Intent(
        type=IntentType.EXECUTE_TRADE,
        ticker="GOOGL",
        quantity=5.0,
        side=ActionSide.BUY,
        price=None,
    )
    assert engine._calculate_order_value(intent_market) is None


def test_calculate_fractional_shares_correctly():
    """
    Fractional share quantities should be calculated accurately.
    """
    engine = TradeSizePolicyEngine(max_trade_value=500.0)

    intent = Intent(
        type=IntentType.EXECUTE_TRADE,
        ticker="AAPL",
        quantity=2.5,
        side=ActionSide.BUY,
        price=100.0,
    )
    assert engine._calculate_order_value(intent) == pytest.approx(250.0)


@pytest.mark.asyncio
async def test_market_order_not_blocked_by_size_limit():
    """
    Market orders (no limit price) cannot have their value pre-calculated,
    so they must NOT be blocked by the size-limit check.
    """
    agent = _make_agent(max_trade_value=1.0)  # Extremely tight limit
    # No price → market order → engine cannot compute value → must allow
    response = await agent.run("buy 1 AAPL", user_id="tester")

    assert response.status == "success", (
        "Market orders should not be blocked by the size-limit engine "
        f"(got: {response.status}, reason: {response.reason})"
    )
