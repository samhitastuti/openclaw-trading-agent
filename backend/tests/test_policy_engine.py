"""
test_policy_engine.py — Tests for policy engine integration.

Covers:
  - The API's /api/policy endpoint returns correctly structured policy data
  - Policy constraints include required fields (type, value, severity, description)
  - Constraint types match expected enforcement categories
  - A custom policy engine correctly allows and blocks based on its rules
  - Policy violations are detected and surfaced as BLOCKED responses
"""

from __future__ import annotations

import os
import pytest
import pytest_asyncio

# Provide dummy credentials so AlpacaClient does not raise before patching.
os.environ.setdefault("ALPACA_API_KEY", "test-key")
os.environ.setdefault("ALPACA_SECRET_KEY", "test-secret")

from unittest.mock import MagicMock, patch

import alpaca_trade_api as _tradeapi  # noqa: E402

_mock_api = MagicMock()
_mock_api.get_latest_quote.return_value = MagicMock(bidprice=100.0, askprice=101.0)
_mock_api.get_account.return_value = MagicMock(
    cash="50000.00", portfolio_value="100000.00", buying_power="50000.00"
)
_mock_api.list_positions.return_value = []

with patch.object(_tradeapi, "REST", return_value=_mock_api):
    from backend.api.server import app  # noqa: E402

import httpx

from backend.intent.intent_models import (
    EnforcementResult,
    Intent,
    IntentType,
    ActionSide,
)
from backend.layer1_reasoning.agent import OpenClawAgent


# ─────────────────────────────────────────────
# HTTPX client fixture (mirrors test_api_endpoints.py)
# ─────────────────────────────────────────────


@pytest_asyncio.fixture()
async def client():
    """Async HTTPX client using ASGITransport (no real network calls)."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


# ─────────────────────────────────────────────
# Policy endpoint tests
# ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_policy_endpoint_loads_correctly(client):
    """GET /api/policy returns HTTP 200 with a valid JSON body."""
    r = await client.get("/api/policy")
    assert r.status_code == 200
    body = r.json()
    assert "policy_id" in body
    assert "name" in body
    assert "constraints" in body


@pytest.mark.asyncio
async def test_policy_has_expected_id_and_name(client):
    """The policy identifier and name match the configured values."""
    r = await client.get("/api/policy")
    body = r.json()
    assert body["policy_id"] == "analyst_policy_v1"
    assert body["name"] == "Analyst Trading Policy"


@pytest.mark.asyncio
async def test_policy_constraints_are_non_empty(client):
    """At least one constraint must be defined in the active policy."""
    r = await client.get("/api/policy")
    body = r.json()
    assert len(body["constraints"]) >= 1


@pytest.mark.asyncio
async def test_policy_constraint_fields(client):
    """Every constraint must carry the required metadata fields."""
    r = await client.get("/api/policy")
    body = r.json()
    required_fields = {"type", "value", "severity", "description"}
    for constraint in body["constraints"]:
        missing = required_fields - constraint.keys()
        assert not missing, f"Constraint missing fields: {missing} — {constraint}"


@pytest.mark.asyncio
async def test_policy_contains_max_trade_size_constraint(client):
    """A MAX_TRADE_SIZE constraint must be present in the policy."""
    r = await client.get("/api/policy")
    body = r.json()
    types = {c["type"] for c in body["constraints"]}
    assert "MAX_TRADE_SIZE" in types


@pytest.mark.asyncio
async def test_policy_contains_authorized_tickers_constraint(client):
    """An AUTHORIZED_TICKERS constraint must be present in the policy."""
    r = await client.get("/api/policy")
    body = r.json()
    types = {c["type"] for c in body["constraints"]}
    assert "AUTHORIZED_TICKERS" in types


# ─────────────────────────────────────────────
# Mock policy engine unit tests
# ─────────────────────────────────────────────


class CompositeTestEngine:
    """
    A minimal policy engine that enforces two rules:

    1. MAX_TRADE_SIZE: total value (qty × price) must not exceed *max_value*.
    2. AUTHORIZED_TICKERS: only tickers in *allowed_tickers* may be traded.

    Both rules are applied simultaneously; a single violation is enough to
    block the intent.
    """

    def __init__(
        self,
        max_value: float = 500.0,
        allowed_tickers: set[str] | None = None,
    ):
        self.max_value = max_value
        self.allowed_tickers = allowed_tickers or {"MSFT", "AAPL", "GOOGL", "AMZN"}

    async def enforce(self, intent: Intent) -> EnforcementResult:
        if not intent.is_trade():
            return EnforcementResult(allowed=True, reason="")

        # Rule 1: authorized tickers
        if intent.ticker not in self.allowed_tickers:
            return EnforcementResult(
                allowed=False,
                reason=f"Ticker '{intent.ticker}' is not authorized.",
            )

        # Rule 2: maximum trade size (only when price is known)
        if intent.price is not None:
            total = intent.quantity * intent.price
            if total > self.max_value:
                return EnforcementResult(
                    allowed=False,
                    reason=(
                        f"Order value ${total:,.2f} exceeds the "
                        f"${self.max_value:,.2f} limit."
                    ),
                )

        return EnforcementResult(allowed=True, reason="")


class EchoSkill:
    async def execute(self, intent: Intent) -> dict:
        return {"status": "executed", "ticker": intent.ticker}


def _make_agent() -> OpenClawAgent:
    return OpenClawAgent(
        policy_engine=CompositeTestEngine(),
        skills={
            "trading_skill": EchoSkill(),
            "analysis_skill": EchoSkill(),
            "market_data_skill": EchoSkill(),
        },
    )


@pytest.mark.asyncio
async def test_policy_allows_valid_trade():
    """A trade within all constraints is approved by the composite engine."""
    agent = _make_agent()
    response = await agent.run("buy 1 MSFT at 430", user_id="pe_01")

    assert response.status == "success"


@pytest.mark.asyncio
async def test_policy_detects_unauthorized_ticker_violation():
    """Trading an unauthorized ticker is detected as a policy violation."""
    agent = _make_agent()
    # TSLA is parseable but not in the engine's allowed_tickers set.
    response = await agent.run("buy 1 TSLA", user_id="pe_02")

    assert response.status == "blocked"
    assert "TSLA" in response.reason


@pytest.mark.asyncio
async def test_policy_detects_size_violation():
    """Exceeding the max trade value is detected as a policy violation."""
    agent = _make_agent()
    # 10 × $200 = $2,000 > $500 limit
    response = await agent.run("buy 10 AAPL at 200", user_id="pe_03")

    assert response.status == "blocked"
    assert response.reason is not None


@pytest.mark.asyncio
async def test_policy_constraints_are_applied_together():
    """
    Both constraints are evaluated. A ticker violation is caught even if
    the size would have been acceptable.
    """
    agent = _make_agent()
    # TSLA is not authorized; size (1 × $200 = $200) would be fine.
    response = await agent.run("buy 1 TSLA at 200", user_id="pe_04")

    assert response.status == "blocked"
    assert "TSLA" in response.reason
