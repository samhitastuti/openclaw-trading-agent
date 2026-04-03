"""
test_allowed_trade.py — Tests for trade intents that should be approved.

Covers:
  - Buy within size and ticker limits
  - Sell an allowed stock
  - Multiple sequential trades that all remain within policy

These tests use the OpenClawAgent with lightweight mock collaborators so
no real broker connection or policy-engine implementation is required.
"""

from __future__ import annotations

import pytest

from backend.intent.intent_models import (
    ActionSide,
    AgentResponse,
    EnforcementResult,
    Intent,
    IntentType,
)
from backend.layer1_reasoning.agent import OpenClawAgent


# ─────────────────────────────────────────────
# Mock collaborators
# ─────────────────────────────────────────────


class AllowAllPolicyEngine:
    """Stub policy engine that approves every intent."""

    async def enforce(self, intent: Intent) -> EnforcementResult:
        return EnforcementResult(allowed=True, reason="")


class EchoSkill:
    """Stub skill that returns the intent details as its result."""

    async def execute(self, intent: Intent) -> dict:
        return {
            "status": "executed",
            "ticker": intent.ticker,
            "quantity": intent.quantity,
            "side": intent.side.value,
        }


def _make_agent() -> OpenClawAgent:
    return OpenClawAgent(
        policy_engine=AllowAllPolicyEngine(),
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
async def test_buy_within_limits():
    """Buy 1 share of MSFT at $430 — within the $500 max trade size."""
    agent = _make_agent()
    response = await agent.run("buy 1 MSFT at 430", user_id="trader_01")

    assert response.status == "success", f"Expected success, got: {response.reason}"
    assert response.intent is not None
    assert response.intent.type == IntentType.EXECUTE_TRADE
    assert response.intent.side == ActionSide.BUY
    assert response.intent.ticker == "MSFT"
    assert response.intent.quantity == 1.0
    assert response.intent.price == 430.0
    assert response.result is not None
    assert response.result["status"] == "executed"


@pytest.mark.asyncio
async def test_sell_allowed_stock():
    """Sell 5 shares of AAPL — a whitelisted ticker; should be approved."""
    agent = _make_agent()
    response = await agent.run("sell 5 AAPL", user_id="trader_02")

    assert response.status == "success", f"Expected success, got: {response.reason}"
    assert response.intent is not None
    assert response.intent.side == ActionSide.SELL
    assert response.intent.ticker == "AAPL"
    assert response.intent.quantity == 5.0
    assert response.result is not None


@pytest.mark.asyncio
async def test_multiple_trades_within_policy():
    """Three consecutive trades within policy limits all succeed."""
    agent = _make_agent()
    instructions = [
        ("buy 1 MSFT at 430", "MSFT", ActionSide.BUY),
        ("sell 2 AAPL", "AAPL", ActionSide.SELL),
        ("buy 1 GOOGL at 180", "GOOGL", ActionSide.BUY),
    ]

    for instruction, expected_ticker, expected_side in instructions:
        response = await agent.run(instruction, user_id="trader_03")
        assert response.status == "success", (
            f"Trade '{instruction}' expected success, got: {response.reason}"
        )
        assert response.intent.ticker == expected_ticker
        assert response.intent.side == expected_side


@pytest.mark.asyncio
async def test_buy_returns_structured_result():
    """Successful buy returns a structured result dict with required keys."""
    agent = _make_agent()
    response = await agent.run("buy 2 AMZN at 185", user_id="trader_04")

    assert response.status == "success"
    result = response.result
    assert isinstance(result, dict)
    assert "status" in result
    assert result["ticker"] == "AMZN"
    assert result["quantity"] == 2.0
    assert result["side"] == "BUY"


@pytest.mark.asyncio
async def test_trade_response_serialisable():
    """AgentResponse.to_dict() produces a JSON-serialisable dict on success."""
    agent = _make_agent()
    response = await agent.run("buy 1 NVDA at 900", user_id="trader_05")

    assert response.status == "success"
    d = response.to_dict()
    assert d["status"] == "success"
    assert "intent" in d
    assert d["intent"]["ticker"] == "NVDA"
    assert "result" in d
