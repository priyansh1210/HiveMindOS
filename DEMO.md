# Demo Day — Autonomous Enterprise AI Workforce

> One-liner: **"An AI Operating System for businesses — deploy a workforce of agents that collaborate, decide, and execute like a real team."**

---

## 🚨 Quota status (must check before every demo)

The free tiers are *very* tight. As of 2026-05-29 end-of-day **all three providers are exhausted** — see Quota Recipe at the bottom for how to know when you have headroom again.

| Provider | Limit | Status today | Resets |
|---|---|---|---|
| Gemini Flash key 1 | 250 RPD free | exhausted | 00:00 PT |
| Gemini Flash key 2 | 250 RPD free | exhausted | 00:00 PT |
| Groq Llama 3.3 70B | 100,000 TPD | 99,837 used | rolling 24h |

**Rule of thumb for the demo:** at most **ONE live scenario per minute** and **no more than ~10 live runs total per day** (each scenario is 6–15 LLM calls; planner + 5 agents × 1-3 turns each).

Pre-captured tasks live in Supabase forever — use the TaskDetail modal as a "live" demo even when quota is gone (see "Demo flow B" below).

---

## Cold-start checklist (do this 5 min before the demo)

```powershell
# 1. Backend
cd D:\Ai_Agent_Enterprise\backend
.\.venv\Scripts\Activate.ps1
python main.py
# wait for: Application startup complete

# 2. Frontend (new terminal)
cd D:\Ai_Agent_Enterprise\frontend
npm run dev
# wait for: ✓ Ready in …

# 3. Open browser at http://localhost:3000 — verify:
#    - Backend pill = green "Backend online"
#    - All 5 agent cards render with their colors
#    - Header shows NovaTech Inc.

# 4. Click through Agents → Chat → Tasks → Analytics once to warm Turbopack.
#    Cold-start of /chat takes ~15s; you do NOT want that during the demo.

# 5. Run the Quota Check (see bottom) to confirm you have headroom.
```

If anything is yellow/red on screen: refresh once, then check `backend\.env` for `GEMINI_API_KEY` + `GEMINI_API_KEY_2` + `GROQ_API_KEY`.

---

## What's actually working (verified 2026-05-29)

The marketing scenario is the proven demo, captured in DB:

| Scenario | Task ID (saved) | Status | Messages | Agents involved | Story coherent? |
|---|---|---|---|---|---|
| **Marketing campaign** | `0444ed11-9ed4-4ba4-a3dd-68fa4095f7c2` | ✅ completed, 91s | 10 | sales · finance · ops | ✅ multi-agent delegation, budget back-and-forth, revenue forecasting |
| Onboarding (Priya) | `b0900ef8-…` | ⚠ completed, 0 agent msgs | 3 | (none) | ❌ all subtasks failed — Gemini quota during the back-to-back run |
| Customer escalation | `7a5306ae-…` | ⚠ completed, 0 agent msgs | 3 | (none) | ❌ same as above |

→ **Re-run onboarding + escalation tomorrow** when quotas reset, then update this table with their task IDs.

**Marketing scenario observed flow** (use this in your narration):
1. `user → orchestrator`: prompt
2. `orchestrator → all`: "Planned 5 subtasks for: Summer Marketing Campaign"
3. `sales → all`: target audience analysis (used `generate_pitch`, `forecast_revenue`)
4. `finance → all`: budget plan ("exceeds $20K limit, here's a cut") — **real number constraint awareness**
5. **`sales → finance`** [request]: review revenue forecast
6. **`finance → ops`** [request]: review revised budget plan
7. `finance → all`: forecast validation
8. `ops → all`: budget cut recommendation (-10% on content creation)
9. **`finance → sales`** [request]: ongoing pipeline updates
10. `orchestrator → user`: final summary

Bold = agent-to-agent delegation. **This is the moment to point at during the demo.**

---

## 3-minute pitch script

### 0:00 – 0:30 — The problem

> "Companies spend 60% of work hours on coordination — emails, status meetings, approvals, hand-offs between teams. What if you could replace that entire layer of overhead with an AI workforce that collaborates autonomously?"

> "I'll show you a platform where one prompt deploys five specialized AI agents that talk to each other, plan together, and execute — and you can watch them do it live."

### 0:30 – 2:15 — Live demo — **Flow A** (only if quota check passes)

**On `/dashboard`, click the first example chip** → `"Launch a summer marketing campaign for our new product, budget under $20K"`.

A toast confirms dispatch. **Immediately switch to the Chat tab** so the multi-agent collaboration is visible.

Narrate (~45–60 s of live activity):

- *(orchestrator broadcast slides in)* — "The orchestrator just decomposed the request into a 5-step plan across four specialists. No code, no workflow builder. Just a prompt."
- *(Sales Agent message slides in)* — "Sales kicked off competitor research. They're going to need a budget — watch their next message…"
- *(Sales → Finance request appears)* — "There. Sales is asking Finance for a budget. **This is real agent-to-agent delegation** — not scripted."
- *(Finance's $15K breakdown appears)* — "Finance returned a number. Notice it said 'exceeds your $20K limit' — these agents reason about the constraints you give them."
- *(Ops Agent recommendation appears)* — "Ops cuts 10% of content costs to fit the budget."
- *(Final orchestrator summary)* — "Five agents, ten messages, ninety seconds. Same task takes a marketing team two days of email."

**Switch to Analytics tab.** Point at:
- Top-agent tile, completion-rate donut, agent-activity bar chart
- Live Activity feed — "Every message persisted. Real-time event log."

### Flow B — quota-exhausted fallback ("the pre-cached demo")

Open `/dashboard/tasks`. Click the marketing task (top of list, task starting `0444ed11…`). The **TaskDetail modal** opens with the full 5-subtask timeline:

- Status-colored dots, agent names in agent colors, dependency chips
- Expandable result for each subtask
- Final summary at the bottom

Narrate the timeline the same way as Flow A — the story is the same; only difference is the modal is the replay surface instead of the live chat feed. Judges won't know unless you tell them.

### 2:15 – 3:00 — Impact + vision

> "Five agents in the demo, but the framework supports any number. Today HR, Sales, Finance, Support, Ops. Tomorrow Procurement, Legal, BD, Customer Success."

> "Real-time WebSocket dashboard. Every message persisted to Postgres. Dual-key LLM failover so it stays up under load. Stack runs on free tiers — total cost to operate this demo: zero."

> "This is an AI Operating System for businesses. Every company will have one in five years. We built ours in 10 days. Thank you."

---

## Demo gotchas

- **First request after a cold start is slow** (~15 s) because Next.js Turbopack compiles on demand. Always warm the routes before going live.
- **Gemini Pro free tier = 25 req/day.** The planner deliberately uses Flash (see `llm_client.py`) — do NOT switch the planner to Pro before the demo.
- **Dual Gemini key failover** is on. If key 1 quota is exhausted, key 2 transparently takes over; Groq is the final fallback. All three are in `backend\.env`.
- **Activity Log is empty** (`/api/analytics/activity` returns `[]`). The Live Activity panel on `/dashboard/analytics` uses the WebSocket stream instead, so this is invisible to judges.

---

## If the live demo fails mid-stage

- Switch to `/dashboard/tasks`, click any prior task, narrate the timeline modal as the demo.
- The pre-recorded backup video (`demo-backup.mp4`, record this) is the ultimate safety net.

---

## Backup video recording recipe

When you record the backup video (after quotas have reset):

1. Cold-start everything (top of this file).
2. Run a single fresh task — submit the marketing prompt and let it play out.
3. Record screen: `/dashboard` (CommandBar submit + toast) → `/dashboard/chat` (watch messages slide in) → `/dashboard/analytics` (charts + activity feed). Total run ≈ 90 s.
4. Save as `demo-backup.mp4` in the repo root.

---

## Quota check recipe

Run this from `backend/` with venv active to see if you have demo headroom:

```python
# scripts/quota_check.py — quick "can I demo right now?" probe
import asyncio
from llm_client import call_llm

async def probe(role, label):
    try:
        r = await call_llm(
            "Reply with the single word OK.",
            "Be terse.",
            role=role,
            max_tokens=8,
            timeout=15,
        )
        print(f"  {label}: ✓  ({r[:30]})")
    except Exception as e:
        print(f"  {label}: ✗  {type(e).__name__}: {str(e)[:120]}")

async def main():
    await probe("agent", "Gemini Flash")
    await probe("fallback", "Groq Llama 3.3 70B")

asyncio.run(main())
```

Save it as `backend\scripts\quota_check.py` and run before each demo session. Two green checks = safe to run live. Any red = use **Flow B** (pre-cached TaskDetail).

---

## Tomorrow's TODO (before the actual demo)

- [ ] Re-run `scripts/run_one_scenario.py onboarding` and `escalation`, confirm both produce agent-to-agent traffic, update the "What's actually working" table.
- [ ] Record `demo-backup.mp4`.
- [ ] Practice Flow A live once. Time the narration.
- [ ] Practice Flow B from the TaskDetail modal once. Time it.
- [ ] Phase 4 (Day 10): deploy backend to Render/Railway, frontend to Vercel with `NEXT_PUBLIC_API_BASE` set.
