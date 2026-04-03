# Pitch Templates

## 90-Second Structure

| Segment | Time | Content |
|---|---|---|
| Problem | 0:00 – 0:20 | One sentence: who is affected, what goes wrong, why it matters |
| Solution | 0:20 – 0:55 | How OpenClaw solves it — 3-layer architecture in plain language |
| Demo Proof | 0:55 – 1:20 | Show 1 allowed + 1 blocked trade live or on screen |
| Impact | 1:20 – 1:30 | One concrete metric + what's next |

**Template**

> **Problem (20s):** "AI trading agents are powerful but unguarded — a single bad instruction or prompt-injection attack can cause catastrophic financial damage."
>
> **Solution (35s):** "OpenClaw adds a 3-layer safety net. Layer 1 parses and classifies intent with GPT-4o. Layer 2 enforces strict declarative policies — ticker whitelists, order limits, risk thresholds. Layer 3 executes only if both layers approve. Every decision is logged."
>
> **Demo Proof (25s):** _(show live demo)_ "Safe trade — allowed. Credential attack — blocked. Audit trail — complete."
>
> **Impact (10s):** "100 % of policy violations blocked in testing. Built in 36 hours. Extensible to any brokerage."

---

## 180-Second Structure

| Segment | Time | Content |
|---|---|---|
| Problem | 0:00 – 0:30 | Pain point, who is affected, quantified if possible |
| Why Now | 0:30 – 0:50 | Regulatory tailwinds, market timing, urgency |
| Architecture | 0:50 – 1:25 | 3-layer diagram walkthrough |
| Demo | 1:25 – 2:25 | Happy path + 2 blocked scenarios + audit log |
| Impact + Roadmap | 2:25 – 3:00 | Metric + 2–3 roadmap items |

**Template**

> **Problem (30s):** "Financial AI agents are increasingly autonomous — but there is no safety layer between the AI model and the brokerage. Regulators are watching. A misconfigured policy or a prompt-injection attack can cause a catastrophic, irreversible trade."
>
> **Why Now (20s):** "Regulatory pressure on algorithmic trading is rising. SEC and FINRA are increasing scrutiny of AI-generated orders. The market for compliant, auditable AI trading infrastructure is opening right now."
>
> **Architecture (35s):** "We built OpenClaw with three layers. Layer 1 — Reasoning: GPT-4o parses your instruction and scores it for risk. Layer 2 — Enforcement: a deterministic policy engine checks a YAML-driven ruleset. Layer 3 — Execution: only approved orders reach Alpaca. Every decision writes to an immutable audit log."
>
> **Demo (60s):** _(live demo: allowed trade → credential attack blocked → policy bypass blocked → audit log)_
>
> **Impact + Roadmap (35s):** "100 % of unsafe instructions blocked. Full audit trail. Roadmap: per-user policy profiles, real-time exposure monitoring, and a compliance dashboard."

---

## What Judges Look For

### Problem Clarity
> Clear user pain and why it matters.

**Self-check:** Can a judge repeat your problem in one sentence after your pitch?

### Technical Depth
> Strong architecture and implementation choices, with trade-offs explained.

**Self-check:** Did you explain *why* you chose YAML-driven policies over hard-coded logic? Why GPT-4o for classification?

### Execution Quality
> Working demo, reliable flow, polished UX.

**Self-check:** Does your core happy path work without manual fixes or refreshes?

### Impact
> Measurable value or meaningful outcome.

**Self-check:** Do you have one concrete impact metric? (e.g., "100 % block rate on policy violations")

### Presentation
> Crisp storytelling and confident demo.

**Self-check:** Can your entire team pitch in under 3 minutes, clearly, without reading from notes?

---

## Self-Check Questions

1. Can a non-technical judge understand the problem from your opening sentence?
2. Is your architecture diagram simple enough to explain in 30 seconds?
3. Does your demo flow work end-to-end without manual intervention?
4. Do you have a single, memorable impact number?
5. Can every team member answer "what problem does this solve?" in one sentence?
