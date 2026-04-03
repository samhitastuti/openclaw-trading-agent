# Policy Model

## Policy Enforcement Rules

All policy constraints are declared in YAML files under `backend/layer2_enforcement/rules/`. The `PolicyEnforcer` loads and evaluates them at request time.

---

## Active Policy: `analyst_policy_v1`

### 1. Ticker Whitelist (`asset_restrictions.yaml`)

```yaml
allowed_tickers:
  - MSFT
  - AAPL
  - GOOGL
  - AMZN
  - NVDA
```

- Any ticker not in this list → **BLOCK**
- Case-insensitive match at parse time.

### 2. Maximum Order Value (`trade_limits.yaml`)

```yaml
max_order_value: 10000   # USD
```

- `quantity × price > 10,000` → **BLOCK**
- For market orders without price, uses last-known bid.

### 3. Portfolio Exposure Limit (`exposure_limits.yaml`)

```yaml
max_exposure_pct: 0.25   # 25% of portfolio value per single position
```

- Adding the new position would exceed 25% → **BLOCK**

### 4. Market Hours Gate (`time_restrictions.yaml`)

```yaml
allowed_window:
  start: "09:30"
  end: "16:00"
  timezone: "America/New_York"
  days: [MON, TUE, WED, THU, FRI]
```

- Orders outside the window → **BLOCK**

### 5. AI Risk Threshold

Applied directly in `PolicyEnforcer`, not in a YAML file:

```python
AI_RISK_THRESHOLD = 0.8  # block if AI confidence of risk >= 0.8
BLOCK_LEVELS = {"high_risk", "critical"}
```

- `risk_level ∈ {high_risk, critical}` → **BLOCK**

---

## PolicyDecision Model

```python
@dataclass
class PolicyDecision:
    allowed: bool
    reason: str          # human-readable explanation logged to audit trail
    rule_id: str | None  # which rule triggered the block
    metadata: dict       # additional context
```

---

## Extending the Policy

To add a new constraint:

1. Add a new YAML file (or extend existing) in `rules/`.
2. Implement a check in `backend/layer2_enforcement/policy_engine.py`.
3. Register it in `enforcer.py` enforcement chain.
4. Add a test in `backend/tests/test_api_endpoints.py`.
5. Document in this file.

---

## Policy Audit Trail

Every enforcement decision is persisted:

```jsonl
{"timestamp": "2026-04-03T16:00:00Z", "user": "analyst_001", "instruction": "...",
 "ai_classification": {...}, "policy_decision": {"allowed": false, "reason": "..."}}
```

See `GET /api/audit/decisions` and `GET /api/audit/blocked`.
