"""
test_blocked_asset.py — Tests for trades on restricted (non-whitelisted) tickers.

These tests verify that the enforcement layer correctly blocks trade requests
for tickers that are not on the authorised whitelist, and that blocked
decisions include an informative reason string.

An ``AuthorisedTickerPolicyEngine`` stub implements the whitelist check so
these tests are independent of any Person-2 enforcement implementation.

Run with:
    pytest backend/tests/test_blocked_asset.py -v
"""

from __future__ import annotations

from typing import FrozenSet

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
# Policy engine stub: ticker whitelist
# ─────────────────────────────────────────────

_DEFAULT_WHITELIST: FrozenSet[str] = frozenset(
    {"MSFT", "AAPL", "GOOGL", "AMZN", "TSLA", "NVDA", "AMD", "SPY", "QQQ"}
)


class AuthorisedTickerPolicyEngine:
    """
    Blocks any trade intent whose ticker is not in *allowed_tickers*.
    Non-trade intents (ANALYZE, FETCH_DATA) are always permitted.
    """

    def __init__(self, allowed_tickers: FrozenSet[str] = _DEFAULT_WHITELIST) -> None:
        self.allowed_tickers = allowed_tickers
        # Internal audit list of blocked decisions (for log-inspection tests)
        self._blocked: list[dict] = []

    async def enforce(self, intent: Intent) -> EnforcementResult:
        if intent.is_trade() and intent.ticker not in self.allowed_tickers:
            reason = (
                f"Ticker '{intent.ticker}' is not on the authorised whitelist. "
                f"Allowed tickers: {sorted(self.allowed_tickers)}"
            )
            self._blocked.append(
                {
                    "intent_id": intent.intent_id,
                    "ticker": intent.ticker,
                    "reason": reason,
                }
            )
            return EnforcementResult(allowed=False, reason=reason)
        return EnforcementResult(allowed=True, reason="")

    def get_blocked_decisions(self) -> list[dict]:
        """Return a copy of all blocked decision records."""
        return list(self._blocked)


# ─────────────────────────────────────────────
# Shared skill stub
# ─────────────────────────────────────────────


class EchoSkill:
    async def execute(self, intent: Intent) -> dict:
        return {"executed": True, "intent": intent.to_dict()}


def _make_agent(policy_engine=None) -> OpenClawAgent:
    sk = EchoSkill()
    return OpenClawAgent(
        policy_engine=policy_engine or AuthorisedTickerPolicyEngine(),
        skills={
            "trading_skill": sk,
            "analysis_skill": sk,
            "market_data_skill": sk,
        },
    )


# ─────────────────────────────────────────────
# Test: Attempt to buy a restricted ticker
# ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_buy_restricted_ticker_is_blocked():
    """
    Attempting to BUY a ticker not in the whitelist results in a BLOCKED
    response from the agent.

    Note: The intent parser only accepts tickers in ``SUPPORTED_TICKERS``.
    We therefore use a whitelist that is a strict subset of the parser's
    supported set – INTC is supported by the parser but excluded from the
    policy whitelist to simulate a restricted asset.
    """
    narrow_whitelist = frozenset({"MSFT", "AAPL", "GOOGL", "AMZN"})
    engine = AuthorisedTickerPolicyEngine(allowed_tickers=narrow_whitelist)
    agent = _make_agent(policy_engine=engine)

    # INTC is parseable (in SUPPORTED_TICKERS) but not whitelisted by policy
    response = await agent.run("buy 5 INTC at 30", user_id="tester")

    assert response.status == "blocked", (
        f"Expected 'blocked', got '{response.status}'"
    )
    assert response.intent is not None
    assert response.intent.ticker == "INTC"


@pytest.mark.asyncio
async def test_sell_restricted_ticker_is_blocked():
    """
    SELL orders on a non-whitelisted ticker are also blocked.
    """
    narrow_whitelist = frozenset({"MSFT", "AAPL"})
    engine = AuthorisedTickerPolicyEngine(allowed_tickers=narrow_whitelist)
    agent = _make_agent(policy_engine=engine)

    response = await agent.run("sell 3 NVDA at 500", user_id="tester")

    assert response.status == "blocked"
    assert response.intent.ticker == "NVDA"


# ─────────────────────────────────────────────
# Test: Blocks with a proper error message
# ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_blocked_reason_mentions_ticker():
    """
    The block reason returned to the user must reference the offending ticker
    so the operator knows exactly which asset triggered the policy.
    """
    narrow_whitelist = frozenset({"MSFT", "AAPL"})
    engine = AuthorisedTickerPolicyEngine(allowed_tickers=narrow_whitelist)
    agent = _make_agent(policy_engine=engine)

    response = await agent.run("buy 10 INTC at 30", user_id="tester")

    assert response.status == "blocked"
    assert response.reason is not None
    assert "INTC" in response.reason, (
        f"Expected 'INTC' in reason, got: {response.reason!r}"
    )


@pytest.mark.asyncio
async def test_blocked_reason_mentions_whitelist():
    """
    The block reason must indicate that the ticker is not on the whitelist,
    so the user understands why the trade was refused.
    """
    narrow_whitelist = frozenset({"MSFT"})
    engine = AuthorisedTickerPolicyEngine(allowed_tickers=narrow_whitelist)
    agent = _make_agent(policy_engine=engine)

    response = await agent.run("buy 5 AAPL at 150", user_id="tester")

    assert response.status == "blocked"
    # The reason should reference the whitelist or authorisation
    reason_lower = response.reason.lower()
    assert any(
        keyword in reason_lower for keyword in ("whitelist", "authoris", "authoriz", "allowed")
    ), f"Block reason does not mention whitelist: {response.reason!r}"


# ─────────────────────────────────────────────
# Test: Blocked decision is logged
# ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_blocked_decision_is_logged():
    """
    After a blocked trade the policy engine's internal audit log should
    contain exactly one entry with the correct ticker and intent ID.
    """
    narrow_whitelist = frozenset({"MSFT"})
    engine = AuthorisedTickerPolicyEngine(allowed_tickers=narrow_whitelist)
    agent = _make_agent(policy_engine=engine)

    response = await agent.run("buy 5 AAPL at 150", user_id="audit_tester")

    assert response.status == "blocked"

    blocked = engine.get_blocked_decisions()
    assert len(blocked) == 1, f"Expected 1 blocked entry, got {len(blocked)}"

    entry = blocked[0]
    assert entry["ticker"] == "AAPL"
    assert entry["intent_id"] == response.intent.intent_id


@pytest.mark.asyncio
async def test_multiple_blocked_decisions_are_all_logged():
    """
    Each blocked trade generates its own audit-log entry; the count grows
    with every rejected request.
    """
    narrow_whitelist = frozenset({"MSFT"})
    engine = AuthorisedTickerPolicyEngine(allowed_tickers=narrow_whitelist)
    agent = _make_agent(policy_engine=engine)

    restricted_instructions = [
        "buy 5 AAPL at 150",
        "sell 3 NVDA at 500",
        "buy 1 INTC at 30",
    ]

    for instruction in restricted_instructions:
        response = await agent.run(instruction, user_id="audit_tester")
        assert response.status == "blocked"

    blocked = engine.get_blocked_decisions()
    assert len(blocked) == len(restricted_instructions), (
        f"Expected {len(restricted_instructions)} blocked entries, got {len(blocked)}"
    )


@pytest.mark.asyncio
async def test_allowed_trades_do_not_appear_in_blocked_log():
    """
    Approved trades must NOT be recorded in the blocked-decisions log.
    """
    engine = AuthorisedTickerPolicyEngine(allowed_tickers=frozenset({"MSFT", "AAPL"}))
    agent = _make_agent(policy_engine=engine)

    # Allowed trade
    response = await agent.run("buy 1 MSFT at 430", user_id="tester")
    assert response.status == "success"

    # Blocked trade
    response = await agent.run("buy 5 INTC at 30", user_id="tester")
    assert response.status == "blocked"

    blocked = engine.get_blocked_decisions()
    assert len(blocked) == 1
    assert blocked[0]["ticker"] == "INTC"
