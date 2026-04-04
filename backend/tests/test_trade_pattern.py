"""
test_trade_pattern.py — Unit tests for TRADE_PATTERN regex in constants.py.

Verifies that the regex correctly handles all supported trade input formats,
including "buy 10 MSFT" (direct ticker), "buy 10 shares of MSFT" (with
shares/units keyword), and optional price variants.

Run with:
    pytest backend/tests/test_trade_pattern.py -v
"""

from __future__ import annotations

import re

import pytest

from backend.config.constants import TRADE_PATTERN
from backend.intent.intent_parser import parse_intent, _resolve_ticker
from backend.intent.intent_models import ActionSide, IntentType


_RE_TRADE = re.compile(TRADE_PATTERN, re.IGNORECASE)


# ─────────────────────────────────────────────
# Regex-level tests
# ─────────────────────────────────────────────


@pytest.mark.parametrize(
    "instruction,expected_side,expected_qty,expected_ticker,expected_price",
    [
        # Direct ticker (no "shares of" keyword)
        ("buy 10 MSFT", "buy", "10", "MSFT", None),
        ("sell 5 TSLA", "sell", "5", "TSLA", None),
        # With price
        ("sell 5 TSLA at 150", "sell", "5", "TSLA", "150"),
        ("buy 2 AAPL at 200", "buy", "2", "AAPL", "200"),
        # With "shares" keyword (no "of")
        ("buy 10 shares MSFT", "buy", "10", "MSFT", None),
        ("sell 3 units TSLA", "sell", "3", "TSLA", None),
        # With "shares of" / "units of"
        ("buy 10 shares of MSFT", "buy", "10", "MSFT", None),
        ("sell 5 units of TSLA at 150", "sell", "5", "TSLA", "150"),
        # Case insensitive side
        ("Buy 10 MSFT", "Buy", "10", "MSFT", None),
        ("SELL 5 TSLA at 150", "SELL", "5", "TSLA", "150"),
        # Fractional quantity
        ("buy 2.5 NVDA at 450", "buy", "2.5", "NVDA", "450"),
    ],
)
def test_trade_pattern_matches(
    instruction, expected_side, expected_qty, expected_ticker, expected_price
):
    """TRADE_PATTERN should match the instruction and capture correct groups."""
    match = _RE_TRADE.search(instruction)
    assert match is not None, f"Pattern did not match: {instruction!r}"
    groups = match.groupdict()
    assert groups["side"].lower() == expected_side.lower()
    assert groups["quantity"] == expected_qty
    assert groups["ticker"] == expected_ticker
    assert groups["price"] == expected_price


@pytest.mark.parametrize(
    "instruction",
    [
        "analyze MSFT",
        "price of AAPL",
        "what is the price of AMZN",
        "hello world",
        "",
    ],
)
def test_trade_pattern_no_match(instruction):
    """TRADE_PATTERN should NOT match non-trade instructions."""
    match = _RE_TRADE.search(instruction)
    assert match is None, f"Pattern unexpectedly matched: {instruction!r}"


# ─────────────────────────────────────────────
# Intent-parser integration tests
# ─────────────────────────────────────────────


@pytest.mark.parametrize(
    "instruction,expected_side,expected_ticker",
    [
        # Direct ticker — key scenario from the bug report
        ("buy 10 MSFT", ActionSide.BUY, "MSFT"),
        ("sell 5 TSLA at 150", ActionSide.SELL, "TSLA"),
        # With "shares" keyword
        ("buy 10 shares MSFT", ActionSide.BUY, "MSFT"),
        # With "shares of"
        ("buy 10 shares of MSFT", ActionSide.BUY, "MSFT"),
        # With "units of"
        ("sell 5 units of TSLA at 150", ActionSide.SELL, "TSLA"),
    ],
)
def test_parse_intent_trade_formats(instruction, expected_side, expected_ticker):
    """parse_intent should correctly parse all supported trade input formats."""
    intent = parse_intent(instruction, user_id="tester")
    assert intent is not None, f"parse_intent returned None for: {instruction!r}"
    assert intent.type == IntentType.EXECUTE_TRADE
    assert intent.side == expected_side
    assert intent.ticker == expected_ticker


def test_parse_intent_direct_ticker_no_price():
    """'buy 10 MSFT' (simplest format) must parse as a market order."""
    intent = parse_intent("buy 10 MSFT", user_id="tester")
    assert intent is not None
    assert intent.ticker == "MSFT"
    assert intent.quantity == 10.0
    assert intent.side == ActionSide.BUY
    assert intent.price is None  # market order


def test_parse_intent_direct_ticker_with_price():
    """'sell 5 TSLA at 150' must parse with price captured."""
    intent = parse_intent("sell 5 TSLA at 150", user_id="tester")
    assert intent is not None
    assert intent.ticker == "TSLA"
    assert intent.quantity == 5.0
    assert intent.side == ActionSide.SELL
    assert intent.price == 150.0


# ─────────────────────────────────────────────
# Company name → ticker mapping
# ─────────────────────────────────────────────


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("MICROSOFT", "MSFT"),
        ("microsoft", "MSFT"),
        ("Microsoft", "MSFT"),
        ("APPLE", "AAPL"),
        ("apple", "AAPL"),
        ("NVIDIA", "NVDA"),
        ("AMAZON", "AMZN"),
        ("TESLA", "TSLA"),
        ("MSFT", "MSFT"),   # canonical symbol passes through unchanged
        ("AAPL", "AAPL"),
    ],
)
def test_resolve_ticker_company_names(raw, expected):
    """_resolve_ticker must map common company names to their ticker symbols."""
    assert _resolve_ticker(raw) == expected


# ─────────────────────────────────────────────
# End-to-end: "BUY 240 MICROSOFT" scenario
# ─────────────────────────────────────────────


def test_buy_240_microsoft_pattern_matches():
    """TRADE_PATTERN must match 'BUY 240 MICROSOFT' (company name, 9 chars)."""
    match = _RE_TRADE.search("BUY 240 MICROSOFT")
    assert match is not None, "Pattern did not match 'BUY 240 MICROSOFT'"
    groups = match.groupdict()
    assert groups["side"].lower() == "buy"
    assert groups["quantity"] == "240"
    assert groups["ticker"] == "MICROSOFT"


def test_parse_intent_buy_240_microsoft():
    """parse_intent must parse 'BUY 240 MICROSOFT' and map ticker to MSFT."""
    intent = parse_intent("BUY 240 MICROSOFT", user_id="tester")
    assert intent is not None, "parse_intent returned None for 'BUY 240 MICROSOFT'"
    assert intent.type == IntentType.EXECUTE_TRADE
    assert intent.side == ActionSide.BUY
    assert intent.ticker == "MSFT"
    assert intent.quantity == 240.0
    assert intent.price is None  # market order


@pytest.mark.parametrize(
    "instruction,expected_ticker,expected_qty",
    [
        ("BUY 240 MICROSOFT", "MSFT", 240.0),
        ("buy 100 Apple", "AAPL", 100.0),
        ("sell 50 nvidia", "NVDA", 50.0),
        ("BUY 10 AMAZON at 185", "AMZN", 10.0),
        ("sell 5 TESLA at 200", "TSLA", 5.0),
    ],
)
def test_parse_intent_company_name_inputs(instruction, expected_ticker, expected_qty):
    """parse_intent must correctly handle full company names as the ticker."""
    intent = parse_intent(instruction, user_id="tester")
    assert intent is not None, f"parse_intent returned None for: {instruction!r}"
    assert intent.ticker == expected_ticker, (
        f"Expected ticker={expected_ticker!r}, got {intent.ticker!r} for {instruction!r}"
    )
    assert intent.quantity == expected_qty
