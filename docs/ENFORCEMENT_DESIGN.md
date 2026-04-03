# Enforcement Design

## Layer 2 – Policy Enforcement Architecture

Layer 2 sits between the AI reasoning output (Layer 1) and trade execution (Layer 3). Its sole responsibility is to **allow or block** a parsed trade intent based on declarative, auditable rules.

---

## Design Principles

1. **Default-deny** — if a rule cannot be evaluated, the trade is blocked.
2. **Declarative rules** — all policy lives in YAML files under `backend/layer2_enforcement/rules/`. No enforcement logic is hard-coded in business handlers.
3. **Composable checks** — each YAML file handles one concern. All checks run independently; the first failure blocks the trade.
4. **Immutable audit trail** — every decision (allow or block) is written to `audit_log.jsonl` before returning to the caller.

---

## Rule Files

| File | Concern | Block condition |
|---|---|---|
| `asset_restrictions.yaml` | Ticker whitelist | Ticker not in `allowed_tickers` list |
| `trade_limits.yaml` | Max order value | `quantity × price > max_order_value` |
| `exposure_limits.yaml` | Portfolio concentration | Position would exceed `max_exposure_pct` |
| `time_restrictions.yaml` | Market-hours gate | Order outside allowed window |
| `tool_permissions.yaml` | Agent tool calls | Tool not in `permitted_tools` |

---

## Enforcement Flow

```
ParsedIntent + AIClassification
        │
        ▼
[1] AI risk gate  ──── risk_level ∈ {high_risk, critical} ──→ BLOCK
        │ safe / low_risk
        ▼
[2] Ticker whitelist  ── ticker ∉ allowed_tickers ──────────→ BLOCK
        │ in list
        ▼
[3] Order value  ──── qty × price > $10,000 ────────────────→ BLOCK
        │ within limit
        ▼
[4] Exposure limit  ── would exceed 25 % portfolio ─────────→ BLOCK
        │ within limit
        ▼
[5] Time restriction  ── outside 09:30–16:00 ET ────────────→ BLOCK
        │ in window
        ▼
      ALLOW  →  Layer 3 Execution
```

---

## PolicyEnforcer Interface

```python
# backend/layer2_enforcement/enforcer.py
class PolicyEnforcer:
    def enforce(
        self,
        intent: ParsedIntent,
        classification: AIClassification,
    ) -> PolicyDecision:
        """
        Returns PolicyDecision(allowed=True|False, reason=str).
        Never raises — failures default to block.
        """
```

---

## Adding a New Rule

1. Create or edit the relevant YAML file in `rules/`.
2. Add a check method to `policy_engine.py`.
3. Register the check in `enforcer.py` (add to the check chain).
4. Write a test case in `backend/tests/`.
