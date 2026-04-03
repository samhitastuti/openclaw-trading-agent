"""
test_blocked_asset.py — Tests for trade attempts on restricted tickers.

Covers:
  - Attempt to buy a ticker not in the supported/whitelisted set
  - Confirms the response carries a meaningful error message
  - Explicit policy-level blocking of a known ticker via BlockedTickerEngine
  - Blocked response is serialisable (audit-log ready)
"""

from __future__ import annotations

import pytest

from backend.intent.intent_models import (
    EnforcementResult,
    Intent,
    IntentType,
    ActionSide,
)
from backend.layer1_reasoning.agent import OpenClawAgent


# ─────────────────────────────────────────────
# Mock collaborators
# ─────────────────────────────────────────────


class AllowAllPolicyEngine:
    """Stub that approves every intent."""

    async def enforce(self, intent: Intent) -> EnforcementResult:
        return EnforcementResult(allowed=True, reason="")


class BlockedTickerEngine:
    """
    Policy engine that blocks trading in a pre-defined set of tickers.

    Any intent whose ticker appears in *blocked_tickers* receives a
    BLOCKED enforcement result with a descriptive reason string.
    """

    def __init__(self, blocked_tickers: set[str]):
        self._blocked = {t.upper() for t in blocked_tickers}

    async def enforce(self, intent: Intent) -> EnforcementResult:
        if intent.ticker in self._blocked:
            return EnforcementResult(
                allowed=False,
                reason=(
                    f"Ticker '{intent.ticker}' is restricted by policy. "
                    "Only whitelisted assets may be traded."
                ),
            )
        return EnforcementResult(allowed=True, reason="")


class EchoSkill:
    async def execute(self, intent: Intent) -> dict:
        return {"status": "executed", "ticker": intent.ticker}


def _make_agent(policy_engine=None) -> OpenClawAgent:
    return OpenClawAgent(
        policy_engine=policy_engine or AllowAllPolicyEngine(),
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
async def test_buy_unsupported_ticker_is_rejected():
    """
    Tickers outside SUPPORTED_TICKERS (constants.py) are rejected at parse
    time — the agent returns an error before enforcement even runs.
    """
    agent = _make_agent()
    # "XYZ" is not in SUPPORTED_TICKERS; the intent parser returns None.
    response = await agent.run("buy 1 XYZ", user_id="trader_10")

    assert response.status == "error"
    assert response.reason is not None
    assert len(response.reason) > 0


@pytest.mark.asyncio
async def test_buy_restricted_ticker_blocked_by_policy():
    """
    Even a parseable/supported ticker is BLOCKED when the policy engine
    has it on its restricted list.
    """
    # Restrict TSLA explicitly via the policy engine.
    engine = BlockedTickerEngine(blocked_tickers={"TSLA"})
    agent = _make_agent(policy_engine=engine)

    response = await agent.run("buy 5 TSLA", user_id="trader_11")

    assert response.status == "blocked"
    assert response.intent is not None
    assert response.intent.ticker == "TSLA"


@pytest.mark.asyncio
async def test_blocked_asset_error_message_is_descriptive():
    """
    The block reason returned for a restricted asset must be non-empty and
    mention the ticker so a compliance officer can identify the violation.
    """
    engine = BlockedTickerEngine(blocked_tickers={"NVDA"})
    agent = _make_agent(policy_engine=engine)

    response = await agent.run("buy 1 NVDA at 900", user_id="trader_12")

    assert response.status == "blocked"
    assert response.reason is not None
    # The reason must reference the blocked ticker.
    assert "NVDA" in response.reason


@pytest.mark.asyncio
async def test_blocked_asset_response_is_serialisable():
    """
    A blocked response can be serialised to a dict so it can be written to
    an audit log without raising exceptions.
    """
    engine = BlockedTickerEngine(blocked_tickers={"AMD"})
    agent = _make_agent(policy_engine=engine)

    response = await agent.run("buy 3 AMD", user_id="trader_13")

    assert response.status == "blocked"
    d = response.to_dict()
    assert d["status"] == "blocked"
    assert d["intent"] is not None
    assert d["intent"]["ticker"] == "AMD"
    assert d["reason"] is not None


@pytest.mark.asyncio
async def test_unrestricted_ticker_is_allowed_after_block():
    """
    Blocking one ticker must not affect other tickers — MSFT should still
    be allowed when only TSLA is restricted.
    """
    engine = BlockedTickerEngine(blocked_tickers={"TSLA"})
    agent = _make_agent(policy_engine=engine)

    response = await agent.run("buy 1 MSFT at 430", user_id="trader_14")

    assert response.status == "success"
    assert response.intent.ticker == "MSFT"
