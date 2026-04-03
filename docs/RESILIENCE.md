# Resilience

## HOUR 13-24: Quality + Resilience

---

## Error States & Handling

| Error State | Detection | Response |
|---|---|---|
| Invalid instruction (empty / malformed) | `intent_validator.py` | `status: error`, HTTP 200 with reason |
| Unknown action extracted | `ParsedIntent.action == UNKNOWN` | Layer 2 defaults to block |
| OpenAI API timeout / failure | `try/except` in classifier | Fallback to `risk_level: low_risk`; trade proceeds to Layer 2 |
| Alpaca API unavailable | `alpaca_client is None` | `GET /health` returns `alpaca_connected: false`; demo endpoints still work |
| Policy rule file missing | YAML load in policy engine | Default-deny: trade blocked, error logged |
| Audit log write failure | `try/except` in audit_logger | Error logged to stdout; trade result still returned to client |
| Unexpected exception in handler | Outer `try/except` in server.py | `status: error`, reason surfaced to client, no crash |

---

## Loading States & Timeouts

### Backend API Timeouts

| Call | Timeout | Behaviour on timeout |
|---|---|---|
| OpenAI classification | 10 s | Catch `TimeoutError`; return `low_risk` fallback classification |
| Alpaca order submission | 5 s | Catch `TimeoutError`; return `status: error` with reason |
| Alpaca market data | 5 s | HTTP 503 with detail message |

Configure via environment:
```
OPENAI_TIMEOUT_SECONDS=10
ALPACA_TIMEOUT_SECONDS=5
```

### Frontend Loading States (Next.js)

- Trade submission shows spinner until response received.
- Timeout after 15 s shows user-facing error: "Service temporarily unavailable."

---

## Fallback Behavior

### OpenAI Unavailable

```python
try:
    classification = classifier.classify(instruction)
except Exception:
    # Fallback: assume low-risk, let policy layer decide
    classification = AIClassification(
        risk_level="low_risk",
        threat_flags=[],
        confidence=0.0,
        fallback=True,
    )
```

Policy enforcement still runs. Trades with explicit policy violations (wrong ticker, oversized order) are still blocked.

### Alpaca Unavailable

- `/api/trade` returns `status: error` with reason `"Alpaca client not connected"`.
- All `/api/demo/*` endpoints work without Alpaca (canned responses).
- `/api/account` and `/api/positions` return HTTP 503.

### Policy File Missing

- `PolicyEnforcer` catches YAML load errors.
- All trades are blocked with reason `"Policy configuration unavailable — default deny"`.

---

## API Retry Logic

### OpenAI (classifier)

```python
# Retry up to 2 times with exponential backoff
for attempt in range(3):
    try:
        return openai_client.chat.completions.create(...)
    except openai.RateLimitError:
        time.sleep(2 ** attempt)
raise  # propagate after 3 failures → fallback kicks in
```

### Alpaca (order submission)

- Single attempt; no automatic retry (prevent duplicate orders).
- On failure: error logged, `status: error` returned.

---

## Edge Cases Covered

| Edge Case | Handling |
|---|---|
| Instruction with no ticker | `ticker: null` in ParsedIntent; Layer 2 blocks (null not in whitelist) |
| Quantity of 0 or negative | IntentValidator rejects; `status: error` |
| Price of 0 or negative | IntentValidator rejects; `status: error` |
| Ticker in wrong case (e.g. `msft`) | Parser uppercases before whitelist check |
| Very long instruction (> 1,000 chars) | Truncated to 1,000 chars before AI call |
| Concurrent requests | FastAPI async handlers; each request is independent |
| Audit log doesn't exist yet | `FileNotFoundError` caught; returns empty list |
| Path traversal attempt in file API | `FileAccessController` rejects paths outside `outputs/` |
| Prompt injection in instruction | Layer 1 AI classifier detects and flags; Layer 2 blocks |
