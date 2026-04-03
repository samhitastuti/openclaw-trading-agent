"""
intent_parser.py — Natural Language → Structured Intent converter.

Uses regex-based parsing (no LLM calls) to transform raw user strings
into typed Intent objects that the agent can enforce and route.

Supported input patterns (case-insensitive after normalisation):
  Trade  : "buy 10 shares of AAPL"
           "sell 5 TSLA"
           "buy 2.5 NVDA at 450"
           "sell 100 SPY at 420.50"
  Analyze: "analyze MSFT"
           "analysis of AAPL"
           "check fundamentals of GOOGL"
  Fetch  : "price of GOOGL"
           "get TSLA price"
           "what is the price of AMZN"
           "quote for SPY"
           "fetch data for AMD"
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from backend.config.constants import (
    ANALYZE_PATTERN,
    FETCH_PRICE_PATTERN,
    SUPPORTED_TICKERS,
    TRADE_PATTERN,
)
from .intent_models import ActionSide, Intent, IntentType

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Compiled Regex Cache
# (Compiled once at import time for efficiency)
# ─────────────────────────────────────────────

_RE_TRADE = re.compile(TRADE_PATTERN, re.IGNORECASE)
_RE_ANALYZE = re.compile(ANALYZE_PATTERN, re.IGNORECASE)
_RE_FETCH = re.compile(FETCH_PRICE_PATTERN, re.IGNORECASE)


# ─────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────


def parse_intent(raw_input: str, user_id: str = "anonymous") -> Optional[Intent]:
    """
    Convert a raw user string into a structured Intent.

    Parameters
    ----------
    raw_input : The original, unmodified user text.
    user_id   : Identifier of the requesting user (threaded through to audit).

    Returns
    -------
    Intent    : A fully populated Intent object on success.
    None      : If no pattern matches (caller should surface a helpful error).

    Notes
    -----
    - Normalisation (strip + upper-case ticker extraction) happens internally.
    - raw_input is preserved verbatim in Intent.raw_input for auditing.
    - Ticker validation is performed: unrecognised tickers return None so the
      agent can give a clear "unsupported ticker" message instead of routing
      to enforcement with garbage data.
    """
    if not raw_input or not raw_input.strip():
        logger.debug("parse_intent: empty input received")
        return None

    stripped = raw_input.strip()

    # ── Attempt 1: Trade intent ────────────────
    intent = _try_parse_trade(stripped, user_id)
    if intent:
        return intent

    # ── Attempt 2: Analyze intent ─────────────
    intent = _try_parse_analyze(stripped, user_id)
    if intent:
        return intent

    # ── Attempt 3: Fetch / price intent ────────
    intent = _try_parse_fetch(stripped, user_id)
    if intent:
        return intent

    logger.info("parse_intent: no pattern matched for input: %r", stripped[:80])
    return None


# ─────────────────────────────────────────────
# Private Parsers
# ─────────────────────────────────────────────


def _try_parse_trade(raw: str, user_id: str) -> Optional[Intent]:
    """
    Match BUY / SELL patterns.

    Expected captures:
      side     : "buy" | "sell"
      quantity : numeric string (int or float)
      ticker   : uppercase symbol
      price    : optional numeric string
    """
    match = _RE_TRADE.search(raw)
    if not match:
        return None

    groups = match.groupdict()

    side_str = groups["side"].upper()
    side = ActionSide.BUY if side_str == "BUY" else ActionSide.SELL

    ticker = groups["ticker"].upper()
    if not _is_valid_ticker(ticker):
        logger.warning("parse_intent: unsupported ticker %r in trade", ticker)
        return None

    try:
        quantity = float(groups["quantity"])
    except (TypeError, ValueError):
        logger.warning("parse_intent: invalid quantity %r", groups.get("quantity"))
        return None

    if quantity <= 0:
        logger.warning("parse_intent: non-positive quantity %s", quantity)
        return None

    price: Optional[float] = None
    if groups.get("price"):
        try:
            price = float(groups["price"])
        except (TypeError, ValueError):
            price = None  # Treat as market order if price unparseable

    return Intent(
        type=IntentType.EXECUTE_TRADE,
        ticker=ticker,
        quantity=quantity,
        side=side,
        price=price,
        raw_input=raw,
        user_id=user_id,
    )


def _try_parse_analyze(raw: str, user_id: str) -> Optional[Intent]:
    """
    Match ANALYZE patterns.

    Expected captures:
      ticker : uppercase symbol
    """
    match = _RE_ANALYZE.search(raw)
    if not match:
        return None

    ticker = match.group("ticker").upper()
    if not _is_valid_ticker(ticker):
        logger.warning("parse_intent: unsupported ticker %r in analyze", ticker)
        return None

    return Intent(
        type=IntentType.ANALYZE,
        ticker=ticker,
        quantity=0.0,
        side=ActionSide.NONE,
        price=None,
        raw_input=raw,
        user_id=user_id,
    )


def _try_parse_fetch(raw: str, user_id: str) -> Optional[Intent]:
    """
    Match FETCH_DATA / price-quote patterns.

    Uses multiple named groups (ticker1..ticker5) — only one fires per match.
    """
    match = _RE_FETCH.search(raw)
    if not match:
        return None

    groups = match.groupdict()
    raw_ticker = next(
        (v for k, v in groups.items() if k.startswith("ticker") and v is not None),
        None,
    )
    if raw_ticker is None:
        return None

    ticker = raw_ticker.upper()
    if not _is_valid_ticker(ticker):
        logger.warning("parse_intent: unsupported ticker %r in fetch", ticker)
        return None

    return Intent(
        type=IntentType.FETCH_DATA,
        ticker=ticker,
        quantity=0.0,
        side=ActionSide.NONE,
        price=None,
        raw_input=raw,
        user_id=user_id,
    )


# ─────────────────────────────────────────────
# Validation Helpers
# ─────────────────────────────────────────────


def _is_valid_ticker(ticker: str) -> bool:
    """
    Return True if the ticker is in the supported list.
    Enforcement may impose further restrictions; this is a first-pass
    sanity check to avoid routing nonsense to the policy engine.
    """
    return ticker in SUPPORTED_TICKERS


# ─────────────────────────────────────────────
# Convenience wrapper (for testing / REPL use)
# ─────────────────────────────────────────────


def parse_or_raise(raw_input: str, user_id: str = "anonymous") -> Intent:
    """
    Like parse_intent() but raises ValueError on failure instead of
    returning None. Useful in test scenarios.
    """
    result = parse_intent(raw_input, user_id)
    if result is None:
        raise ValueError(
            f"Could not parse intent from input: {raw_input!r}"
        )
    return result