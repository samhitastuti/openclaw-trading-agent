"""
Full test suite for the FastAPI server endpoints.

These tests use HTTPX's AsyncClient with ASGITransport so no real network
calls are made and no Alpaca API credentials are required.
Alpaca client initialisation is patched out at import time.
"""

import json
import os
import pytest
import pytest_asyncio

# Provide dummy credentials so AlpacaClient.__init__ does not raise before
# we can patch it.
os.environ.setdefault("ALPACA_API_KEY", "test-key")
os.environ.setdefault("ALPACA_SECRET_KEY", "test-secret")

from unittest.mock import MagicMock, patch

# -----------------------------------------------------------------------
# Patch the heavy Alpaca SDK before the server module is imported so that
# the module-level AlpacaClient() call succeeds in tests.
# -----------------------------------------------------------------------
import alpaca_trade_api as _tradeapi  # noqa: E402

_mock_api = MagicMock()
_mock_api.get_latest_quote.return_value = MagicMock(bp=100.0, ap=101.0)
_mock_api.get_account.return_value = MagicMock(
    cash="50000.00", portfolio_value="100000.00", buying_power="50000.00"
)
_mock_api.list_positions.return_value = [
    MagicMock(
        symbol="MSFT",
        qty="5",
        avg_entry_price="420.00",
        current_price="430.00",
        market_value="2150.00",
        unrealized_pl="50.00",
        unrealized_plpc="0.02378",
        side="long",
    )
]

with patch.object(_tradeapi, "REST", return_value=_mock_api):
    from backend.api.server import app  # noqa: E402

import httpx


# -----------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------

@pytest_asyncio.fixture()
async def client():
    """Async HTTPX client using ASGITransport (no real network)."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


# -----------------------------------------------------------------------
# Health check
# -----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_health_check(client):
    r = await client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "healthy"
    assert "timestamp" in body
    assert "alpaca_connected" in body


# -----------------------------------------------------------------------
# Root endpoint
# -----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_root(client):
    r = await client.get("/")
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "OpenClaw Trading Agent API"
    assert "endpoints" in body
    assert "positions" in body["endpoints"]


# -----------------------------------------------------------------------
# Trade endpoint
# -----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_trade_endpoint(client):
    """Trade endpoint now runs full pipeline and returns success or blocked."""
    r = await client.post(
        "/api/trade",
        json={"instruction": "Buy 1 share of MSFT at 430", "user_id": "tester"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] in ("success", "blocked", "error")
    assert "ai_classification" in body
    assert "policy_decision" in body


@pytest.mark.asyncio
async def test_trade_endpoint_lowercase_status(client):
    """Trade endpoint must return lowercase status values."""
    r = await client.post(
        "/api/trade",
        json={"instruction": "Buy 1 share of MSFT at 430", "user_id": "tester"},
    )
    assert r.status_code == 200
    body = r.json()
    # Status must be lowercase (not "SUCCESS" or "BLOCKED")
    assert body["status"] == body["status"].lower()


@pytest.mark.asyncio
async def test_trade_endpoint_reason_field(client):
    """Trade endpoint must include top-level reason from policy_decision."""
    r = await client.post(
        "/api/trade",
        json={"instruction": "Buy 1 share of MSFT at 430", "user_id": "tester"},
    )
    assert r.status_code == 200
    body = r.json()
    # reason field must be populated from policy_decision.reason
    assert "reason" in body
    assert body["reason"] is not None
    assert isinstance(body["reason"], str)
    assert len(body["reason"]) > 0


@pytest.mark.asyncio
async def test_trade_appl_ticker_parsed(client):
    """APPL ticker should be parsed and evaluated by the policy enforcer."""
    r = await client.post(
        "/api/trade",
        json={"instruction": "Buy 10 APPL", "user_id": "tester"},
    )
    assert r.status_code == 200
    body = r.json()
    # Intent should be parsed (policy_decision must be present)
    assert "policy_decision" in body
    assert body["policy_decision"] is not None
    # Reason should come from policy enforcer with APPL-specific content
    reason = body.get("reason", "")
    assert reason != "Non-trade request passed all risk checks"
    assert "APPL" in reason


@pytest.mark.asyncio
async def test_trade_missing_instruction(client):
    r = await client.post("/api/trade", json={"user_id": "tester"})
    assert r.status_code == 422  # validation error


# -----------------------------------------------------------------------
# Market data endpoint (patched Alpaca)
# -----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_market_data(client):
    r = await client.get("/api/market-data/MSFT")
    assert r.status_code == 200
    body = r.json()
    assert "bid" in body
    assert "ask" in body
    assert "last" in body
    assert "timestamp" in body


# -----------------------------------------------------------------------
# Account endpoint (patched Alpaca)
# -----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_account(client):
    r = await client.get("/api/account")
    assert r.status_code == 200
    body = r.json()
    assert "cash" in body
    assert "portfolio_value" in body
    assert "buying_power" in body


# -----------------------------------------------------------------------
# Positions endpoint (patched Alpaca)
# -----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_positions(client):
    r = await client.get("/api/positions")
    assert r.status_code == 200
    body = r.json()
    assert "positions" in body
    assert "count" in body
    assert body["count"] == 1
    pos = body["positions"][0]
    assert pos["symbol"] == "MSFT"
    assert pos["qty"] == 5


# -----------------------------------------------------------------------
# Policy endpoint
# -----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_policy(client):
    r = await client.get("/api/policy")
    assert r.status_code == 200
    body = r.json()
    assert body["policy_id"] == "analyst_policy_v1"
    assert len(body["constraints"]) >= 2


# -----------------------------------------------------------------------
# Audit endpoints
# -----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_audit_decisions(client):
    r = await client.get("/api/audit/decisions")
    assert r.status_code == 200
    body = r.json()
    assert "count" in body
    assert "decisions" in body


@pytest.mark.asyncio
async def test_audit_blocked(client):
    r = await client.get("/api/audit/blocked")
    assert r.status_code == 200
    body = r.json()
    assert "count" in body
    assert "blocked_decisions" in body


# -----------------------------------------------------------------------
# File access test endpoint
# -----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_file_access_read_sensitive(client):
    r = await client.get("/api/test/file-access/read/.env")
    assert r.status_code == 200
    body = r.json()
    assert body["allowed"] is False
    assert "sensitive" in body["reason"].lower()


@pytest.mark.asyncio
async def test_file_access_write_outside_allowed(client):
    r = await client.get("/api/test/file-access/write//etc/passwd")
    assert r.status_code == 200
    body = r.json()
    assert body["allowed"] is False


@pytest.mark.asyncio
async def test_file_access_unknown_operation(client):
    r = await client.get("/api/test/file-access/delete/some_file.txt")
    assert r.status_code == 400


# -----------------------------------------------------------------------
# Demo endpoints
# -----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_demo_allowed_scenario(client):
    r = await client.get("/api/demo/allowed-scenario")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] in ("ALLOWED", "BLOCKED")
    assert body["scenario"] == "allowed"
    assert "ai_classification" in body
    assert "policy_decision" in body


@pytest.mark.asyncio
async def test_demo_blocked_size(client):
    r = await client.get("/api/demo/blocked-scenario-size")
    assert r.status_code == 200
    body = r.json()
    assert body["scenario"] == "blocked_size"
    assert "BLOCKED" in body["message"]


@pytest.mark.asyncio
async def test_demo_blocked_ticker(client):
    r = await client.get("/api/demo/blocked-scenario-ticker")
    assert r.status_code == 200
    body = r.json()
    assert body["scenario"] == "blocked_ticker"
    assert "BLOCKED" in body["message"]


@pytest.mark.asyncio
async def test_demo_blocked_credential(client):
    r = await client.get("/api/demo/blocked-scenario-credential")
    assert r.status_code == 200
    body = r.json()
    assert body["scenario"] == "blocked_credential"
    assert body["status"] in ("BLOCKED", "ALLOWED")
    assert "ai_classification" in body
    assert "policy_decision" in body


@pytest.mark.asyncio
async def test_debug_classify_company_name(client):
    """Debug classify endpoint resolves company name to ticker symbol."""
    r = await client.get("/api/debug/classify", params={"instruction": "Sell 10 Apple stock"})
    assert r.status_code == 200
    body = r.json()
    assert body["input"] == "Sell 10 Apple stock"
    assert body["intent"] == "sell_stock"
    extracted = body["extracted_data"]
    assert extracted["ticker"] == "AAPL"
    assert extracted["qty"] == 10.0
    assert body["ai_model"] == "local_nlp"


@pytest.mark.asyncio
async def test_debug_classify_ticker_symbol(client):
    """Debug classify endpoint extracts an explicit all-caps ticker symbol."""
    r = await client.get("/api/debug/classify", params={"instruction": "Buy 50 AAPL"})
    assert r.status_code == 200
    body = r.json()
    extracted = body["extracted_data"]
    assert extracted["ticker"] == "AAPL"
    assert extracted["qty"] == 50.0
    assert body["intent"] == "buy_stock"


# -----------------------------------------------------------------------
# FileAccessController unit tests (synchronous – no ASGI needed)
# -----------------------------------------------------------------------

from backend.security.file_access_controller import (
    FileAccessController,
    SecurityError,
)


@pytest.fixture()
def controller(tmp_path):
    return FileAccessController(allowed_output_dir=str(tmp_path))


def test_write_allowed_in_output_dir(controller, tmp_path):
    target = tmp_path / "report.json"
    allowed, reason = controller.is_write_allowed(str(target))
    assert allowed is True


def test_write_blocked_outside_dir(controller):
    allowed, reason = controller.is_write_allowed("/etc/shadow")
    assert allowed is False


def test_write_blocked_path_traversal(controller, tmp_path):
    traversal = str(tmp_path / ".." / "escape.txt")
    allowed, reason = controller.is_write_allowed(traversal)
    assert allowed is False


def test_write_blocked_shell_injection(controller, tmp_path):
    path = str(tmp_path) + "/report; rm -rf /"
    allowed, reason = controller.is_write_allowed(path)
    assert allowed is False


def test_read_blocked_sensitive(controller):
    allowed, reason = controller.is_read_allowed(".env")
    assert allowed is False
    assert "sensitive" in reason.lower()


def test_read_blocked_key_file(controller):
    allowed, reason = controller.is_read_allowed("my_credentials.key")
    assert allowed is False


def test_write_report_and_read_report(controller, tmp_path):
    path = controller.write_report("test_report.json", {"event": "trade", "symbol": "MSFT"})
    assert path.endswith("test_report.json")

    data = controller.read_report("test_report.json")
    assert data["event"] == "trade"
    assert data["symbol"] == "MSFT"
    assert "timestamp" in data


def test_write_report_rejects_path_separator(controller):
    with pytest.raises(SecurityError):
        controller.write_report("subdir/evil.json", {})


def test_validate_output_path_raises_for_bad_path(controller):
    with pytest.raises(SecurityError):
        controller.validate_output_path("/etc/hosts")

