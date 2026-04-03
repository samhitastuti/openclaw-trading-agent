"""
test_blocked_trade_size.py — Tests for trade attempts that exceed size limits.

Covers:
  - A trade whose total order value (qty × price) exceeds the maximum is blocked
  - The block reason mentions the size violation
  - Total order value is calculated correctly (qty × price)
  - Trades within the size limit are approved by the same engine
  - Market orders (no price) are not incorrectly size-blocked
"""

from __future__ import annotations

import pytest

from backend.intent.intent_models import (
    EnforcementResult,
    Intent,
    IntentType,
)
from backend.layer1_reasoning.agent import OpenClawAgent


# ─────────────────────────────────────────────
# Policy engine
# ─────────────────────────────────────────────


class TradeSizeLimitEngine:
    """
    Policy engine that enforces a maximum total order value.

    The check only applies when a limit price is specified (qty × price).
    Market orders without a price are allowed through so the caller must
    rely on the broker's own risk controls for those.
    """

    def __init__(self, max_order_value: float = 500.0):
        self.max_order_value = max_order_value

    async def enforce(self, intent: Intent) -> EnforcementResult:
        if intent.is_trade() and intent.price is not None:
            total_value = intent.quantity * intent.price
            if total_value > self.max_order_value:
                return EnforcementResult(
                    allowed=False,
                    reason=(
                        f"Order value ${total_value:,.2f} exceeds the maximum "
                        f"allowed trade size of ${self.max_order_value:,.2f}."
                    ),
                    details={
                        "order_value": total_value,
                        "max_order_value": self.max_order_value,
                        "qty": intent.quantity,
                        "price": intent.price,
                    },
                )
        return EnforcementResult(allowed=True, reason="")


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────


class EchoSkill:
    async def execute(self, intent: Intent) -> dict:
        return {
            "status": "executed",
            "ticker": intent.ticker,
            "quantity": intent.quantity,
            "price": intent.price,
        }


def _make_agent(max_order_value: float = 500.0) -> OpenClawAgent:
    return OpenClawAgent(
        policy_engine=TradeSizeLimitEngine(max_order_value=max_order_value),
        skills={
            "trading_skill": EchoSkill(),
            "analysis_skill": EchoSkill(),
            "market_data_skill": EchoSkill(),
        },
    )


# ─────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_buy_exceeding_size_limit_is_blocked():
    """
    Buying 10 shares at $200 = $2,000 — well above the $500 limit.
    The trade must be BLOCKED.
    """
    agent = _make_agent(max_order_value=500.0)
    response = await agent.run("buy 10 AAPL at 200", user_id="trader_30")

    assert response.status == "blocked"
    assert response.intent is not None
    assert response.intent.quantity == 10.0
    assert response.intent.price == 200.0


@pytest.mark.asyncio
async def test_block_reason_mentions_size_exceeded():
    """
    The block reason must communicate that the order value exceeded the
    limit so the user understands how to correct it.
    """
    agent = _make_agent(max_order_value=500.0)
    response = await agent.run("buy 10 AAPL at 200", user_id="trader_31")

    assert response.status == "blocked"
    assert response.reason is not None
    # Reason should reference the size/value violation.
    lower_reason = response.reason.lower()
    assert any(
        keyword in lower_reason
        for keyword in ("size", "value", "exceed", "maximum", "limit")
    ), f"Expected size-related block reason, got: {response.reason}"


@pytest.mark.asyncio
async def test_order_value_calculation_is_correct():
    """
    5 shares at $150 = $750 → above $500 limit → blocked.
    Confirms that qty × price is the value used for the check.
    """
    agent = _make_agent(max_order_value=500.0)
    response = await agent.run("buy 5 MSFT at 150", user_id="trader_32")

    assert response.status == "blocked"
    # 5 × 150 = 750 > 500


@pytest.mark.asyncio
async def test_trade_within_size_limit_is_allowed():
    """
    1 share at $430 = $430 — under the $500 limit — must be APPROVED.
    """
    agent = _make_agent(max_order_value=500.0)
    response = await agent.run("buy 1 MSFT at 430", user_id="trader_33")

    assert response.status == "success"
    assert response.result is not None


@pytest.mark.asyncio
async def test_trade_exactly_at_limit_is_allowed():
    """
    An order whose value equals the limit exactly should be allowed
    (boundary condition: ≤ limit passes, > limit is blocked).
    """
    agent = _make_agent(max_order_value=500.0)
    # 2 shares at $250 = $500.00 → exactly at the limit
    response = await agent.run("buy 2 MSFT at 250", user_id="trader_34")

    assert response.status == "success"


@pytest.mark.asyncio
async def test_market_order_not_blocked_by_size_engine():
    """
    A market order (no price specified) cannot have its value calculated
    and must not be blocked by the size engine.
    """
    agent = _make_agent(max_order_value=500.0)
    # No price → market order; intent.price will be None
    response = await agent.run("buy 10 AAPL", user_id="trader_35")

    # The size engine skips market orders; the trade should reach the skill.
    assert response.status == "success"
