"""
Pydantic schemas for the OpenClaw Trading Agent API.

Centralises all request/response models so they can be shared across route
modules, imported by client-side tooling, and validated consistently.

Models
------
TradeRequest      — POST /api/trade request body
TradeResponse     — POST /api/trade response
AnalysisRequest   — POST /api/analyze request body
AnalysisResponse  — POST /api/analyze response
PolicyConstraint  — A single policy rule (nested in PolicyResponse)
PolicyResponse    — GET /api/policy response
AccountInfo       — GET /api/account response
Position          — Single open equity position (nested in positions list)
AuditEntry        — Single enforcement audit log entry
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


# ──────────────────────────────────────────────────────────────────────────────
# Trading
# ──────────────────────────────────────────────────────────────────────────────


class TradeRequest(BaseModel):
    """Payload for POST /api/trade."""

    instruction: str = Field(
        ...,
        description=(
            "Natural language trade instruction, "
            "e.g. 'Buy 10 shares of MSFT at $430'"
        ),
    )
    user_id: Optional[str] = Field(
        "user_default",
        description="Requesting user identifier (for audit trail)",
    )


class TradeResponse(BaseModel):
    """Response from POST /api/trade."""

    status: str = Field(..., description="SUCCESS | BLOCKED | PENDING | ERROR")
    intent: Optional[dict] = Field(None, description="Parsed intent details")
    decision: Optional[dict] = Field(None, description="Policy enforcement decision")
    result: Optional[dict] = Field(None, description="Skill execution result")
    reason: Optional[str] = Field(
        None, description="Explanation for BLOCKED or ERROR status"
    )


# ──────────────────────────────────────────────────────────────────────────────
# Analysis
# ──────────────────────────────────────────────────────────────────────────────


class AnalysisRequest(BaseModel):
    """Payload for POST /api/analyze."""

    ticker: str = Field(
        ...,
        description="Asset ticker symbol, e.g. 'MSFT'",
    )
    user_id: Optional[str] = Field(
        "user_default",
        description="Requesting user identifier",
    )


class AnalysisResponse(BaseModel):
    """Response from POST /api/analyze."""

    ticker: str
    signal: str = Field(
        ...,
        description="BULLISH | BEARISH | NEUTRAL",
    )
    confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Signal confidence in the range 0.0-1.0",
    )
    summary: Optional[str] = Field(None, description="Human-readable analysis summary")
    details: Optional[dict] = Field(None, description="Additional analysis metadata")


# ──────────────────────────────────────────────────────────────────────────────
# Policy
# ──────────────────────────────────────────────────────────────────────────────


class PolicyConstraint(BaseModel):
    """A single policy enforcement constraint."""

    type: str = Field(..., description="Constraint kind, e.g. MAX_TRADE_SIZE")
    value: str = Field(..., description="Constraint value serialised as a string")
    severity: str = Field(
        ..., description="'block' halts the trade; 'warn' logs a warning only"
    )
    description: str = Field(..., description="Human-readable constraint explanation")


class PolicyResponse(BaseModel):
    """Response from GET /api/policy."""

    policy_id: str
    name: str
    constraints: List[dict] = Field(default_factory=list)


# ──────────────────────────────────────────────────────────────────────────────
# Account
# ──────────────────────────────────────────────────────────────────────────────


class AccountInfo(BaseModel):
    """Broker account information returned by GET /api/account."""

    cash: float = Field(..., description="Available cash balance")
    portfolio_value: float = Field(..., description="Total portfolio value")
    buying_power: float = Field(..., description="Current buying power")


class Position(BaseModel):
    """Single open equity position."""

    symbol: str
    qty: int
    avg_entry_price: float
    current_price: float
    market_value: float
    unrealized_pl: float
    unrealized_plpc: float
    side: str = Field(..., description="'long' or 'short'")


# ──────────────────────────────────────────────────────────────────────────────
# Audit
# ──────────────────────────────────────────────────────────────────────────────


class AuditEntry(BaseModel):
    """A single enforcement audit log entry."""

    intent_id: str
    timestamp: str
    user_id: str
    action: str = Field(..., description="e.g. EXECUTE_TRADE, ANALYZE")
    allowed: bool
    reason: Optional[str] = None
    details: Optional[dict] = None
