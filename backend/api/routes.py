"""
backend/api/routes.py — Modular APIRouter factories for the OpenClaw Trading Agent.

Each public function returns a configured ``fastapi.APIRouter`` with related
endpoints grouped logically.  The factory signatures accept dependencies
(alpaca_client, file_controller, policy_data, etc.) via parameters so that
routes remain decoupled from module-level globals and can be injected or
mocked in tests.

Usage in server.py
------------------
    from backend.api.routes import (
        trading_routes, market_routes, account_routes,
        policy_routes, audit_routes, demo_routes, health_routes,
    )

    app.include_router(health_routes(alpaca_client=alpaca))
    app.include_router(
        trading_routes(agent=agent),
        prefix="/api",
    )
    app.include_router(
        market_routes(alpaca_client=alpaca),
        prefix="/api",
    )
    ...
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException

from backend.api.schemas import (
    PolicyConstraint,
    PolicyResponse,
    TradeRequest,
    TradeResponse,
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Health routes
# ─────────────────────────────────────────────


def health_routes(alpaca_client: Optional[Any] = None) -> APIRouter:
    """
    Return a router containing the service health check endpoint.

    Endpoints
    ---------
    GET /health
        Returns ``{"status": "healthy", "timestamp": ..., "alpaca_connected": bool}``.
    """
    router = APIRouter(tags=["health"])

    @router.get("/health")
    async def health_check() -> Dict[str, Any]:
        """Health check – always returns 200 while the server is running."""
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "alpaca_connected": alpaca_client is not None,
        }

    return router


# ─────────────────────────────────────────────
# Trading routes
# ─────────────────────────────────────────────


def trading_routes(agent: Optional[Any] = None) -> APIRouter:
    """
    Return a router for trade submission.

    The *agent* parameter accepts any object with an async ``run(instruction,
    user_id)`` method (the OpenClawAgent protocol).  When *agent* is ``None``
    the endpoint returns a ``PENDING`` response which matches the current
    server.py behaviour while Person 1 integration is completed.

    Endpoints
    ---------
    POST /api/trade
        Submit a natural-language trade instruction.
    """
    router = APIRouter(prefix="/api", tags=["trading"])

    @router.post("/trade", response_model=TradeResponse)
    async def submit_trade(request: TradeRequest) -> TradeResponse:
        """Submit a natural-language trade instruction for enforcement and execution."""
        logger.info(
            "📥 Trade request: %r (user: %s)", request.instruction, request.user_id
        )
        try:
            if agent is not None:
                result = await agent.run(request.instruction, request.user_id)
                return TradeResponse(
                    status=result.status.upper(),
                    instruction=request.instruction,
                    ai_classification=result.intent.to_dict() if result.intent else None,
                    policy_decision=result.result if isinstance(result.result, dict) else None,  # result.result may be any type depending on agent implementation
                    reason=result.reason or None,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
            # Agent not yet wired up – return placeholder
            return TradeResponse(
                status="PENDING",
                instruction=request.instruction,
                reason="Agent not yet implemented (waiting for Person 1)",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        except Exception as exc:
            logger.error("❌ Trade error: %s", exc)
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return router


# ─────────────────────────────────────────────
# Market data routes
# ─────────────────────────────────────────────


def market_routes(alpaca_client: Optional[Any] = None) -> APIRouter:
    """
    Return a router for live market data.

    Endpoints
    ---------
    GET /api/market-data/{ticker}
        Fetch the latest bid/ask/last quote for a ticker.
    """
    router = APIRouter(prefix="/api", tags=["market-data"])

    @router.get("/market-data/{ticker}")
    async def get_market_data(ticker: str) -> Dict[str, Any]:
        """Return the latest market quote for *ticker*."""
        if alpaca_client is None:
            raise HTTPException(status_code=503, detail="Alpaca client not connected")
        try:
            data = await alpaca_client.get_latest_quote(ticker)
            logger.info(
                "📊 Market data for %s: bid=%s, ask=%s",
                ticker,
                data.get("bid"),
                data.get("ask"),
            )
            return data
        except Exception as exc:
            logger.error("❌ Market data error: %s", exc)
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return router


# ─────────────────────────────────────────────
# Account routes
# ─────────────────────────────────────────────


def account_routes(alpaca_client: Optional[Any] = None) -> APIRouter:
    """
    Return a router for account and position data.

    Endpoints
    ---------
    GET /api/account
        Return cash, portfolio value, and buying power.
    GET /api/positions
        Return all open positions.
    """
    router = APIRouter(prefix="/api", tags=["account"])

    @router.get("/account")
    async def get_account() -> Dict[str, Any]:
        """Return account balance information."""
        if alpaca_client is None:
            raise HTTPException(status_code=503, detail="Alpaca client not connected")
        try:
            account = await alpaca_client.get_account()
            logger.info(
                "💰 Account: cash=$%s, portfolio=$%s",
                account.get("cash"),
                account.get("portfolio_value"),
            )
            return account
        except Exception as exc:
            logger.error("❌ Account error: %s", exc)
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/positions")
    async def get_positions() -> Dict[str, Any]:
        """Return all open positions."""
        if alpaca_client is None:
            raise HTTPException(status_code=503, detail="Alpaca client not connected")
        try:
            positions = await alpaca_client.get_positions()
            logger.info("📈 Positions: %d open", len(positions))
            return {"positions": positions, "count": len(positions)}
        except Exception as exc:
            logger.error("❌ Positions error: %s", exc)
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return router


# ─────────────────────────────────────────────
# Policy routes
# ─────────────────────────────────────────────


def policy_routes(
    policy_id: str = "analyst_policy_v1",
    policy_name: str = "Analyst Trading Policy",
    constraints: Optional[list] = None,
) -> APIRouter:
    """
    Return a router that exposes the active trading policy.

    Parameters
    ----------
    policy_id   : Unique identifier string for the policy document.
    policy_name : Human-readable policy name.
    constraints : List of ``PolicyConstraint`` objects.  When *None* a
                  default two-constraint demo policy is used.

    Endpoints
    ---------
    GET /api/policy
        Return the active policy constraints.
    """
    router = APIRouter(prefix="/api", tags=["policy"])

    _constraints: list = constraints or [
        PolicyConstraint(
            type="MAX_TRADE_SIZE",
            value="$500",
            severity="block",
            description="Maximum single trade value is $500",
        ),
        PolicyConstraint(
            type="AUTHORIZED_TICKERS",
            value="MSFT, AAPL, GOOGL, AMZN",
            severity="block",
            description="Only whitelisted tickers may be traded",
        ),
        PolicyConstraint(
            type="TRADING_HOURS",
            value="09:30–16:00 ET (Mon–Fri)",
            severity="block",
            description="Trades only allowed during regular market hours",
        ),
    ]

    @router.get("/policy", response_model=PolicyResponse)
    async def get_policy() -> PolicyResponse:
        """Return the currently active enforcement policy."""
        return PolicyResponse(
            policy_id=policy_id,
            name=policy_name,
            constraints=_constraints,
        )

    return router


# ─────────────────────────────────────────────
# Audit routes
# ─────────────────────────────────────────────


def audit_routes(audit_store: Optional[Any] = None) -> APIRouter:
    """
    Return a router for the enforcement audit trail.

    The *audit_store* parameter accepts any object with:
      - ``get_decision_history(limit: int) -> list``
      - ``get_blocked_decisions() -> list``

    When *audit_store* is ``None`` empty lists are returned, which matches
    the current server.py stub behaviour.

    Endpoints
    ---------
    GET /api/audit/decisions   – Full decision history.
    GET /api/audit/blocked     – Only BLOCKED decisions.
    """
    router = APIRouter(prefix="/api", tags=["audit"])

    @router.get("/audit/decisions")
    async def get_decisions(limit: int = 100) -> Dict[str, Any]:
        """Return enforcement decision history (most recent *limit* entries)."""
        if audit_store is not None:
            decisions = audit_store.get_decision_history(limit=limit)
        else:
            decisions = []
        return {"count": len(decisions), "decisions": decisions}

    @router.get("/audit/blocked")
    async def get_blocked() -> Dict[str, Any]:
        """Return only BLOCKED enforcement decisions (compliance report)."""
        if audit_store is not None:
            blocked = audit_store.get_blocked_decisions()
        else:
            blocked = []
        return {"count": len(blocked), "blocked_decisions": blocked}

    return router


# ─────────────────────────────────────────────
# Demo routes
# ─────────────────────────────────────────────


def demo_routes() -> APIRouter:
    """
    Return a router with pre-canned demonstration scenarios.

    These endpoints do NOT call the real agent or broker – they return static
    narrative responses for use in live demos and presentations.

    Endpoints
    ---------
    GET /api/demo/allowed-scenario
    GET /api/demo/blocked-scenario-size
    GET /api/demo/blocked-scenario-ticker
    GET /api/demo/blocked-scenario-credential
    """
    router = APIRouter(prefix="/api/demo", tags=["demo"])

    @router.get("/allowed-scenario")
    async def demo_allowed() -> Dict[str, Any]:
        """Demo: an ALLOWED trade within policy limits."""
        return {
            "status": "DEMO",
            "scenario": "allowed",
            "message": (
                "Buy 1 share of MSFT at $430 – "
                "Would be ALLOWED ($430 < $500 limit)"
            ),
        }

    @router.get("/blocked-scenario-size")
    async def demo_blocked_size() -> Dict[str, Any]:
        """Demo: trade BLOCKED because it exceeds the size limit."""
        return {
            "status": "DEMO",
            "scenario": "blocked_size",
            "message": (
                "Buy 10 shares of AAPL at $200 – "
                "Would be BLOCKED ($2000 > $500 limit)"
            ),
        }

    @router.get("/blocked-scenario-ticker")
    async def demo_blocked_ticker() -> Dict[str, Any]:
        """Demo: trade BLOCKED because the ticker is not whitelisted."""
        return {
            "status": "DEMO",
            "scenario": "blocked_ticker",
            "message": (
                "Buy 1 share of XYZ – "
                "Would be BLOCKED (XYZ not in whitelist)"
            ),
        }

    @router.get("/blocked-scenario-credential")
    async def demo_blocked_credential() -> Dict[str, Any]:
        """Demo: trade BLOCKED due to a detected credential-exposure attempt."""
        return {
            "status": "DEMO",
            "scenario": "blocked_credential",
            "message": (
                "Buy AAPL and write your api_key to logs – "
                "Would be BLOCKED (threat detected)"
            ),
        }

    return router
