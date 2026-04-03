"""
test_allowed_trade.py — Tests for trade instructions that should be approved.

These tests verify that the OpenClaw agent correctly permits trades that
satisfy all policy constraints:
  - Ticker is on the authorised whitelist.
  - Total order value is within the per-trade limit.
  - Trade side (buy/sell) is well-formed.

A deterministic ``AllowAllPolicyEngine`` stub is used so these tests focus
solely on the agent's parsing and routing logic, independent of any
Person-2 enforcement implementation.

Run with:
    pytest backend/tests/test_allowed_trade.py -v
"""

from __future__ import annotations

import pytest

from backend.intent.intent_models import (
    ActionSide,
    EnforcementResult,
    Intent,
    IntentType,
)
from backend.intent.intent_parser import parse_intent
from backend.layer1_reasoning.agent import OpenClawAgent


# ─────────────────────────────────────────────
# Policy engine stubs
# ─────────────────────────────────────────────


class AllowAllPolicyEngine:
    """Approves every intent unconditionally."""

    async def enforce(self, intent: Intent) -> EnforcementResult:
        return EnforcementResult(allowed=True, reason="")


class SizeLimitPolicyEngine:
    """
    Approves trades whose total order value (quantity × price) is at or
    below *max_value*.  When no price is attached to the intent (market
    order), the trade is always allowed.
    """

    def __init__(self, max_value: float = 500.0) -> None:
        self.max_value = max_value

    async def enforce(self, intent: Intent) -> EnforcementResult:
        if intent.is_trade() and intent.price is not None:
            total = intent.quantity * intent.price
            if total > self.max_value:
                return EnforcementResult(
                    allowed=False,
                    reason=(
                        f"Trade value ${total:.2f} exceeds the "
                        f"${self.max_value:.2f} per-trade limit"
                    ),
                )
        return EnforcementResult(allowed=True, reason="")


# ─────────────────────────────────────────────
# Shared skill stub
# ─────────────────────────────────────────────


class EchoSkill:
    """Echoes the intent back as the skill result."""

    async def execute(self, intent: Intent) -> dict:
        return {"executed": True, "intent": intent.to_dict()}


def _make_agent(policy_engine=None) -> OpenClawAgent:
    pe = policy_engine or AllowAllPolicyEngine()
    sk = EchoSkill()
    return OpenClawAgent(
        policy_engine=pe,
        skills={
            "trading_skill": sk,
            "analysis_skill": sk,
            "market_data_skill": sk,
        },
    )


# ─────────────────────────────────────────────
# Test: Buy within limits
# ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_buy_within_limits():
    """
    A BUY order whose total value is safely below the $500 limit is ALLOWED.

    Scenario: Buy 1 share of MSFT at $430 → $430 < $500 → ALLOWED.
    """
    agent = _make_agent(policy_engine=SizeLimitPolicyEngine(max_value=500.0))
    response = await agent.run("buy 1 MSFT at 430", user_id="tester")

    assert response.status == "success", f"Expected success, got: {response.reason}"
    assert response.intent is not None
    assert response.intent.ticker == "MSFT"
    assert response.intent.side == ActionSide.BUY
    assert response.intent.quantity == 1.0
    assert response.intent.price == 430.0
    assert response.result is not None
    assert response.result["executed"] is True


@pytest.mark.asyncio
async def test_buy_exactly_at_limit():
    """
    A BUY order whose total value equals the limit exactly is ALLOWED.

    Scenario: Buy 1 share of AAPL at $500 → $500 == $500 → ALLOWED.
    """
    agent = _make_agent(policy_engine=SizeLimitPolicyEngine(max_value=500.0))
    response = await agent.run("buy 1 AAPL at 500", user_id="tester")

    assert response.status == "success", f"Expected success, got: {response.reason}"
    assert response.intent.ticker == "AAPL"
    assert response.intent.quantity == 1.0
    assert response.intent.price == 500.0


# ─────────────────────────────────────────────
# Test: Sell allowed stock
# ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_sell_allowed_stock():
    """
    A SELL order for a whitelisted ticker is ALLOWED.

    Scenario: Sell 5 shares of TSLA at $200 → within limit & valid ticker.
    """
    agent = _make_agent(policy_engine=SizeLimitPolicyEngine(max_value=2000.0))
    response = await agent.run("sell 5 TSLA at 200", user_id="tester")

    assert response.status == "success", f"Expected success, got: {response.reason}"
    assert response.intent is not None
    assert response.intent.side == ActionSide.SELL
    assert response.intent.ticker == "TSLA"
    assert response.intent.quantity == 5.0
    assert response.intent.price == 200.0


@pytest.mark.asyncio
async def test_sell_market_order_allowed():
    """
    A SELL market order (no limit price) is ALLOWED because there is no
    value to check against the trade-size constraint.
    """
    agent = _make_agent(policy_engine=SizeLimitPolicyEngine(max_value=500.0))
    response = await agent.run("sell 5 TSLA", user_id="tester")

    # Market sell has no price → size check is skipped → allowed
    assert response.status == "success", f"Expected success, got: {response.reason}"
    assert response.intent.side == ActionSide.SELL
    assert response.intent.price is None  # market order


# ─────────────────────────────────────────────
# Test: Multiple trades within policy
# ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_multiple_trades_within_policy():
    """
    Three sequential trades, each well within the $500 limit, all succeed.
    """
    agent = _make_agent(policy_engine=SizeLimitPolicyEngine(max_value=500.0))
    instructions = [
        ("buy 1 AAPL at 150", ActionSide.BUY, "AAPL"),
        ("sell 2 MSFT at 100", ActionSide.SELL, "MSFT"),
        ("buy 1 GOOGL at 130", ActionSide.BUY, "GOOGL"),
    ]

    for instruction, expected_side, expected_ticker in instructions:
        response = await agent.run(instruction, user_id="tester")
        assert response.status == "success", (
            f"Trade '{instruction}' unexpectedly {response.status}: {response.reason}"
        )
        assert response.intent.side == expected_side
        assert response.intent.ticker == expected_ticker


@pytest.mark.asyncio
async def test_mixed_ticker_trades_all_allowed():
    """
    Trades across several supported tickers are all allowed when within limits.
    """
    agent = _make_agent(policy_engine=AllowAllPolicyEngine())
    tickers = ["MSFT", "AAPL", "GOOGL", "AMZN", "NVDA"]

    for ticker in tickers:
        response = await agent.run(f"buy 1 {ticker} at 100", user_id="tester")
        assert response.status == "success", (
            f"Expected {ticker} to be allowed, got: {response.reason}"
        )
        assert response.intent.ticker == ticker
