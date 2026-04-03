"""
intent_models.py — Structured data models for the OpenClaw Reasoning Layer.

Defines the canonical representation of a parsed user intent.
These models act as the contract between:
  - intent_parser (produces Intent)
  - agent (orchestrates Intent)
  - policy_engine (receives Intent for enforcement)
  - skills (receive Intent for execution)

No business logic. Pure data structures.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


# ─────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────


class IntentType(str, Enum):
    """
    High-level category of what the user wants the agent to do.

    Using str-mixin so IntentType.EXECUTE_TRADE == "EXECUTE_TRADE"
    works in JSON serialization without extra handling.
    """

    EXECUTE_TRADE = "EXECUTE_TRADE"   # Place a buy or sell order
    ANALYZE = "ANALYZE"               # Run analysis on an asset
    FETCH_DATA = "FETCH_DATA"         # Retrieve market data / price quote
    UNKNOWN = "UNKNOWN"               # Parser could not determine intent


class ActionSide(str, Enum):
    """
    Direction of a trade intent.
    Only relevant when IntentType == EXECUTE_TRADE.
    """

    BUY = "BUY"
    SELL = "SELL"
    NONE = "NONE"   # Not a trade intent


# ─────────────────────────────────────────────
# Core Intent Model
# ─────────────────────────────────────────────


@dataclass
class Intent:
    """
    The canonical structured representation of a user's parsed command.

    This object flows through the entire pipeline:
      parser → agent → policy_engine → skill (if allowed)

    Fields
    ------
    type        : What the user wants to do (IntentType)
    ticker      : The asset symbol (e.g. "AAPL", "TSLA")
    quantity    : Number of shares / units (0.0 for non-trade intents)
    side        : BUY / SELL / NONE
    price       : Optional limit price; None = market order
    raw_input   : The original unmodified user string (for audit)
    user_id     : Identifier of the requesting user / session
    timestamp   : UTC ISO-8601 creation time (auto-set)
    intent_id   : Unique UUID for this intent (auto-set, for tracing)
    """

    # ── Required ──────────────────────────────
    type: IntentType
    ticker: str
    quantity: float
    side: ActionSide

    # ── Optional ──────────────────────────────
    price: Optional[float] = None          # Limit price; None → market order

    # ── Metadata (auto-populated) ─────────────
    raw_input: str = ""
    user_id: str = "anonymous"
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    intent_id: str = field(
        default_factory=lambda: str(uuid.uuid4())
    )

    # ─────────────────────────────────────────
    # Serialisation
    # ─────────────────────────────────────────

    def to_dict(self) -> dict:
        """
        Return a JSON-serialisable dictionary representation.
        Used when passing the intent to the enforcement layer or logging.
        """
        return {
            "intent_id": self.intent_id,
            "type": self.type.value,
            "ticker": self.ticker,
            "quantity": self.quantity,
            "side": self.side.value,
            "price": self.price,
            "raw_input": self.raw_input,
            "user_id": self.user_id,
            "timestamp": self.timestamp,
        }

    # ─────────────────────────────────────────
    # Helper predicates
    # ─────────────────────────────────────────

    def is_trade(self) -> bool:
        """True if this intent represents a trade execution request."""
        return self.type == IntentType.EXECUTE_TRADE

    def is_analysis(self) -> bool:
        """True if this intent requests asset analysis."""
        return self.type == IntentType.ANALYZE

    def is_data_fetch(self) -> bool:
        """True if this intent requests a market data / price lookup."""
        return self.type == IntentType.FETCH_DATA

    def is_buy(self) -> bool:
        """True if this is a BUY order."""
        return self.side == ActionSide.BUY

    def is_sell(self) -> bool:
        """True if this is a SELL order."""
        return self.side == ActionSide.SELL

    def is_market_order(self) -> bool:
        """True when no limit price is specified (market order semantics)."""
        return self.price is None

    def with_updated_quantity(self, new_qty: float) -> "Intent":
        """
        Return a NEW Intent with a different quantity.
        Used by multi-step reasoning to adjust order sizes.
        Immutable-style helper — does not mutate self.
        """
        import dataclasses
        return dataclasses.replace(self, quantity=new_qty)

    def with_updated_side(self, new_side: ActionSide) -> "Intent":
        """
        Return a NEW Intent with a different action side.
        Used by multi-step reasoning (e.g. analysis drives direction).
        """
        import dataclasses
        return dataclasses.replace(self, side=new_side)

    # ─────────────────────────────────────────
    # Display
    # ─────────────────────────────────────────

    def __repr__(self) -> str:
        price_str = f" @ ${self.price:.2f}" if self.price else " (market)"
        return (
            f"<Intent [{self.intent_id[:8]}] "
            f"{self.type.value} | {self.side.value} "
            f"{self.quantity}x {self.ticker}{price_str} "
            f"user={self.user_id}>"
        )


# ─────────────────────────────────────────────
# Enforcement Result Model
# ─────────────────────────────────────────────


@dataclass
class EnforcementResult:
    """
    Expected return shape from policy_engine.enforce(intent).

    The agent reads this to decide whether to proceed with skill routing.
    Person 2 (enforcement layer) must return an object compatible with
    this shape (duck-typing is fine — exact class not required).

    Fields
    ------
    allowed : True = proceed to skill; False = block execution
    reason  : Human-readable explanation (populated when allowed=False)
    details : Optional structured metadata from the policy engine
    """

    allowed: bool
    reason: str = ""
    details: Optional[dict] = None

    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "details": self.details or {},
        }


# ─────────────────────────────────────────────
# Agent Response Model
# ─────────────────────────────────────────────


@dataclass
class AgentResponse:
    """
    Standardised response object returned by the agent for every request.

    status  : "success" | "blocked" | "error"
    intent  : The parsed intent (or None on hard parse failure)
    result  : Skill output (populated on success)
    reason  : Block / error message (populated on non-success)
    """

    status: str                        # "success" | "blocked" | "error"
    intent: Optional[Intent] = None
    result: Optional[dict] = None
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "intent": self.intent.to_dict() if self.intent else None,
            "result": self.result,
            "reason": self.reason,
        }

    @classmethod
    def success(cls, intent: Intent, result: dict) -> "AgentResponse":
        return cls(status="success", intent=intent, result=result)

    @classmethod
    def blocked(cls, intent: Intent, reason: str) -> "AgentResponse":
        return cls(status="blocked", intent=intent, reason=reason)

    @classmethod
    def error(cls, message: str, intent: Optional[Intent] = None) -> "AgentResponse":
        return cls(status="error", intent=intent, reason=message)