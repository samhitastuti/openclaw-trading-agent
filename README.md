# OpenClaw Trading Agent

**Autonomous AI-powered trading agent with a 3-layer enforcement architecture that parses natural-language trade instructions, validates them against configurable policies, and executes only safe, compliant trades via Alpaca Markets.**

---

## Problem Statement

Retail and institutional traders risk executing unsafe or non-compliant trades when delegating decisions to AI agents — OpenClaw solves this by adding a rule-enforced safety layer between the AI and the brokerage.

## Success Metrics (MVP)

| Metric | Target |
|---|---|
| Safe trades allowed end-to-end | ≥ 5 happy-path scenarios pass |
| Unsafe trades blocked | 100 % of policy-violating instructions rejected |
| Audit log completeness | Every decision logged with reason |
| API response time (p95) | < 500 ms |

---

## Architecture Overview

```
User Instruction (natural language)
        │
        ▼
┌───────────────────────────────┐
│  Layer 1 – Reasoning          │  intent_parser + IntentClassifier (AI)
│  Parse & classify trade intent│  → ticker, action, quantity, risk score
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│  Layer 2 – Enforcement        │  PolicyEnforcer + YAML rules
│  Validate against policies    │  → allow / block + reason
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│  Layer 3 – Execution          │  AlpacaClient (paper trading)
│  Execute safe trades only     │  → order confirmed + audit log entry
└───────────────────────────────┘
```

**Tech Stack**
- **Backend**: Python 3.11 · FastAPI · Pydantic v2
- **AI/ML**: OpenAI GPT-4o (intent parsing + risk classification)
- **Brokerage**: Alpaca Markets (paper trading API)
- **Logging**: JSONL audit trail (`audit_log.jsonl`)
- **Frontend**: (see `frontend/` — Next.js)

---

## Setup Instructions

### Prerequisites
- Python 3.11+
- An [Alpaca paper-trading account](https://alpaca.markets) (free)
- An [OpenAI API key](https://platform.openai.com)

### 1 — Clone & install dependencies

```bash
git clone https://github.com/samhitastuti/openclaw-trading-agent.git
cd openclaw-trading-agent
pip install -r requirements.txt
```

### 2 — Configure environment

```bash
cp .env.example .env
# Edit .env and fill in your credentials:
#   ALPACA_API_KEY, ALPACA_SECRET_KEY, OPENAI_API_KEY
```

### 3 — Run the backend

```bash
python -m uvicorn backend.api.server:app --reload --port 8000
```

### 4 — Try the API

```bash
# Health check
curl http://localhost:8000/health

# Submit a trade instruction
curl -X POST http://localhost:8000/api/trade \
  -H "Content-Type: application/json" \
  -d '{"instruction": "Buy 2 shares of MSFT at $430", "user_id": "demo"}'
```

Interactive API docs: **http://localhost:8000/docs**

### 5 — Run tests

```bash
python -m pytest backend/tests/ -q
```

---

## Live Deployment

| Environment | URL |
|---|---|
| API (paper) | _See deployment notes — Alpaca paper mode only_ |
| API Docs | `http://<host>:8000/docs` |

> **Desktop & Mobile**: The FastAPI `/docs` UI is desktop-optimised. For mobile demos use the JSON API directly or the frontend Next.js app.

---

## Demo Instructions (Happy Path)

1. Start the server (`uvicorn backend.api.server:app --port 8000`)
2. Open `http://localhost:8000/docs`
3. Call `GET /api/demo/allowed-scenario` → expect `status: ALLOWED` for `Buy 2 MSFT`
4. Call `GET /api/demo/blocked-scenario-ticker` → expect `status: BLOCKED` (unauthorized ticker)
5. Call `GET /api/demo/blocked-scenario-credential` → expect `status: BLOCKED` (credential exposure)
6. Call `GET /api/audit/decisions` → confirm every decision was logged

See [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md) for full scripted walkthrough.

---

## Documentation

| Document | Description |
|---|---|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Deep-dive architecture & API contracts |
| [`docs/PROBLEM_DEFINITION.md`](docs/PROBLEM_DEFINITION.md) | Users, use cases, pain points, MVP scope |
| [`docs/IMPLEMENTATION.md`](docs/IMPLEMENTATION.md) | Core implementation walkthrough |
| [`docs/RESILIENCE.md`](docs/RESILIENCE.md) | Error handling, retries, fallback behavior |
| [`docs/ENFORCEMENT_DESIGN.md`](docs/ENFORCEMENT_DESIGN.md) | Layer 2 enforcement strategy |
| [`docs/INTENT_MODEL.md`](docs/INTENT_MODEL.md) | Intent parsing & validation |
| [`docs/POLICY_MODEL.md`](docs/POLICY_MODEL.md) | Policy enforcement rules |
| [`docs/SECURITY_CASES.md`](docs/SECURITY_CASES.md) | Security workflows & test cases |
| [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md) | 90s / 3-min pitch scripts |
| [`docs/SUBMISSION_CHECKLIST.md`](docs/SUBMISSION_CHECKLIST.md) | Pre-submission validation |
| [`docs/PITCH_TEMPLATES.md`](docs/PITCH_TEMPLATES.md) | Pitch structure & judge criteria |
| [`docs/MENTOR_QUESTIONS.md`](docs/MENTOR_QUESTIONS.md) | 10 mentor questions for design validation |
| [`docs/API_READINESS.md`](docs/API_READINESS.md) | API quality checklist |
| [`docs/SECURITY_CHECKS.md`](docs/SECURITY_CHECKS.md) | Security audit checklist |

---

## Team & Submission Links

- **Team**: samhitastuti
- **Repository**: https://github.com/samhitastuti/openclaw-trading-agent
- **Submission video**: _[add link before submission]_
- **Live demo**: _[add link before submission]_

