# Submission Checklist

## HOUR 25-36: Demo + Submission Validation

---

## README Validation

- [ ] README includes a one-sentence problem statement
- [ ] README has a success metrics table
- [ ] README has an architecture overview (text diagram or image)
- [ ] README has step-by-step setup instructions (clone → install → configure → run)
- [ ] README has a live deployment link or clear instructions to run locally
- [ ] README has demo instructions (happy path walkthrough)
- [ ] README has team names and submission links
- [ ] README links to all `docs/` files

---

## Live Deployment Verification

- [ ] Server starts cleanly: `uvicorn backend.api.server:app --port 8000`
- [ ] `GET /health` returns `{"status": "healthy"}`
- [ ] `GET /api/policy` returns the active constraint list
- [ ] `GET /api/demo/allowed-scenario` returns `status: ALLOWED`
- [ ] `GET /api/demo/blocked-scenario-credential` returns `status: BLOCKED`
- [ ] `GET /api/demo/blocked-scenario-threat` returns `status: BLOCKED`
- [ ] `GET /api/audit/decisions` returns at least 1 logged entry after demo runs
- [ ] API docs accessible at `http://<host>:8000/docs`
- [ ] Desktop browser: all endpoints work without layout issues
- [ ] Mobile browser: JSON API responses readable (no broken UI)

---

## Environment Variables Documentation

All required environment variables must be present in `.env.example` with placeholder values only — no real secrets.

| Variable | Required | Description |
|---|---|---|
| `ALPACA_API_KEY` | Yes | Alpaca paper-trading API key |
| `ALPACA_SECRET_KEY` | Yes | Alpaca paper-trading secret key |
| `ALPACA_BASE_URL` | Yes | `https://paper-api.alpaca.markets` |
| `OPENAI_API_KEY` | Yes | OpenAI API key for intent classification |
| `SERVER_HOST` | No | Default `0.0.0.0` |
| `SERVER_PORT` | No | Default `8000` |
| `LOG_LEVEL` | No | Default `INFO` |
| `AUDIT_LOG_FILE` | No | Default `audit_trail.jsonl` |
| `ALLOWED_OUTPUT_DIR` | No | Default `outputs/` |

- [ ] `.env.example` contains all variables above
- [ ] `.env.example` contains NO real API keys or secrets
- [ ] `.env` is listed in `.gitignore`
- [ ] `audit_log.jsonl` is listed in `.gitignore`

---

## Security Pre-Submission Check

- [ ] `git log --all --full-history -- .env` shows `.env` was never committed
- [ ] `grep -r "sk-" .` returns no matches in tracked files
- [ ] No hardcoded credentials in any `.py` or `.yaml` file
- [ ] `GET /api/test/file-access/read/../../etc/passwd` returns `allowed: false`

---

## Video & Link Verification

- [ ] Demo video recorded (3 minutes max)
- [ ] Video shows: problem statement → allowed trade → blocked trade → audit log
- [ ] Video link is publicly accessible (YouTube unlisted or Loom)
- [ ] Submission form completed with correct repository URL
- [ ] All links tested in incognito window (no auth required)

---

## 3-Minute Team Pitch Structure

1. **(0:00 – 0:30)** State the problem in one sentence. Who is affected and why it matters.
2. **(0:30 – 1:15)** Explain the 3-layer solution: Reason → Enforce → Execute. Show the architecture briefly.
3. **(1:15 – 2:15)** Live demo: 1 allowed trade + 1 blocked threat + audit log.
4. **(2:15 – 2:45)** Technical depth: YAML-driven policies, AI fallback, immutable audit trail.
5. **(2:45 – 3:00)** Impact: 100 % block rate, compliance-ready, extensible.

---

## Final Go / No-Go

- [ ] All tests pass: `python -m pytest backend/tests/ -q`
- [ ] Server starts without errors
- [ ] Demo endpoints all return expected responses
- [ ] Audit log captures all decisions
- [ ] No secrets in git history
- [ ] Submission form submitted
- [ ] Team is ready to explain problem, solution, and impact in < 3 minutes
