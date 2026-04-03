# API Readiness Checklist

## API Quality Validation

Use this checklist before demo and submission to confirm the API is production-demo-ready.

---

## Timeouts & Retries

- [ ] OpenAI classification call has a timeout (default: 10 s, configurable via `OPENAI_TIMEOUT_SECONDS`)
- [ ] Alpaca order submission has a timeout (default: 5 s, configurable via `ALPACA_TIMEOUT_SECONDS`)
- [ ] OpenAI calls retry up to 2 times on `RateLimitError` with exponential backoff
- [ ] Alpaca order submission does NOT retry (prevents duplicate orders)
- [ ] Timeout exceeded → graceful fallback (`low_risk` classification or `status: error` response)

## Rate-Limit Behavior

- [ ] OpenAI `RateLimitError` is caught and retried with backoff
- [ ] After max retries, falls back to `low_risk` classification (not a crash)
- [ ] User-visible response indicates service degradation (`fallback: true` in classification)
- [ ] Alpaca rate-limit errors surface as HTTP 503 with a user-readable detail message

## Input Validation

- [ ] `instruction` field: required, non-empty string
- [ ] `user_id` field: optional, alphanumeric, max 64 chars
- [ ] `ticker` extracted by parser: uppercase, 1–5 chars, alphanumeric
- [ ] `quantity`: must be positive number (> 0)
- [ ] `price`: must be positive number (> 0) if provided
- [ ] `action`: must be one of `BUY`, `SELL`, `QUERY`, `UNKNOWN`
- [ ] Very long instructions (> 1,000 chars) truncated before AI call

## Structured Error Responses & Logs

- [ ] All errors return `{"status": "error", "reason": "<human-readable string>"}` (never a 500 traceback)
- [ ] Every request logs at `INFO` level: instruction received + final status
- [ ] Every error logs at `ERROR` level with full exception detail
- [ ] Audit log entry written for every trade decision (allow or block)
- [ ] `/api/audit/decisions` endpoint confirms audit entries are persisted

## Graceful No-Network / Offline Behavior

- [ ] If Alpaca is unreachable: `/health` returns `alpaca_connected: false`, API returns `status: error`
- [ ] All `/api/demo/*` endpoints work without network access (canned responses)
- [ ] If OpenAI is unreachable: classifier falls back to `low_risk`; Layer 2 still enforces
- [ ] Frontend (if applicable) shows "Service unavailable" message after 15 s timeout
- [ ] No unhandled exceptions crash the server under any tested error condition

---

## Quick Smoke Test

```bash
# 1. Health
curl http://localhost:8000/health

# 2. Policy
curl http://localhost:8000/api/policy

# 3. Safe trade
curl -X POST http://localhost:8000/api/trade \
  -H "Content-Type: application/json" \
  -d '{"instruction": "Buy 2 shares of MSFT at $430"}'

# 4. Demo endpoints
curl http://localhost:8000/api/demo/allowed-scenario
curl http://localhost:8000/api/demo/blocked-scenario-credential
curl http://localhost:8000/api/demo/blocked-scenario-threat

# 5. Audit log
curl http://localhost:8000/api/audit/decisions
```

All requests should return valid JSON with no 500 errors.
