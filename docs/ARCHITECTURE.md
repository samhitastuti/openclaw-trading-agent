# Architecture

## System Overview

OpenClaw Trading Agent is a 3-layer autonomous trading system that accepts natural-language instructions, enforces configurable safety policies, and executes compliant orders via Alpaca Markets.

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENT                               │
│   REST calls  /api/trade · /api/demo/* · /api/audit/*       │
└──────────────────────────┬──────────────────────────────────┘
                           │  HTTP (FastAPI)
┌──────────────────────────▼──────────────────────────────────┐
│                   LAYER 1 – REASONING                       │
│  intent_parser()  →  parsed ticker / action / quantity      │
│  IntentClassifier (AI)  →  risk_level + threat_flags        │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                   LAYER 2 – ENFORCEMENT                     │
│  PolicyEnforcer  →  checks YAML rules                       │
│    • asset_restrictions.yaml  (ticker whitelist)            │
│    • trade_limits.yaml        (max order value)             │
│    • exposure_limits.yaml     (portfolio exposure)          │
│    • time_restrictions.yaml   (market-hours gate)           │
│    • tool_permissions.yaml    (allowed tool calls)          │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                   LAYER 3 – EXECUTION                       │
│  AlpacaClient  →  paper-trading order (if ALLOWED)          │
│  AuditLogger   →  append to audit_log.jsonl                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Map

| Path | Role |
|---|---|
| `backend/api/server.py` | FastAPI app, route handlers |
| `backend/api/schemas.py` | Pydantic request/response models |
| `backend/intent/intent_parser.py` | NLP → structured `ParsedIntent` |
| `backend/intent/intent_models.py` | Domain models (`ParsedIntent`, `AgentResponse`) |
| `backend/intent/intent_validator.py` | Pre-enforcement input validation |
| `backend/layer1_reasoning/classifier.py` | AI risk classifier |
| `backend/layer2_enforcement/enforcer.py` | Policy enforcement entry point |
| `backend/layer2_enforcement/policy_engine.py` | Rule evaluation engine |
| `backend/layer2_enforcement/policy_models.py` | Policy data models |
| `backend/layer2_enforcement/rules/*.yaml` | Declarative policy rules |
| `backend/integrations/alpaca_client.py` | Alpaca Markets API wrapper |
| `backend/logging/audit_logger.py` | JSONL audit log writer |
| `backend/security/file_access_controller.py` | File-system boundary enforcement |

---

## API Contracts

### POST /api/trade

**Request**
```json
{
  "instruction": "Buy 10 shares of MSFT at $430",
  "user_id": "analyst_001"
}
```

**Response – ALLOWED**
```json
{
  "status": "success",
  "instruction": "Buy 10 shares of MSFT at $430",
  "intent": {
    "action": "BUY",
    "ticker": "MSFT",
    "quantity": 10,
    "price": 430.0
  },
  "ai_classification": {
    "risk_level": "safe",
    "threat_flags": [],
    "confidence": 0.97
  },
  "policy_decision": {
    "allowed": true,
    "reason": "All policy checks passed"
  },
  "timestamp": "2026-04-03T16:00:00Z"
}
```

**Response – BLOCKED**
```json
{
  "status": "blocked",
  "instruction": "Buy 10 shares of XYZ at $50",
  "policy_decision": {
    "allowed": false,
    "reason": "Ticker XYZ is not in the authorised whitelist"
  },
  "timestamp": "2026-04-03T16:00:01Z"
}
```

### GET /api/policy

Returns current active `PolicyConstraint` list (ticker whitelist, size limits, risk thresholds).

### GET /api/audit/decisions

Returns last N audit log entries from `audit_log.jsonl`.

### GET /api/audit/blocked

Returns only BLOCKED decisions — compliance report.

---

## Data Flow (Core Happy Path)

```
1. POST /api/trade  {"instruction": "Buy 2 MSFT at $430"}
2. intent_parser()  →  ParsedIntent(action=BUY, ticker=MSFT, qty=2, price=430)
3. IntentClassifier →  risk=safe, flags=[]
4. PolicyEnforcer   →  check ticker whitelist ✅  check order value ✅  check exposure ✅
5. AlpacaClient     →  submit_order(MSFT, qty=2, side=buy) [paper]
6. AuditLogger      →  append entry to audit_log.jsonl
7. HTTP 200         →  {status: "success", ...}
```
