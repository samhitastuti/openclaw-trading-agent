"""
test_blocked_time.py — Tests for trade attempts outside allowed market hours.

Covers:
  - A time-restricted policy engine blocks trades during off-hours
  - A time-restricted policy engine allows trades during market hours
  - The block reason references the time restriction
  - Non-trade intents (analysis, data fetch) are not time-gated

Market hours are modelled as a configurable window so tests remain
deterministic regardless of when they run.
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
# Policy engines
# ─────────────────────────────────────────────


class OutsideMarketHoursEngine:
    """
    Policy engine that always considers the current time to be outside
    market hours (09:00-16:00 ET).

    Used to simulate off-hours enforcement without depending on the
    wall-clock time of the test runner.
    """

    MARKET_OPEN_HOUR: int = 9
    MARKET_CLOSE_HOUR: int = 16

    async def enforce(self, intent: Intent) -> EnforcementResult:
        if intent.is_trade():
            return EnforcementResult(
                allowed=False,
                reason=(
                    f"Trading not allowed outside market hours "
                    f"({self.MARKET_OPEN_HOUR}:00-{self.MARKET_CLOSE_HOUR}:00 ET). "
                    "Please retry during regular trading hours."
                ),
            )
        return EnforcementResult(allowed=True, reason="")


class InsideMarketHoursEngine:
    """
    Policy engine that always considers the current time to be within
    market hours — used to confirm the non-blocking path.
    """

    async def enforce(self, intent: Intent) -> EnforcementResult:
        return EnforcementResult(allowed=True, reason="")


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────


class EchoSkill:
    async def execute(self, intent: Intent) -> dict:
        return {"status": "executed", "ticker": intent.ticker}


def _make_agent(policy_engine) -> OpenClawAgent:
    return OpenClawAgent(
        policy_engine=policy_engine,
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
async def test_trade_blocked_outside_market_hours():
    """
    When the policy engine reports off-hours, a BUY order must be blocked
    regardless of ticker or size.
    """
    agent = _make_agent(OutsideMarketHoursEngine())
    response = await agent.run("buy 1 MSFT at 430", user_id="trader_20")

    assert response.status == "blocked"
    assert response.intent is not None
    assert response.intent.type == IntentType.EXECUTE_TRADE


@pytest.mark.asyncio
async def test_trade_blocked_includes_time_restriction_reason():
    """
    The block reason for an off-hours trade must describe the time
    restriction so the user knows when to retry.
    """
    agent = _make_agent(OutsideMarketHoursEngine())
    response = await agent.run("sell 3 AAPL", user_id="trader_21")

    assert response.status == "blocked"
    assert response.reason is not None
    # Reason should mention market hours or time restriction
    lower_reason = response.reason.lower()
    assert any(
        keyword in lower_reason
        for keyword in ("market hours", "trading hours", "hours", "time")
    ), f"Expected time-related reason, got: {response.reason}"


@pytest.mark.asyncio
async def test_trade_allowed_inside_market_hours():
    """
    When the policy engine considers us inside market hours, the same
    BUY order that was blocked above must succeed.
    """
    agent = _make_agent(InsideMarketHoursEngine())
    response = await agent.run("buy 1 MSFT at 430", user_id="trader_22")

    assert response.status == "success"
    assert response.intent is not None
    assert response.intent.ticker == "MSFT"


@pytest.mark.asyncio
async def test_sell_also_blocked_outside_hours():
    """
    Time restrictions apply to SELL orders as well as BUY orders.
    """
    agent = _make_agent(OutsideMarketHoursEngine())
    response = await agent.run("sell 5 GOOGL", user_id="trader_23")

    assert response.status == "blocked"


@pytest.mark.asyncio
async def test_analysis_not_blocked_by_time_restriction():
    """
    The OutsideMarketHoursEngine only gates trade intents; analysis
    requests should still be allowed at any hour.
    """
    agent = _make_agent(OutsideMarketHoursEngine())
    response = await agent.run("analyze MSFT", user_id="trader_24")

    # Analysis is not a trade — must not be blocked by the time engine.
    assert response.status == "success"
    assert response.intent.type == IntentType.ANALYZE
