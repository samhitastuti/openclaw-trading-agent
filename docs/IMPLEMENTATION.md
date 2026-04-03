# Implementation

## HOUR 4-12: Core Implementation

---

## Architecture Diagram (Text-Based)

```
┌──────────────────────────────────────────────────────────────────────┐
│  CLIENT (curl / frontend / demo browser)                             │
└────────────────────────────┬─────────────────────────────────────────┘
                             │  POST /api/trade
                             │  {"instruction": "...", "user_id": "..."}
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│  FastAPI  (backend/api/server.py)                                    │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  LAYER 1 – REASONING                                         │    │
│  │                                                              │    │
│  │  intent_parser()  ──────────→  ParsedIntent                  │    │
│  │    • regex extraction                                        │    │
│  │    • action / ticker / qty / price                           │    │
│  │                                                              │    │
│  │  IntentClassifier.classify()  ──→  AIClassification          │    │
│  │    • GPT-4o structured prompt                                │    │
│  │    • risk_level / threat_flags / confidence                  │    │
│  └──────────────────────────┬───────────────────────────────────┘    │
│                             │                                        │
│  ┌──────────────────────────▼───────────────────────────────────┐    │
│  │  LAYER 2 – ENFORCEMENT                                       │    │
│  │                                                              │    │
│  │  PolicyEnforcer.enforce()                                    │    │
│  │    [1] AI risk gate  (high_risk / critical → BLOCK)          │    │
│  │    [2] Ticker whitelist  (asset_restrictions.yaml)           │    │
│  │    [3] Order value limit  (trade_limits.yaml)                │    │
│  │    [4] Exposure limit  (exposure_limits.yaml)                │    │
│  │    [5] Market hours  (time_restrictions.yaml)                │    │
│  │                                                              │    │
│  │  → PolicyDecision(allowed: bool, reason: str)                │    │
│  └──────────────────────────┬───────────────────────────────────┘    │
│                             │  if allowed                            │
│  ┌──────────────────────────▼───────────────────────────────────┐    │
│  │  LAYER 3 – EXECUTION                                         │    │
│  │                                                              │    │
│  │  AlpacaClient.submit_order()  (paper trading)                │    │
│  │  AuditLogger.log_trade_decision()  → audit_log.jsonl         │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  → TradeResponse  {status, intent, ai_classification,                │
│                    policy_decision, reason, timestamp}               │
└──────────────────────────────────────────────────────────────────────┘
```

---

## API Contracts

### POST /api/trade

**Request schema**
```json
{
  "instruction": "string (required) — natural language trade instruction",
  "user_id":    "string (optional) — caller identity for audit log"
}
```

**Response schema**
```json
{
  "status":            "success | blocked | error",
  "instruction":       "string",
  "intent":            { "action": "BUY|SELL", "ticker": "...", "quantity": 0, "price": 0.0 },
  "ai_classification": { "risk_level": "safe|low_risk|high_risk|critical", "threat_flags": [], "confidence": 0.0 },
  "policy_decision":   { "allowed": true, "reason": "string" },
  "reason":            "string (top-level shortcut to policy reason)",
  "timestamp":         "ISO 8601"
}
```

### GET /api/policy

Returns the active policy constraint list.

### GET /api/audit/decisions?limit=100

Returns the last N audit log entries.

### GET /api/audit/blocked

Returns only blocked decisions.

### GET /health

```json
{ "status": "healthy", "timestamp": "...", "alpaca_connected": true }
```

---

## Core Flow Walkthrough

```
Step 1  Client sends POST /api/trade {"instruction": "Buy 2 MSFT at $430"}

Step 2  server.py calls intent_parser("Buy 2 MSFT at $430", "user_001")
        → ParsedIntent(action=BUY, ticker=MSFT, quantity=2, price=430.0)

Step 3  server.py calls IntentClassifier.classify("Buy 2 MSFT at $430")
        → AIClassification(risk_level=safe, threat_flags=[], confidence=0.97)

Step 4  server.py calls PolicyEnforcer.enforce(parsed_intent, classification)
        Check 1: risk safe → pass
        Check 2: MSFT in whitelist → pass
        Check 3: 2 × $430 = $860 < $10,000 → pass
        Check 4: exposure within 25 % → pass
        Check 5: within market hours → pass
        → PolicyDecision(allowed=True, reason="All policy checks passed")

Step 5  AlpacaClient.submit_order(ticker=MSFT, qty=2, side=buy, type=limit, price=430)
        → Alpaca paper order accepted

Step 6  log_trade_decision(instruction, classification, decision, user)
        → Appended to audit_log.jsonl

Step 7  Return TradeResponse(status="success", ...)
```

---

## Stable Baseline Features

| Feature | Status | Notes |
|---|---|---|
| Intent parsing (regex) | ✅ Stable | No external dependency |
| AI risk classification | ✅ Stable | Falls back to `low_risk` if OpenAI unavailable |
| Policy enforcement | ✅ Stable | Pure Python + YAML, deterministic |
| Audit logging | ✅ Stable | JSONL append-only |
| Alpaca integration | ✅ Stable | Paper trading only |
| Health endpoint | ✅ Stable | No dependencies |
| Demo endpoints | ✅ Stable | Canned scenarios, no Alpaca required |

---

## Basic Logging Strategy

| Log type | Location | Format | Content |
|---|---|---|---|
| Application logs | stdout / stderr | Structured text (`logging`) | Request lifecycle, errors |
| Audit trail | `audit_log.jsonl` | JSONL (one entry per line) | Every trade decision |
| Decision log | `audit_log.jsonl` | JSONL | AI classification + policy result |

**Log levels**: `DEBUG` (dev) · `INFO` (default) · `WARNING` (anomalies) · `ERROR` (failures)

Set via `LOG_LEVEL` environment variable.

**Audit log entry format**
```jsonl
{
  "timestamp": "2026-04-03T16:00:00Z",
  "user": "analyst_001",
  "instruction": "Buy 2 MSFT at $430",
  "ai_classification": {"risk_level": "safe", "threat_flags": [], "confidence": 0.97},
  "policy_decision": {"allowed": true, "reason": "All policy checks passed"}
}
```
