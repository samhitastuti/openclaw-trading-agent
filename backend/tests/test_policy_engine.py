"""
test_policy_engine.py — Tests for combined policy engine enforcement.

These tests verify a composite ``CompositePolicyEngine`` that applies
multiple constraints simultaneously:
  1. Authorised ticker whitelist.
  2. Per-trade size limit.
  3. Trading hours restriction.

The suite covers:
  - Policy object construction and constraint loading.
  - Individual constraint application (each constraint fires in isolation).
  - Violation detection (a trade that violates any constraint is blocked).
  - A trade that passes all constraints is correctly allowed.

Run with:
    pytest backend/tests/test_policy_engine.py -v
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import FrozenSet, List, Optional
from zoneinfo import ZoneInfo

import pytest

from backend.intent.intent_models import (
    ActionSide,
    EnforcementResult,
    Intent,
    IntentType,
)
from backend.layer1_reasoning.agent import OpenClawAgent

_ET = ZoneInfo("America/New_York")


# ─────────────────────────────────────────────
# Policy data model
# ─────────────────────────────────────────────


class PolicyConstraintConfig:
    """
    Typed configuration object for a single policy constraint.
    Mirrors what a real YAML-backed policy loader would produce.
    """

    def __init__(
        self,
        name: str,
        constraint_type: str,
        value: str,
        severity: str = "block",
        description: str = "",
    ) -> None:
        self.name = name
        self.constraint_type = constraint_type
        self.value = value
        self.severity = severity
        self.description = description

    def __repr__(self) -> str:
        return (
            f"PolicyConstraintConfig(name={self.name!r}, "
            f"type={self.constraint_type!r}, value={self.value!r})"
        )


class TradingPolicy:
    """
    Aggregates a list of ``PolicyConstraintConfig`` objects that the
    ``CompositePolicyEngine`` will enforce.

    Analogous to what ``layer2_enforcement/policy_models.py`` should provide.
    """

    def __init__(
        self,
        policy_id: str,
        name: str,
        constraints: List[PolicyConstraintConfig],
    ) -> None:
        self.policy_id = policy_id
        self.name = name
        self.constraints = constraints

    @classmethod
    def default(cls) -> "TradingPolicy":
        """
        Build the default analyst trading policy used throughout the project.

        Returns a ``TradingPolicy`` with:
          - MAX_TRADE_SIZE: $500
          - AUTHORIZED_TICKERS: MSFT, AAPL, GOOGL, AMZN
          - TRADING_HOURS: 09:30–16:00 ET, Mon–Fri
        """
        return cls(
            policy_id="analyst_policy_v1",
            name="Analyst Trading Policy",
            constraints=[
                PolicyConstraintConfig(
                    name="max_trade_size",
                    constraint_type="MAX_TRADE_SIZE",
                    value="500",
                    severity="block",
                    description="Maximum single trade value is $500",
                ),
                PolicyConstraintConfig(
                    name="authorized_tickers",
                    constraint_type="AUTHORIZED_TICKERS",
                    value="MSFT,AAPL,GOOGL,AMZN",
                    severity="block",
                    description="Only whitelisted tickers may be traded",
                ),
                PolicyConstraintConfig(
                    name="trading_hours",
                    constraint_type="TRADING_HOURS",
                    value="09:30-16:00",
                    severity="block",
                    description="Trades only during regular market hours",
                ),
            ],
        )


# ─────────────────────────────────────────────
# Composite policy engine
# ─────────────────────────────────────────────


class CompositePolicyEngine:
    """
    Applies all constraints defined in a ``TradingPolicy`` in order.

    Stops at the first violated constraint (fail-fast semantics) and
    returns a ``EnforcementResult`` with ``allowed=False`` and the
    reason from the violated constraint.

    The *now* parameter allows callers to inject a fixed datetime for
    deterministic trading-hours tests.
    """

    def __init__(
        self, policy: TradingPolicy, now: Optional[datetime] = None
    ) -> None:
        self.policy = policy
        self._fixed_now = now

        # Pre-parse constraint values for efficiency
        self._max_trade_value: float = float("inf")
        self._allowed_tickers: FrozenSet[str] = frozenset()
        self._market_open_minutes: int = 9 * 60 + 30
        self._market_close_minutes: int = 16 * 60

        for c in policy.constraints:
            if c.constraint_type == "MAX_TRADE_SIZE":
                self._max_trade_value = float(c.value)
            elif c.constraint_type == "AUTHORIZED_TICKERS":
                self._allowed_tickers = frozenset(
                    t.strip() for t in c.value.split(",")
                )
            elif c.constraint_type == "TRADING_HOURS":
                # Expected format: "HH:MM-HH:MM"
                open_str, close_str = c.value.split("-")
                oh, om = map(int, open_str.strip().split(":"))
                ch, cm = map(int, close_str.strip().split(":"))
                self._market_open_minutes = oh * 60 + om
                self._market_close_minutes = ch * 60 + cm

    def _current_et(self) -> datetime:
        if self._fixed_now is not None:
            return self._fixed_now.astimezone(_ET)
        return datetime.now(_ET)

    def _is_market_open(self) -> bool:
        et_now = self._current_et()
        if et_now.weekday() >= 5:
            return False
        current_minutes = et_now.hour * 60 + et_now.minute
        return self._market_open_minutes <= current_minutes < self._market_close_minutes

    async def enforce(self, intent: Intent) -> EnforcementResult:
        if not intent.is_trade():
            return EnforcementResult(allowed=True, reason="")

        # ── Constraint 1: Authorised tickers ──────────────────────────────
        if self._allowed_tickers and intent.ticker not in self._allowed_tickers:
            return EnforcementResult(
                allowed=False,
                reason=(
                    f"Ticker '{intent.ticker}' is not authorised. "
                    f"Allowed: {sorted(self._allowed_tickers)}"
                ),
            )

        # ── Constraint 2: Per-trade size limit ────────────────────────────
        if intent.price is not None:
            order_value = intent.quantity * intent.price
            if order_value > self._max_trade_value:
                return EnforcementResult(
                    allowed=False,
                    reason=(
                        f"Order value ${order_value:.2f} exceeds the "
                        f"${self._max_trade_value:.2f} per-trade limit"
                    ),
                )

        # ── Constraint 3: Trading hours ───────────────────────────────────
        if not self._is_market_open():
            et_now = self._current_et()
            return EnforcementResult(
                allowed=False,
                reason=(
                    f"Trade outside market hours "
                    f"({et_now.strftime('%A %H:%M ET')}). "
                    f"Market is open Mon–Fri 09:30–16:00 ET."
                ),
            )

        return EnforcementResult(allowed=True, reason="")


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────


def _et_datetime(weekday: int, hour: int, minute: int) -> datetime:
    """Return an ET-aware datetime fixed at *weekday* (0=Mon) and *hour:minute*."""
    base_monday = datetime(2025, 1, 6, tzinfo=_ET)
    return base_monday + timedelta(days=weekday, hours=hour, minutes=minute)


_TRADING_NOW = _et_datetime(weekday=1, hour=10, minute=0)  # Tue 10:00 ET


class EchoSkill:
    async def execute(self, intent: Intent) -> dict:
        return {"executed": True, "intent": intent.to_dict()}


def _make_agent(
    policy: Optional[TradingPolicy] = None,
    now: Optional[datetime] = None,
) -> OpenClawAgent:
    p = policy or TradingPolicy.default()
    t = now or _TRADING_NOW
    sk = EchoSkill()
    engine = CompositePolicyEngine(policy=p, now=t)
    return OpenClawAgent(
        policy_engine=engine,
        skills={
            "trading_skill": sk,
            "analysis_skill": sk,
            "market_data_skill": sk,
        },
    )


# ─────────────────────────────────────────────
# Test: Policy loads correctly
# ─────────────────────────────────────────────


def test_default_policy_has_expected_id():
    """The default policy has the expected policy ID."""
    policy = TradingPolicy.default()
    assert policy.policy_id == "analyst_policy_v1"


def test_default_policy_has_expected_name():
    """The default policy has the expected human-readable name."""
    policy = TradingPolicy.default()
    assert policy.name == "Analyst Trading Policy"


def test_default_policy_has_three_constraints():
    """The default policy must define exactly three constraints."""
    policy = TradingPolicy.default()
    assert len(policy.constraints) == 3


def test_default_policy_constraint_types():
    """Each constraint has the correct type string."""
    policy = TradingPolicy.default()
    types = {c.constraint_type for c in policy.constraints}
    assert "MAX_TRADE_SIZE" in types
    assert "AUTHORIZED_TICKERS" in types
    assert "TRADING_HOURS" in types


def test_composite_engine_parses_max_trade_value():
    """The engine correctly parses the MAX_TRADE_SIZE constraint value."""
    engine = CompositePolicyEngine(policy=TradingPolicy.default(), now=_TRADING_NOW)
    assert engine._max_trade_value == pytest.approx(500.0)


def test_composite_engine_parses_authorized_tickers():
    """The engine correctly parses the AUTHORIZED_TICKERS constraint value."""
    engine = CompositePolicyEngine(policy=TradingPolicy.default(), now=_TRADING_NOW)
    assert "MSFT" in engine._allowed_tickers
    assert "AAPL" in engine._allowed_tickers
    assert "GOOGL" in engine._allowed_tickers
    assert "AMZN" in engine._allowed_tickers


def test_composite_engine_parses_trading_hours():
    """The engine correctly parses the TRADING_HOURS open/close minutes."""
    engine = CompositePolicyEngine(policy=TradingPolicy.default(), now=_TRADING_NOW)
    assert engine._market_open_minutes == 9 * 60 + 30   # 570 minutes
    assert engine._market_close_minutes == 16 * 60       # 960 minutes


# ─────────────────────────────────────────────
# Test: Constraints are applied
# ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ticker_constraint_applied():
    """
    A trade on a non-whitelisted ticker is blocked even when size and timing
    are within policy.
    """
    agent = _make_agent(now=_TRADING_NOW)
    # INTC is supported by the parser but not in the default whitelist
    response = await agent.run("buy 1 INTC at 30", user_id="tester")

    assert response.status == "blocked"
    assert "INTC" in response.reason


@pytest.mark.asyncio
async def test_size_constraint_applied():
    """
    A trade on a whitelisted ticker is blocked when the order value exceeds
    the per-trade limit.
    """
    agent = _make_agent(now=_TRADING_NOW)
    # AAPL whitelisted but 10 × $200 = $2,000 > $500
    response = await agent.run("buy 10 AAPL at 200", user_id="tester")

    assert response.status == "blocked"
    assert "2000" in response.reason or "500" in response.reason


@pytest.mark.asyncio
async def test_time_constraint_applied():
    """
    A trade on a whitelisted ticker within size limits is blocked when
    submitted outside market hours.
    """
    after_hours = _et_datetime(weekday=1, hour=20, minute=0)  # Tue 20:00
    agent = _make_agent(now=after_hours)
    response = await agent.run("buy 1 MSFT at 430", user_id="tester")

    assert response.status == "blocked"
    reason_lower = response.reason.lower()
    assert any(
        kw in reason_lower for kw in ("market", "hours", "time", "outside")
    )


@pytest.mark.asyncio
async def test_all_constraints_pass():
    """
    A trade on a whitelisted ticker, within the size limit, submitted during
    market hours, is ALLOWED.
    """
    agent = _make_agent(now=_TRADING_NOW)
    # MSFT whitelisted, 1 × $430 = $430 < $500, Tue 10:00 → market open
    response = await agent.run("buy 1 MSFT at 430", user_id="tester")

    assert response.status == "success", (
        f"Expected success for a compliant trade, got: {response.reason}"
    )


# ─────────────────────────────────────────────
# Test: Violations are detected
# ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_violation_detected_unknown_ticker():
    """Ticker violation is detected and surfaces a non-empty block reason."""
    agent = _make_agent(now=_TRADING_NOW)
    response = await agent.run("buy 1 INTC at 30", user_id="tester")

    assert response.status == "blocked"
    assert response.reason  # non-empty


@pytest.mark.asyncio
async def test_violation_detected_size_exceeded():
    """Size violation is detected and surfaces the order value and limit."""
    agent = _make_agent(now=_TRADING_NOW)
    response = await agent.run("buy 10 AAPL at 200", user_id="tester")

    assert response.status == "blocked"
    assert response.reason


@pytest.mark.asyncio
async def test_violation_detected_after_hours():
    """Time violation is detected when market is closed."""
    agent = _make_agent(now=_et_datetime(weekday=5, hour=10, minute=0))  # Sat
    response = await agent.run("buy 1 MSFT at 430", user_id="tester")

    assert response.status == "blocked"
    assert response.reason


@pytest.mark.asyncio
async def test_ticker_check_fires_before_size_check():
    """
    Constraint ordering: the ticker check runs before the size check so
    that the block reason references the unauthorised ticker (not the size).
    """
    agent = _make_agent(now=_TRADING_NOW)
    # INTC not whitelisted AND value $600 > $500 → ticker violation fires first
    response = await agent.run("buy 20 INTC at 30", user_id="tester")

    assert response.status == "blocked"
    assert "INTC" in response.reason, (
        f"Expected ticker violation to fire first; got reason: {response.reason!r}"
    )


@pytest.mark.asyncio
async def test_custom_policy_with_single_constraint():
    """
    A policy with only a size constraint can be constructed and enforced.
    """
    custom_policy = TradingPolicy(
        policy_id="custom_v1",
        name="Custom Size-Only Policy",
        constraints=[
            PolicyConstraintConfig(
                name="max_trade_size",
                constraint_type="MAX_TRADE_SIZE",
                value="1000",
                severity="block",
                description="$1,000 max trade",
            )
        ],
    )
    # No ticker or time constraints → any whitelisted ticker is OK
    agent = _make_agent(policy=custom_policy, now=_TRADING_NOW)

    # Under limit → allowed
    response = await agent.run("buy 5 AAPL at 100", user_id="tester")
    assert response.status == "success"

    # Over limit → blocked
    response = await agent.run("buy 20 AAPL at 100", user_id="tester")
    assert response.status == "blocked"
