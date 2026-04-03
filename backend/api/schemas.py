"""
backend/api/schemas.py — Pydantic request/response models for the OpenClaw Trading Agent API.

Centralises all API models so they can be imported cleanly by server.py,
routes.py, and external test/client code.  server.py's inline model
definitions are intentionally kept as thin re-exports for backwards
compatibility.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ─────────────────────────────────────────────
# Trade models
# ─────────────────────────────────────────────


class TradeRequest(BaseModel):
    """Request body for POST /api/trade."""

    instruction: str = Field(
        ...,
        description=(
            "Natural-language trade instruction, "
            "e.g. 'Buy 10 shares of AAPL at $150'"
        ),
    )
    user_id: Optional[str] = Field(
        default="user_default",
        description="Identifier for the requesting user",
    )


class TradeResponse(BaseModel):
    """Response from POST /api/trade."""

    status: str = Field(
        ...,
        description="Outcome: SUCCESS | BLOCKED | ERROR | PENDING",
    )
    instruction: Optional[str] = Field(
        default=None, description="Original trade instruction"
    )
    intent: Optional[Dict[str, Any]] = None
    ai_classification: Optional[Dict[str, Any]] = Field(
        default=None, description="AI intent classification result"
    )
    policy_decision: Optional[Dict[str, Any]] = Field(
        default=None, description="Policy enforcement decision"
    )
    decision: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    reason: Optional[str] = None
    timestamp: Optional[str] = Field(
        default=None, description="ISO 8601 UTC timestamp of the decision"
    )


# ─────────────────────────────────────────────
# Analysis models
# ─────────────────────────────────────────────


class AnalysisRequest(BaseModel):
    """Request body for POST /api/analyze."""

    ticker: str = Field(
        ...,
        description="Asset symbol to analyse, e.g. 'AAPL'",
    )
    user_id: Optional[str] = Field(
        default="user_default",
        description="Identifier for the requesting user",
    )


class AnalysisResponse(BaseModel):
    """Response from POST /api/analyze."""

    ticker: str
    signal: str = Field(
        ...,
        description="Market signal: BULLISH | BEARISH | NEUTRAL",
    )
    reason: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


# ─────────────────────────────────────────────
# Policy models
# ─────────────────────────────────────────────


class PolicyConstraint(BaseModel):
    """A single policy constraint returned by GET /api/policy."""

    type: str = Field(
        ...,
        description="Constraint category, e.g. 'MAX_TRADE_SIZE'",
    )
    value: str = Field(
        ...,
        description="Constraint value as a human-readable string",
    )
    severity: str = Field(
        ...,
        description="Enforcement level: 'block' | 'warn'",
    )
    description: str = Field(..., description="Human-readable explanation")


class PolicyResponse(BaseModel):
    """Response from GET /api/policy."""

    policy_id: str
    name: str
    constraints: List[PolicyConstraint]


# ─────────────────────────────────────────────
# Account / position models
# ─────────────────────────────────────────────


class AccountInfo(BaseModel):
    """Account summary returned by GET /api/account."""

    cash: float = Field(..., description="Available cash balance in USD")
    portfolio_value: float = Field(
        ..., description="Total portfolio value in USD"
    )
    buying_power: float = Field(
        ..., description="Remaining buying power in USD"
    )


class Position(BaseModel):
    """A single open position returned by GET /api/positions."""

    symbol: str
    qty: int = Field(..., description="Number of shares held")
    avg_entry_price: float = Field(
        ..., description="Average entry price per share in USD"
    )
    current_price: float = Field(
        ..., description="Current market price per share in USD"
    )
    market_value: float = Field(
        ..., description="Current market value of the position in USD"
    )
    unrealized_pl: float = Field(
        ..., description="Unrealised profit/loss in USD"
    )
    unrealized_plpc: float = Field(
        ...,
        description="Unrealised profit/loss as a fraction (e.g. 0.02 = 2%)",
    )
    side: str = Field(..., description="'long' or 'short'")


# ─────────────────────────────────────────────
# Audit models
# ─────────────────────────────────────────────


class AuditEntry(BaseModel):
    """A single enforcement decision entry from the audit trail."""

    entry_id: str = Field(
        ..., description="Unique identifier for this audit record"
    )
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp")
    intent_type: str = Field(
        ..., description="Intent category, e.g. 'EXECUTE_TRADE'"
    )
    ticker: str
    quantity: float
    side: str
    decision: str = Field(
        ...,
        description="Enforcement outcome: 'ALLOWED' | 'BLOCKED'",
    )
    reason: Optional[str] = Field(
        default=None,
        description="Block reason (only set when decision='BLOCKED')",
    )
    user_id: str
