# Security Checks

## Security Audit Checklist

Run this checklist before demo and submission.

---

## No Secrets Committed

- [ ] `.env` is listed in `.gitignore` and never tracked
- [ ] `audit_log.jsonl` is listed in `.gitignore`
- [ ] `git log --all --full-history -- .env` shows no commits containing `.env`
- [ ] `git grep -i "sk-"` returns no matches in tracked files
- [ ] `git grep -i "AKIA"` (AWS key pattern) returns no matches
- [ ] `.env.example` contains only placeholder values (e.g. `your_openai_api_key_here`)
- [ ] No API keys, tokens, or passwords in any `.py`, `.yaml`, `.json`, or `.md` file

```bash
# Quick secret scan
git grep -E "(sk-|AKIA|password\s*=|secret\s*=)" -- "*.py" "*.yaml" "*.json"
```

## Input Validation & Sanitisation

- [ ] `instruction` field is validated: non-empty, max length enforced (1,000 chars)
- [ ] `user_id` field is validated: alphanumeric, max 64 chars, no injection characters
- [ ] `ticker` is uppercased and matched against whitelist before any trade action
- [ ] `quantity` and `price` are validated as positive numbers before policy checks
- [ ] File path inputs in `/api/test/file-access/*` are validated by `FileAccessController`
- [ ] Path traversal (`../../etc/passwd`) is blocked: `GET /api/test/file-access/read/../../etc/passwd` → `allowed: false`

## Auth / Session Logic

- [ ] Sensitive routes (if any) are protected — document which routes require auth
- [ ] For MVP (no auth): document that all routes are internal/paper-trading only
- [ ] `user_id` in trade requests is logged but not trusted for privilege escalation
- [ ] No session tokens stored in audit log

## CORS Policy

- [ ] CORS is configured in `server.py` to restrict allowed origins
- [ ] In production, `allow_origins` must NOT be `["*"]`
- [ ] For local dev only, `["*"]` is acceptable with a comment noting the restriction

```python
# Example: restrict to frontend origin in production
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # tighten in production
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
```

## Audit Logging for Critical Actions

- [ ] Every `/api/trade` request is logged: instruction, user_id, ai_classification, policy_decision, timestamp
- [ ] All BLOCKED decisions are retrievable via `GET /api/audit/blocked`
- [ ] Audit log entries are append-only (no delete or overwrite logic)
- [ ] Audit log does NOT contain raw API keys, passwords, or secrets
- [ ] File access control decisions are logged when a path traversal is attempted

## Additional Security Hardening (Nice-to-Have)

- [ ] Request rate limiting implemented (prevent brute-force of the trade endpoint)
- [ ] Instruction length capped at server level (not just in parser)
- [ ] OpenAI prompt uses a system message that cannot be overridden by user input
- [ ] Dependency audit: `pip-audit` or `safety check` run on `requirements.txt`
