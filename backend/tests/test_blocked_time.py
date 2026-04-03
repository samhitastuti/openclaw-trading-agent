"""
test_blocked_time.py — Tests for trades attempted outside allowed market hours.

These tests verify that the enforcement layer correctly blocks trade requests
submitted outside the regular US equity market session (09:30–16:00 ET,
Monday–Friday) and that the block reason clearly describes the time
restriction.

A ``TradingHoursPolicyEngine`` stub is used so these tests are fully
self-contained and do not depend on a real clock.

Run with:
    pytest backend/tests/test_blocked_time.py -v
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

import pytest

from backend.intent.intent_models import (
    ActionSide,
    EnforcementResult,
    Intent,
    IntentType,
)
from backend.layer1_reasoning.agent import OpenClawAgent

# Eastern Time zone (handles DST automatically via zoneinfo)
_ET = ZoneInfo("America/New_York")

# Market session window (inclusive)
_MARKET_OPEN = (9, 30)   # 09:30 ET
_MARKET_CLOSE = (16, 0)  # 16:00 ET


# ─────────────────────────────────────────────
# Policy engine stub: trading hours enforcement
# ─────────────────────────────────────────────


class TradingHoursPolicyEngine:
    """
    Blocks any trade intent submitted outside the regular US equity market
    session (09:30–16:00 ET, Mon–Fri).

    The *now* parameter allows callers to inject a fixed datetime so that
    tests are not time-dependent.
    """

    def __init__(self, now: Optional[datetime] = None) -> None:
        # When *now* is provided it is used as the current time; otherwise the
        # real wall clock is consulted at enforce() time.
        self._fixed_now = now

    def _current_et_time(self) -> datetime:
        """Return the current (or injected) datetime in US/Eastern."""
        if self._fixed_now is not None:
            return self._fixed_now.astimezone(_ET)
        return datetime.now(_ET)

    def _is_market_open(self) -> bool:
        """Return True when the current ET time is within the market session."""
        et_now = self._current_et_time()
        # Weekday: Mon=0 … Fri=4, Sat=5, Sun=6
        if et_now.weekday() >= 5:
            return False
        open_minutes = _MARKET_OPEN[0] * 60 + _MARKET_OPEN[1]
        close_minutes = _MARKET_CLOSE[0] * 60 + _MARKET_CLOSE[1]
        current_minutes = et_now.hour * 60 + et_now.minute
        return open_minutes <= current_minutes < close_minutes

    async def enforce(self, intent: Intent) -> EnforcementResult:
        if intent.is_trade() and not self._is_market_open():
            et_now = self._current_et_time()
            return EnforcementResult(
                allowed=False,
                reason=(
                    f"Trade attempted outside market hours. "
                    f"Current ET time: {et_now.strftime('%H:%M')} "
                    f"({et_now.strftime('%A')}). "
                    f"Market is open Mon–Fri 09:30–16:00 ET."
                ),
            )
        return EnforcementResult(allowed=True, reason="")


# ─────────────────────────────────────────────
# Shared skill stub
# ─────────────────────────────────────────────


class EchoSkill:
    async def execute(self, intent: Intent) -> dict:
        return {"executed": True, "intent": intent.to_dict()}


def _make_agent(now_et: Optional[datetime] = None) -> OpenClawAgent:
    sk = EchoSkill()
    engine = TradingHoursPolicyEngine(now=now_et)
    return OpenClawAgent(
        policy_engine=engine,
        skills={
            "trading_skill": sk,
            "analysis_skill": sk,
            "market_data_skill": sk,
        },
    )


def _et(weekday: int, hour: int, minute: int) -> datetime:
    """
    Build a timezone-aware ET datetime for the nearest *weekday* (0=Mon, 6=Sun)
    at the given hour and minute.  The exact calendar date is unimportant for
    these tests; only the weekday/time components matter.
    """
    # Start from a known Monday (2025-01-06)
    base_monday = datetime(2025, 1, 6, tzinfo=_ET)
    day_offset = weekday  # 0=Mon → no offset, 5=Sat → +5
    return base_monday + timedelta(days=day_offset, hours=hour, minutes=minute)


# ─────────────────────────────────────────────
# Test: Attempt trade outside market hours (early morning)
# ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_trade_at_2am_is_blocked():
    """
    A trade submitted at 02:00 ET (before market open) must be BLOCKED.
    """
    agent = _make_agent(now_et=_et(weekday=0, hour=2, minute=0))  # Mon 02:00
    response = await agent.run("buy 1 AAPL at 150", user_id="tester")

    assert response.status == "blocked", (
        f"Expected 'blocked', got '{response.status}': {response.reason}"
    )


@pytest.mark.asyncio
async def test_trade_at_night_is_blocked():
    """
    A trade submitted at 20:00 ET (after market close) must be BLOCKED.
    """
    agent = _make_agent(now_et=_et(weekday=2, hour=20, minute=0))  # Wed 20:00
    response = await agent.run("buy 1 MSFT at 430", user_id="tester")

    assert response.status == "blocked"


@pytest.mark.asyncio
async def test_trade_at_market_open_is_allowed():
    """
    A trade submitted at exactly 09:30 ET (market open) must be ALLOWED.
    """
    agent = _make_agent(now_et=_et(weekday=0, hour=9, minute=30))  # Mon 09:30
    response = await agent.run("buy 1 AAPL at 150", user_id="tester")

    assert response.status == "success", (
        f"Expected 'success' at market open, got '{response.status}': {response.reason}"
    )


@pytest.mark.asyncio
async def test_trade_during_session_is_allowed():
    """
    A trade during the regular session (13:00 ET, Wednesday) is ALLOWED.
    """
    agent = _make_agent(now_et=_et(weekday=2, hour=13, minute=0))  # Wed 13:00
    response = await agent.run("sell 2 TSLA at 200", user_id="tester")

    assert response.status == "success", (
        f"Expected 'success', got '{response.status}': {response.reason}"
    )


# ─────────────────────────────────────────────
# Test: Block with a time-restriction error message
# ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_blocked_reason_mentions_market_hours():
    """
    The block reason must communicate to the operator that the trade was
    rejected due to time restrictions (not an asset or size issue).
    """
    agent = _make_agent(now_et=_et(weekday=0, hour=2, minute=0))  # Mon 02:00
    response = await agent.run("buy 1 AAPL at 150", user_id="tester")

    assert response.status == "blocked"
    assert response.reason is not None
    reason_lower = response.reason.lower()
    assert any(
        kw in reason_lower
        for kw in ("market", "hours", "time", "09:30", "16:00", "open")
    ), f"Block reason does not mention market hours: {response.reason!r}"


@pytest.mark.asyncio
async def test_blocked_reason_mentions_current_time():
    """
    The block reason should include the current ET time so the operator
    can diagnose why the trade was rejected.
    """
    agent = _make_agent(now_et=_et(weekday=0, hour=2, minute=0))  # Mon 02:00
    response = await agent.run("buy 1 AAPL at 150", user_id="tester")

    assert response.status == "blocked"
    assert response.reason is not None
    # The time "02:00" should appear in the reason
    assert "02:00" in response.reason, (
        f"Expected '02:00' in block reason, got: {response.reason!r}"
    )


# ─────────────────────────────────────────────
# Test: Weekend trades are blocked
# ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_saturday_trade_is_blocked():
    """
    The equity market is closed on weekends; a Saturday trade is BLOCKED.
    """
    agent = _make_agent(now_et=_et(weekday=5, hour=10, minute=0))  # Sat 10:00
    response = await agent.run("buy 1 GOOGL at 130", user_id="tester")

    assert response.status == "blocked", (
        f"Saturday trade should be blocked, got: {response.status}"
    )


@pytest.mark.asyncio
async def test_sunday_trade_is_blocked():
    """
    Sunday trades are also blocked.
    """
    agent = _make_agent(now_et=_et(weekday=6, hour=12, minute=0))  # Sun 12:00
    response = await agent.run("buy 1 MSFT at 300", user_id="tester")

    assert response.status == "blocked"


# ─────────────────────────────────────────────
# Test: Non-trade intents bypass the time check
# ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_analysis_outside_hours_is_allowed():
    """
    Analysis and data-fetch intents do not execute trades; they should be
    allowed even outside market hours.
    """
    agent = _make_agent(now_et=_et(weekday=0, hour=2, minute=0))  # Mon 02:00
    response = await agent.run("analyze MSFT", user_id="tester")

    # ANALYZE intent is not a trade → time restriction does not apply
    assert response.status == "success", (
        f"Analysis outside market hours should succeed, got: {response.status}"
    )
