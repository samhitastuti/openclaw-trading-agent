"""
constants.py — Global constants for the OpenClaw Reasoning Layer.

Defines input limits, supported tickers, and adversarial detection keywords.
These are configuration values ONLY — no business logic lives here.
"""

# ─────────────────────────────────────────────
# Input Validation
# ─────────────────────────────────────────────

# Maximum allowed length of a raw user input string
MAX_INPUT_LENGTH: int = 512

# ─────────────────────────────────────────────
# Supported Tickers
# (Enforcement layer may impose further restrictions)
# ─────────────────────────────────────────────

SUPPORTED_TICKERS: set[str] = {
    # Tech
    "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "META", "NVDA", "TSLA",
    "AMD", "INTC", "ORCL", "IBM", "CRM", "ADBE", "NFLX", "PYPL",
    # Finance
    "JPM", "GS", "BAC", "WFC", "MS", "C", "BLK",
    # Healthcare
    "JNJ", "PFE", "UNH", "ABBV", "MRK",
    # Energy
    "XOM", "CVX", "COP",
    # ETFs
    "SPY", "QQQ", "IWM", "DIA", "VTI", "GLD", "SLV",
    # Indices (read-only / analysis)
    "BTC", "ETH",
}

# ─────────────────────────────────────────────
# Adversarial / Prompt Injection Detection
# Inputs containing ANY of these keywords are
# immediately rejected before intent parsing.
# ─────────────────────────────────────────────

SUSPICIOUS_KEYWORDS: set[str] = {
    # Credential exfiltration
    "api_key",
    "apikey",
    "api-key",
    "password",
    "passwd",
    "secret",
    "token",
    "auth_token",
    "access_token",
    "refresh_token",
    "private_key",
    "bearer",
    # Prompt injection patterns
    "ignore previous",
    "ignore all",
    "disregard",
    "override",
    "jailbreak",
    "system prompt",
    "forget instructions",
    "new instructions",
    "you are now",
    "act as",
    # Injection via encoding hints
    "base64",
    "eval(",
    "exec(",
    "__import__",
    # Exfil / network
    "curl ",
    "wget ",
    "http://",
    "https://",
    "ftp://",
    # Filesystem traversal
    "../",
    "/etc/passwd",
    "/proc/",
}

# ─────────────────────────────────────────────
# Regex Patterns (used by intent_parser)
# ─────────────────────────────────────────────

# Matches: "buy 10 AAPL", "buy 10 shares AAPL", "buy 10 shares of AAPL",
#          "BUY 10 AAPL at 150", "sell 5 units MSFT at 300",
#          "sell 5 TSLA at 150", "BUY 240 MICROSOFT"
# Ticker group allows up to 15 characters to accommodate full company names
# such as "MICROSOFT" (9) or "SALESFORCE" (10) that users may type instead
# of the canonical symbol.  The intent_parser maps these to real symbols.
TRADE_PATTERN: str = (
    r"(?P<side>buy|sell)\s+"
    r"(?P<quantity>\d+(?:\.\d+)?)\s+"
    r"(?:(?:shares?|units?)\s+(?:of\s+)?)?"
    r"(?P<ticker>[A-Z]{1,15})\b"
    r"(?:\s+at\s+(?P<price>\d+(?:\.\d+)?))?"
)

# Matches: "analyze MSFT", "analysis of AAPL", "analyze Microsoft"
ANALYZE_PATTERN: str = (
    r"(?:analyze|analysis\s+of|analyse|check\s+fundamentals\s+of)\s+"
    r"(?P<ticker>[A-Z]{1,15})"
)

# Matches: "price of GOOGL", "get TSLA price", "what is the price of AMZN"
FETCH_PRICE_PATTERN: str = (
    r"(?:"
    r"(?:get\s+(?:the\s+)?)?price\s+of\s+(?P<ticker1>[A-Z]{1,15})"          # price of X / get price of X
    r"|what(?:\s+is)?\s+the\s+price\s+of\s+(?P<ticker2>[A-Z]{1,15})"        # what is the price of X
    r"|get\s+(?P<ticker3>[A-Z]{1,15})\s+price"                               # get X price
    r"|quote\s+(?:for\s+)?(?P<ticker4>[A-Z]{1,15})"                          # quote for X
    r"|fetch\s+(?:data\s+for\s+)?(?P<ticker5>[A-Z]{1,15})"                   # fetch data for X
    r")"
)

# ─────────────────────────────────────────────
# Skill Route Keys
# (Must match the keys used in agent.py skill registry)
# ─────────────────────────────────────────────

SKILL_TRADE: str = "trading_skill"
SKILL_ANALYZE: str = "analysis_skill"
SKILL_MARKET_DATA: str = "market_data_skill"