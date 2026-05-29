# Autonomous Enterprise AI Workforce — Hackathon Blueprint

## 🎯 One-Liner Pitch

> "An AI Operating System for businesses — deploy an entire AI workforce that collaborates, decides, and executes like a real team."

---

## 📍 Build Progress (last updated 2026-05-29)

**Status:** Phase 1 (Days 1-3) ✅ · Phase 2 (Days 4-6) ✅ · Phase 3 Days 7-9 ✅ · **Day 10 deploy prep ✅** (configs in repo, awaiting user click-through on Vercel + Render/Railway). Demo material in `DEMO.md`.

### ✅ Phase 1 — Foundation (Days 1-3)

**Backend** (`backend/`) — runs on `http://localhost:8000`
- FastAPI app with CORS, `/health`, Swagger at `/docs`
- 6 Pydantic models matching the DB schema
- Supabase client (graceful no-op when unconfigured)
- LLM abstraction (`llm_client.py`):
  - Routes by role: `agent` → Gemini Flash, `orchestrator` → Gemini Pro, `fallback` → Groq Llama 3.3 70B
  - **Dual Gemini-key failover**: tries `GEMINI_API_KEY` then `GEMINI_API_KEY_2` then Groq
  - 45 s hard timeout per call (`asyncio.wait_for`) so nothing ever hangs
  - Groq SDK `max_retries=1` to fail fast on TPM limits
  - Module-level `asyncio.Lock` around Gemini config+call (SDK is global-state)
  - Logs Gemini errors before falling back so we know which key/provider failed
- 5 specialized agents (HR / Sales / Finance / Support / Ops), each with:
  - Personality system prompt
  - 5 LLM-backed "fake-data" tools (25 total)
  - Per-task memory (reset by orchestrator at start of each run)
  - Text-based tool-call protocol via fenced `tool_call` JSON blocks
  - `→ @role:` mention parsing for agent-to-agent delegation
- Orchestrator (`orchestrator/`):
  - `Planner` — Gemini Flash JSON-mode decomposition into 3-5 subtasks; auto-repair retry on bad JSON; uses **Flash not Pro** (Pro's 25/day cap kept exhausting in dev)
  - `MessageBus` — persists every message to Supabase, broadcasts to WebSocket, maintains in-memory per-agent inbox
  - `Engine` — parallel dependency-respecting executor; mention-driven dynamic delegation with caps to prevent runaways:
    - `MAX_SUBTASKS = 10` (total per task)
    - `MAX_ROUNDS = 6`
    - `MAX_DYNAMIC_PER_AGENT = 2`
    - Dedupes `(from_role, to_role, topic_prefix)` to stop circular pinging
- Routers: `/api/tasks`, `/api/agents`, `/api/agents/roles/{role}/invoke`, `/api/messages`, `/api/analytics`, WebSocket at `/ws`
- `POST /api/tasks` plans + executes via FastAPI `BackgroundTasks`, returns immediately

**Database** (Supabase) — schema in `database/schema.sql`, seed in `database/seed.sql`
- Tables: companies, agents, tasks, messages, knowledge, activity_log
- Realtime publication enabled on tasks/messages/agents/activity_log
- Seeded "NovaTech Inc." + 5 agents with personalities + 3 KB articles
- **RLS off** for the hackathon (service key bypasses anyway; anon-key realtime subs need RLS off or permissive policies)

**Frontend** (`frontend/`) — runs on `http://localhost:3000`
- Next.js 16 + React 19 + Tailwind 4 + TypeScript (App Router, `src/` layout)
- **No shadcn/ui** — earlier note was wrong; UI is hand-rolled with Tailwind 4. (Install was skipped to avoid Tailwind-4-init fragility on Windows; reconsider if component count grows.)
- Read `frontend/AGENTS.md` before editing: Next 16 has breaking changes vs training data — check `node_modules/next/dist/docs/` first. Notably: `params`/`searchParams` are Promises; `PageProps`/`LayoutProps` are global helpers.

**Verified end-to-end:**
- "Launch a summer marketing campaign… budget under $20K" → 5 planned subtasks → 8 total executed (3 dynamic delegations) → 13 messages persisted
- "Onboard Priya as a senior frontend engineer" → 5-subtask plan, full Sales/HR/Ops/Finance flow

### ✅ Phase 2 Day 4 — Dashboard shell + Agent Grid

- `src/lib/types.ts` — TS mirrors of the 4 backend Pydantic models (Agent, Task, Subtask, Message) + enums
- `src/lib/api.ts` — typed fetch client (`api.health/listAgents/listTasks/getTask/createTask/listMessages`), `cache: "no-store"`, reads `NEXT_PUBLIC_API_BASE` (defaults to `http://localhost:8000`); also exports `wsUrl()` for the Day-5 socket
- `src/app/page.tsx` — server-side `redirect("/dashboard")`
- `src/app/layout.tsx` — Geist fonts, forced dark base (`bg-zinc-950 text-zinc-100`), proper metadata
- `src/app/dashboard/layout.tsx` — Sidebar + Header shell, scrollable `<main>`
- `src/app/dashboard/page.tsx` — wraps `<CommandBar />` + `<Suspense><AgentGrid /></Suspense>` with a skeleton fallback
- `components/layout/Sidebar.tsx` — Agents/Tasks/Chat/Analytics nav links (Tasks/Chat/Analytics pages not yet built)
- `components/layout/Header.tsx` + `components/layout/BackendStatus.tsx` — client component pings `/health` every 10s, shows green/red/grey pill
- `components/layout/CommandBar.tsx` — client component, textarea + 3 example chips (campaign / onboarding / churn), ⌘/Ctrl+Enter, posts to `/api/tasks`, calls `router.refresh()`, surfaces task id + error inline
- `components/agents/AgentCard.tsx` — colored top-stripe (uses `agent.color` from DB), initial avatar, role badge, status dot with pulse for non-idle states
- `components/agents/AgentGrid.tsx` — **server component**, SSR-fetches `/api/agents`, sorts by canonical role order (hr→sales→finance→support→ops), renders friendly error card if backend is down

**Verified end-to-end:** `curl http://localhost:3000/dashboard` returns 40 KB HTML containing all 5 agent names + CommandBar + Sidebar + BackendStatus. `/ → 307 /dashboard`.

### ✅ Phase 2 Day 5 — Live WebSocket chat feed

- `src/hooks/useLiveEvents.ts` — client hook, opens `ws://localhost:8000/ws`, dedupes by message id, auto-reconnects after 2 s, exposes `{ connection, messages, agentStatus, taskStatus }`
- `components/chat/MessageBubble.tsx` — colored initial avatar (uses `agent.color`), `from → to` header, type pill (REQUEST / RESPONSE / INFO / ESCALATION / BROADCAST / USER), monospace timestamp, whitespace-preserving body. Handles synthetic senders (`orchestrator`, `user`, `all`).
- `components/chat/TypingIndicators.tsx` — pill row, one per agent in `working`/`collaborating` state
- `components/chat/ChatFeed.tsx` — client wrapper; takes server-fetched `agents` + `initialMessages`, layers live updates on top, auto-scrolls on new message, shows connection pill (Live / Connecting / Disconnected)
- `src/app/dashboard/chat/page.tsx` — server component; parallel-fetches `/api/agents` + `/api/messages` (last 50, sorted ASC), passes both to `<ChatFeed/>`

**Backend WS protocol verified:** server emits `{type, data}` for 4 types — `connected`, `message` (full message row), `task_status` (`{task_id, status, plan?, result?, completed_at?}`), `agent_status` (`{role, status}`). Bus in `backend/orchestrator/bus.py` calls `broadcaster.broadcast()` from `send()`, `update_task_status()`, `update_agent_status()`.

**Verified end-to-end:** Connected a Python WS client, posted "draft a one-line greeting for new hire Sam" to `/api/tasks`, received in order: handshake → `user→orchestrator` msg → `task_status: planning` → orchestrator broadcast → `task_status: in_progress` → `agent_status hr: working` → hr response → `agent_status hr: idle` → final orchestrator msg → `task_status: completed`. 4 message events, 3 task_status, 2 agent_status. Initial SSR of `/dashboard/chat` returned 118 KB HTML containing all 5 agents and 50 historical message bubbles with correct type pills.

### ✅ Phase 2 Day 6 — Task timeline + detail modal

- `components/tasks/TaskCard.tsx` — clickable card; status pill (Pending / In Progress / Completed / Failed) with colored dot, agent-role badges from subtasks, `completed/total` step counter, relative timestamp (`Xs/m/h/d ago`)
- `components/tasks/TaskTimeline.tsx` — vertical timeline; per-subtask: status-colored circle (pulse on in_progress), `#N` index, agent name in agent color, `depends on #X` chip, priority tag, description, expandable result `<details>`
- `components/tasks/TaskDetail.tsx` — client modal; lazily fetches `/api/tasks/{id}` on mount, backdrop-click + Escape to close, sections: status header, prompt, Timeline, Summary (`task.result.summary`), Error (if any). Modal stops propagation so clicks inside don't dismiss it.
- `components/tasks/TaskList.tsx` — client wrapper; takes SSR `initialTasks`+`agents`, subscribes via `useLiveEvents()` and merges `taskStatus[id]` updates into rows (status + completed_at), filter chips (All/In progress/Completed/Pending/Failed) with live counts, sorts by `created_at` DESC, owns the selected-task state for the modal
- `src/app/dashboard/tasks/page.tsx` — server component; parallel-fetches `/api/tasks` + `/api/agents`, friendly error card if backend down, hands data to `<TaskList/>`

**Verified end-to-end:** `curl http://localhost:3000/dashboard/tasks` returned 59 KB HTML (HTTP 200) containing all 5 agent role badges (hr/sales/finance/support/ops), status pills (15 Completed / 4 Failed / 2 Pending matching the seed DB), and the filter bar. Live `task_status` merge path reuses the same `useLiveEvents` hook already proven on the chat feed.

### ✅ Phase 3 Day 7 — Analytics dashboard

**Backend changes:**
- `backend/routers/analytics.py` — added `GET /api/analytics/agents`. Existing endpoints were `/tasks` (TaskMetrics) and `/activity` (returns `[]` because the orchestrator doesn't write `activity_log`). New endpoint derives per-agent stats (`messages_sent`, `tasks_touched`) from the `messages` table; returns sorted DESC by `messages_sent`. Live verification: `[{HR: 15msgs/5tasks}, {Sales: 12/2}, {Ops: 12/4}, {Finance: 9/2}, {Support: 6/1}]`.

**Frontend changes:**
- `recharts@3.8.1` installed (`npm i recharts`).
- `src/lib/types.ts` — added `TaskMetrics` and `AgentMetric`.
- `src/lib/api.ts` — added `api.getTaskMetrics()` and `api.getAgentMetrics()`.
- `components/analytics/StatTile.tsx` — label/value/sublabel tile with colored accent stripe.
- `components/analytics/TaskStatusChart.tsx` — donut (recharts Pie) with completion% in center, color legend below.
- `components/analytics/AgentPerformanceChart.tsx` — horizontal bar chart of messages-per-agent; bars colored from `agent.color`; per-agent task counts below.
- `components/analytics/LiveActivityFeed.tsx` — client; subscribes to `useLiveEvents`, merges messages + `agent_status` + `task_status` events into one monospace scrolling log (max 80 items), connection dot. Uses an empty `initialMessages` array because this page is purely live.
- `src/app/dashboard/analytics/page.tsx` — server; parallel-fetches `/tasks` + `/agents` (analytics) + `/api/agents`, lays out 4 StatTiles → TaskStatusChart + AgentPerformanceChart → LiveActivityFeed.

**Verified end-to-end:** `curl http://localhost:3000/dashboard/analytics` returned 36 KB HTML (HTTP 200) containing all 4 stat tiles, both chart sections, the activity feed, and the live values matching `/api/analytics/tasks` (7 completed · 3 failed). Recharts SVG class names present in HTML, all 5 agent names rendered, HR identified as the top agent.

**Known gap (not blocking Day 7):** `activity_log` table is never written. If we want token-usage / duration metrics, the orchestrator's `Engine` needs to start inserting rows around each LLM call. Defer until needed.

### ✅ Phase 3 Day 8 — Polish: toasts + animations

- `src/lib/toast.tsx` — minimal `<ToastProvider>` + `useToast()` (no external lib). Top-right stack, 4 variants (success/error/info), auto-dismiss (configurable per toast, default 4.5s), individual dismiss button. Slide-in animation on enter.
- `src/app/globals.css` — added `slide-in` (220 ms cubic-bezier) and `fade-in` (320 ms ease-out) keyframes; registered as `--animate-slide-in` / `--animate-fade-in` in Tailwind 4 `@theme inline`, so utilities `animate-slide-in` / `animate-fade-in` work.
- `components/layout/LiveToaster.tsx` — invisible client component, subscribes to `useLiveEvents`, fires toasts on `task_status` transitions (`in_progress` → "Agents dispatched", `completed` → success, `failed` → error). Lazy-fetches task title (`api.getTask`) for the description; caches per task; dedupes by `taskId:status` so the same transition only toasts once.
- `app/dashboard/layout.tsx` — wraps the whole dashboard tree in `<ToastProvider>` and mounts `<LiveToaster/>` outside the layout grid.
- `components/layout/CommandBar.tsx` — now imports `useToast`, fires success toast on dispatch and error toast on failure.
- `components/chat/ChatFeed.tsx` — captures the SSR-seed message IDs at mount (`useState(() => new Set(...))`), wraps each rendered message in a div that only gets `animate-fade-in` for IDs NOT in the seed set. Result: historical messages render instantly on SSR, new ones fade in.
- `components/analytics/LiveActivityFeed.tsx` — wraps every row in `animate-slide-in` (the activity feed has no SSR seed, so animating everything is the intended aesthetic).

**Deliberately deferred (not blocking demo):**
- Pause/resume agent control — `PATCH /api/agents/{id}/status` exists, but orchestrator's `Engine` doesn't check `status="paused"` before dispatching. Wiring this up would require touching `orchestrator/engine.py` to skip paused agents and is a multi-touch change.
- Live status reflection on Agent Grid — `/dashboard` agent cards are server-rendered, so live `agent_status` events don't repaint them. Would need a small client wrapper similar to `TaskList`. Not in CommandBar/CommandBar path.
- Light mode — dark is enforced; toggle wasn't a blueprint requirement.

**Verified end-to-end:** All four routes still 200 with stable byte sizes (`/dashboard` 41 KB, `/chat` 116 KB, `/tasks` 60 KB, `/analytics` 38 KB). Each SSR HTML contains exactly one `pointer-events-none fixed top-4 right-4` marker (the ToastProvider viewport). Chat page still renders 5 agent names + 50 historical message bubbles after the wrapper-div change.

### ✅ Phase 3 Day 9 — Demo scenarios + pitch script

Ran all three blueprint demo scenarios sequentially via `backend/scripts/run_demo_scenarios.py`; results saved to `backend/scripts/demo_results.json`.

**Outcome — only marketing is demo-ready today:**

- ✅ **Marketing campaign** (task `0444ed11-9ed4-4ba4-a3dd-68fa4095f7c2`): completed in 91 s, 10 messages, 5 subtasks, 3 agents (sales/finance/ops). Real multi-agent delegation: `sales → finance` for budget, `finance → ops` for revised plan review, `finance → sales` for ongoing updates. Finance correctly flagged budget exceeded $20K constraint and recommended a cut. **This is the marquee demo.**
- ⚠ **Onboarding** + **escalation**: both completed but with 0 agent messages — all subtasks errored. Root cause: **Gemini RPM ceiling** hit by running 3 scenarios back-to-back (5 s cooldown between them was not enough).

**Provider exhaustion discovered:**

- Gemini Flash key 1 + key 2 both exhausted today (free tier `generate_content_free_tier_requests`, limit shown as 20 — possibly daily-RPD on this account).
- **Groq is at 99,837 / 100,000 TPD** (rolling 24h) — fallback is effectively dead until tomorrow.
- Discovered via direct `call_llm(..., role="fallback")` probe — returned `RateLimitError 429: tokens per day (TPD): Limit 100000, Used 99837, Requested 331`.

**Artefacts added:**

- `DEMO.md` (repo root) — quota status table, cold-start checklist, scenario task IDs, 3-minute pitch script with both Flow A (live) and Flow B (replay marketing task via TaskDetail modal if quota is dead), demo gotchas, backup video recipe, tomorrow's TODO list.
- `backend/scripts/run_demo_scenarios.py` — sequential 3-scenario runner; writes `demo_results.json`.
- `backend/scripts/run_one_scenario.py` — single-scenario runner for re-testing onboarding/escalation tomorrow.
- `backend/scripts/quota_check.py` — quick "can I demo right now?" probe; prints OK/FAIL for Gemini Flash and Groq. **Run before every demo session.**

### ✅ Phase 4 Day 10 — Deploy prep

**Backend hardening:**
- `backend/main.py` — honors `PORT` env var, disables uvicorn `reload` outside `ENVIRONMENT=development`.
- `backend/config.py` — `cors_origins` is now a raw CSV string parsed via `cors_origin_list()` helper (pydantic-settings 2.6.1 doesn't ship `NoDecode`, and the alternative `field_validator` runs after pydantic tries JSON-decoding `list[str]` from env — string + helper is the cleanest workaround).
- `backend/main.py` CORS middleware now uses `settings.cors_origin_list()`.

**Deploy configs added:**
- `backend/Procfile` — `web: uvicorn main:app --host 0.0.0.0 --port $PORT` (Heroku-style, works on Render and Railway).
- `backend/render.yaml` — one-click Render blueprint: free plan, `rootDir: backend`, healthcheck `/health`, all 7 env vars declared as `sync: false` (set by hand in dashboard).
- `backend/runtime.txt` — `python-3.11.9` (matches local venv; both Render and Railway respect this).
- `.env.example` — updated to match current code (`NEXT_PUBLIC_API_BASE` not the obsolete `NEXT_PUBLIC_API_URL`/`NEXT_PUBLIC_WS_URL`; added `CORS_ORIGINS` line for prod).

**Frontend verified:**
- `npm run build` succeeds (Next 16 + Turbopack, 12 s).
- TS error fixed: `AgentPerformanceChart` tooltip formatter — recharts' `Formatter<ValueType, NameType>` allows `undefined`, so the explicit `(value: number, name: string)` annotation was rejected. Removed annotations, cast at use.
- Routes: `/` static (redirect), `/dashboard`, `/dashboard/analytics`, `/dashboard/chat`, `/dashboard/tasks` all dynamic (server-rendered on demand).

**Git state:** No git repo at `D:\Ai_Agent_Enterprise\` root. `frontend/.git` exists from the Next.js scaffold but is isolated. **The user must `git init` at the root, commit, and push to GitHub before the platforms can pull.** `.gitignore` is already comprehensive (covers `.env`, `.venv`, `__pycache__`, `node_modules`, `.next`).

### ⏭️ Next — user click-through on the platforms

The codebase is ready. User needs to:
1. `git init` at repo root, push to GitHub.
2. Deploy backend to Render (uses `render.yaml`) or Railway. Set all 7 env vars manually.
3. Deploy frontend to Vercel with Root Directory = `frontend`. Set `NEXT_PUBLIC_API_BASE` = backend URL.
4. Update backend `CORS_ORIGINS` to include the Vercel URL.
5. Smoke-test: load Vercel URL, submit a task, watch chat feed.

See chat transcript or DEMO.md for the verbatim command sequences. **NOT** writing a `DEPLOY.md` unless the user asks.

### 🔑 Known free-tier quotas (so you don't burn yourself)

| Provider | Limit | Notes |
|---|---|---|
| Gemini 2.5 Pro | 25 req/day | Too tight for dev — only use for the final demo recording |
| Gemini 2.5 Flash | 500 req/day per key | Planner + all agents use this; dual keys = 1,000/day |
| Groq Llama 3.3 70B | 100k tokens/day, 12k tokens/min | Auto-fallback only; rolling window resets ~1 min for TPM, ~daily for TPD |

### 🚀 How to run (cold start)

```powershell
# Backend
cd D:\Ai_Agent_Enterprise\backend
.\.venv\Scripts\Activate.ps1
python main.py

# Frontend (separate terminal)
cd D:\Ai_Agent_Enterprise\frontend
npm run dev

# Submit a task (third terminal)
$body = @{ prompt = "Your business request here" } | ConvertTo-Json
Invoke-RestMethod -Uri http://localhost:8000/api/tasks -Method POST `
  -ContentType "application/json" -Body $body
```

`.env` lives at `backend\.env` (see `.env.example` for the template).

---

## Overview

Build a platform where companies spin up AI agents (HR, Sales, Finance, Support, Ops) that communicate with each other, delegate tasks, make decisions, and execute workflows — all visible in a real-time dashboard.

**Timeline:** 1–2 weeks
**Purpose:** High-level hackathon
**Goal:** Jaw-dropping demo, technically solid, clearly useful

---

## Recommended Tech Stack

| Layer | Tech | Why |
|---|---|---|
| Frontend | **Next.js 14 (App Router) + Tailwind + shadcn/ui** | Fast to build, great DX, polished UI out of the box |
| Backend | **Python FastAPI** | Best ecosystem for LLM orchestration, async-native |
| LLM (Orchestrator) | **Google Gemini 2.5 Pro (Free)** | Smartest free model, handles complex task planning |
| LLM (All 5 Agents) | **Google Gemini 2.5 Flash (Free)** | Fast, free, 500 req/day is plenty |
| LLM (Fallback) | **Groq Llama 3.3 70B (Free)** | Ultra-fast fallback if Gemini hits rate limits |
| Agent Framework | **Custom lightweight framework** | More control than LangChain, less bloat, easier to debug |
| Database | **Supabase (Postgres + Realtime)** | Free tier, real-time subscriptions for live dashboard, auth built-in |
| Task Queue | **Redis + Celery** (or just **asyncio** for hackathon speed) | Background agent execution |
| WebSocket | **FastAPI WebSockets** | Live agent-to-agent chat feed |
| Deployment | **Vercel (frontend) + Railway/Render (backend)** | One-click deploys, free tiers |

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   NEXT.JS FRONTEND                   │
│                                                      │
│  ┌──────────┐ ┌──────────┐ ┌───────────────────┐   │
│  │ Agent    │ │ Live Chat│ │ Analytics         │   │
│  │ Dashboard│ │ Feed     │ │ Dashboard         │   │
│  └────┬─────┘ └────┬─────┘ └────────┬──────────┘   │
│       │             │                │               │
└───────┼─────────────┼────────────────┼───────────────┘
        │             │                │
        │        WebSocket          REST API
        │             │                │
┌───────┼─────────────┼────────────────┼───────────────┐
│       │      FASTAPI BACKEND         │               │
│  ┌────▼─────────────▼────────────────▼────────┐      │
│  │           Orchestrator Engine               │      │
│  │  (receives tasks, routes to agents,         │      │
│  │   manages agent-to-agent communication)     │      │
│  └────┬──────┬──────┬──────┬──────┬───────────┘      │
│       │      │      │      │      │                   │
│  ┌────▼─┐┌───▼──┐┌──▼───┐┌─▼────┐┌▼──────┐          │
│  │  HR  ││Sales ││Finan ││Supp- ││ Ops   │          │
│  │Agent ││Agent ││Agent ││ort   ││Agent  │          │
│  │      ││      ││      ││Agent ││       │          │
│  └──┬───┘└──┬───┘└──┬───┘└──┬───┘└──┬────┘          │
│     │       │       │       │       │                │
│  ┌──▼───────▼───────▼───────▼───────▼────┐           │
│  │        Shared Memory / Context        │           │
│  │          (Company Knowledge)          │           │
│  └───────────────┬───────────────────────┘           │
│                  │                                    │
└──────────────────┼────────────────────────────────────┘
                   │
          ┌────────▼────────┐
          │    Supabase     │
          │  (Postgres +    │
          │   Realtime)     │
          └─────────────────┘
```

---

## Agent Design

### Each Agent Has:

```python
class Agent:
    name: str              # "HR Agent", "Sales Agent", etc.
    role: str              # System prompt defining personality & expertise
    tools: list[Tool]      # Functions the agent can call
    memory: list[dict]     # Conversation history + context
    status: str            # "idle", "working", "waiting", "collaborating"
    inbox: list[Message]   # Messages from other agents
```

### The 5 Agents

#### 1. HR Agent
- **Personality:** Professional, empathetic, policy-focused
- **Tools:** `search_employees`, `draft_job_posting`, `schedule_interview`, `analyze_resume`, `generate_onboarding_plan`
- **Triggers:** Hiring requests, employee questions, onboarding, policy lookups

#### 2. Sales Agent
- **Personality:** Energetic, data-driven, persuasive
- **Tools:** `research_competitor`, `generate_pitch`, `create_proposal`, `forecast_revenue`, `draft_outreach_email`
- **Triggers:** Lead follow-ups, proposals, competitor analysis, pipeline management

#### 3. Finance Agent
- **Personality:** Precise, cautious, analytical
- **Tools:** `estimate_budget`, `calculate_roi`, `generate_invoice`, `expense_analysis`, `financial_forecast`
- **Triggers:** Budget requests, cost analysis, invoicing, financial planning

#### 4. Customer Support Agent
- **Personality:** Friendly, patient, solution-oriented
- **Tools:** `search_knowledge_base`, `create_ticket`, `draft_response`, `escalate_issue`, `sentiment_analysis`
- **Triggers:** Customer complaints, ticket routing, FAQ responses, escalations

#### 5. Operations Agent
- **Personality:** Systematic, efficient, process-focused
- **Tools:** `create_task`, `assign_task`, `track_progress`, `schedule_meeting`, `generate_report`
- **Triggers:** Task management, scheduling, workflow optimization, reporting

---

## Agent Communication Protocol

Agents talk to each other via a message bus:

```python
class AgentMessage:
    from_agent: str        # "sales_agent"
    to_agent: str          # "finance_agent"  (or "all" for broadcast)
    message_type: str      # "request", "response", "info", "escalation"
    content: str           # Natural language message
    data: dict             # Structured data (budgets, lists, etc.)
    priority: str          # "low", "medium", "high", "urgent"
    task_id: str           # Links to parent task
    timestamp: datetime
```

### Communication Flow Example

```
User: "Launch a new marketing campaign for our summer sale"

Orchestrator → Sales Agent: "Research competitors and create campaign strategy"
Sales Agent → Finance Agent: "Need budget estimate for summer campaign"
Finance Agent → Sales Agent: "Estimated budget: $15,000. Breakdown attached."
Sales Agent → Ops Agent: "Schedule campaign tasks for next 2 weeks"
Sales Agent → HR Agent: "Do we need to hire a freelance designer?"
HR Agent → Sales Agent: "Current design team has capacity. No hire needed."
Ops Agent → All: "Campaign timeline created. 12 tasks assigned."
Sales Agent → User: "Campaign plan ready. Here's the summary..."
```

---

## Database Schema (Supabase / Postgres)

```sql
-- Company context
CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    industry TEXT,
    created_at TIMESTAMP DEFAULT now()
);

-- Agent definitions
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id),
    name TEXT NOT NULL,
    role TEXT NOT NULL,           -- "hr", "sales", "finance", "support", "ops"
    system_prompt TEXT NOT NULL,
    status TEXT DEFAULT 'idle',   -- "idle", "working", "collaborating"
    avatar_url TEXT,
    created_at TIMESTAMP DEFAULT now()
);

-- Tasks (user requests that get broken down)
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id),
    title TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'pending', -- "pending", "in_progress", "completed", "failed"
    created_by TEXT DEFAULT 'user',
    assigned_agents TEXT[],        -- which agents are involved
    result JSONB,
    created_at TIMESTAMP DEFAULT now(),
    completed_at TIMESTAMP
);

-- Agent-to-agent messages
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES tasks(id),
    from_agent TEXT NOT NULL,
    to_agent TEXT NOT NULL,
    message_type TEXT NOT NULL,     -- "request", "response", "info", "escalation"
    content TEXT NOT NULL,
    data JSONB,
    priority TEXT DEFAULT 'medium',
    created_at TIMESTAMP DEFAULT now()
);

-- Company knowledge base
CREATE TABLE knowledge (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id),
    category TEXT,                  -- "policy", "product", "customer", "process"
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1536),         -- for semantic search
    created_at TIMESTAMP DEFAULT now()
);

-- Agent activity log (for dashboard analytics)
CREATE TABLE activity_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES agents(id),
    task_id UUID REFERENCES tasks(id),
    action TEXT NOT NULL,
    details JSONB,
    tokens_used INTEGER,
    duration_ms INTEGER,
    created_at TIMESTAMP DEFAULT now()
);
```

---

## Folder Structure

```
autonomous-ai-workforce/
├── frontend/                      # Next.js 14
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx               # Landing / login
│   │   ├── dashboard/
│   │   │   ├── page.tsx           # Main dashboard
│   │   │   ├── agents/
│   │   │   │   └── page.tsx       # Agent grid view
│   │   │   ├── tasks/
│   │   │   │   └── page.tsx       # Task management
│   │   │   ├── chat/
│   │   │   │   └── page.tsx       # Live agent chat feed
│   │   │   └── analytics/
│   │   │       └── page.tsx       # Analytics dashboard
│   │   └── api/                   # Next.js API routes (proxy to backend)
│   ├── components/
│   │   ├── ui/                    # shadcn components
│   │   ├── agents/
│   │   │   ├── AgentCard.tsx      # Individual agent status card
│   │   │   ├── AgentGrid.tsx      # All agents overview
│   │   │   └── AgentDetail.tsx    # Agent detail modal
│   │   ├── chat/
│   │   │   ├── ChatFeed.tsx       # Real-time message stream
│   │   │   ├── MessageBubble.tsx  # Individual message
│   │   │   └── TaskInput.tsx      # User command input
│   │   ├── tasks/
│   │   │   ├── TaskCard.tsx
│   │   │   ├── TaskTimeline.tsx   # Visual task execution flow
│   │   │   └── TaskDetail.tsx
│   │   ├── analytics/
│   │   │   ├── AgentPerformance.tsx
│   │   │   ├── TaskMetrics.tsx
│   │   │   └── LiveActivityFeed.tsx
│   │   └── layout/
│   │       ├── Sidebar.tsx
│   │       ├── Header.tsx
│   │       └── CommandBar.tsx     # Global command input
│   ├── lib/
│   │   ├── supabase.ts           # Supabase client
│   │   ├── websocket.ts          # WebSocket connection
│   │   └── api.ts                # Backend API client
│   ├── hooks/
│   │   ├── useAgents.ts
│   │   ├── useMessages.ts
│   │   └── useRealtime.ts
│   └── package.json
│
├── backend/                       # Python FastAPI
│   ├── main.py                    # FastAPI app entry
│   ├── config.py                  # Environment variables
│   ├── routers/
│   │   ├── tasks.py               # POST /tasks, GET /tasks
│   │   ├── agents.py              # GET /agents, agent status
│   │   ├── messages.py            # GET /messages (with filters)
│   │   ├── analytics.py           # GET /analytics
│   │   └── websocket.py           # WebSocket endpoint
│   ├── agents/
│   │   ├── base.py                # Base Agent class
│   │   ├── hr.py                  # HR Agent
│   │   ├── sales.py               # Sales Agent
│   │   ├── finance.py             # Finance Agent
│   │   ├── support.py             # Support Agent
│   │   ├── ops.py                 # Ops Agent
│   │   └── tools/                 # Agent tool functions
│   │       ├── hr_tools.py
│   │       ├── sales_tools.py
│   │       ├── finance_tools.py
│   │       ├── support_tools.py
│   │       └── ops_tools.py
│   ├── orchestrator/
│   │   ├── engine.py              # Main orchestration logic
│   │   ├── planner.py             # Task decomposition
│   │   ├── router.py              # Routes sub-tasks to agents
│   │   └── memory.py              # Shared context manager
│   ├── database/
│   │   ├── client.py              # Supabase client
│   │   ├── models.py              # Pydantic models
│   │   └── queries.py             # Database queries
│   └── requirements.txt
│
├── docker-compose.yml             # (optional) local dev setup
├── .env.example
└── README.md
```

---

## Phased Build Plan (10 Days)

### Phase 1: Foundation (Days 1–3)

**Day 1 — Project Setup + Backend Skeleton**
- [ ] Initialize Next.js project with Tailwind + shadcn/ui
- [ ] Initialize FastAPI project
- [ ] Set up Supabase project (create tables)
- [ ] Create `.env` files with API keys (Gemini, Groq, Supabase)
- [ ] Build basic FastAPI health check + CORS setup
- [ ] Create Pydantic models matching DB schema

**Day 2 — Agent Framework**
- [ ] Build `BaseAgent` class with Gemini API integration + LLM abstraction layer
- [ ] Implement tool-calling mechanism (function calling via Gemini)
- [ ] Create all 5 agents with system prompts and basic tools
- [ ] Test: each agent can respond independently to a prompt
- [ ] Implement agent memory (conversation history per agent)

**Day 3 — Orchestrator**
- [ ] Build `Orchestrator.plan()` — takes user task, uses Gemini Pro to decompose into sub-tasks
- [ ] Build `Orchestrator.route()` — assigns sub-tasks to correct agents
- [ ] Build agent message bus — agents can send/receive messages
- [ ] Implement agent-to-agent delegation (Agent A asks Agent B for info)
- [ ] Test: "Launch a marketing campaign" gets broken into 5+ sub-tasks across agents

### Phase 2: Frontend + Real-time (Days 4–6)

**Day 4 — Dashboard Layout**
- [ ] Build Sidebar + Header + main layout
- [ ] Build Agent Grid — shows all 5 agents with status indicators
- [ ] Build Command Bar — user types natural language commands
- [ ] Connect frontend to backend API (fetch agents, post tasks)

**Day 5 — Live Chat Feed**
- [ ] Set up WebSocket connection (frontend ↔ backend)
- [ ] Build ChatFeed component — shows agent-to-agent messages in real time
- [ ] Build MessageBubble with agent avatars, timestamps, message types
- [ ] Color-code messages by agent (each agent has a distinct color)
- [ ] Show typing indicators when agents are "thinking"

**Day 6 — Task Management View**
- [ ] Build TaskTimeline — visual flow of task execution
- [ ] Show task status (pending → in progress → completed)
- [ ] Show which agents are assigned to each task
- [ ] Build TaskDetail modal — full breakdown of sub-tasks and results

### Phase 3: Wow Factor (Days 7–9)

**Day 7 — Analytics Dashboard**
- [ ] Agent performance metrics (tasks completed, avg response time)
- [ ] Task completion rate chart
- [ ] Token usage tracking
- [ ] Live activity feed (scrolling log of all agent actions)
- [ ] Use recharts for beautiful charts

**Day 8 — Polish + Killer Features**
- [ ] Add agent "personality" — each agent has a unique communication style
- [ ] Add notification system — important events pop up
- [ ] Add "pause/resume" agent control
- [ ] Add dark mode (Tailwind dark: classes)
- [ ] Smooth animations (framer-motion or CSS transitions)
- [ ] Loading states and skeleton screens

**Day 9 — Demo Scenarios**
- [ ] Pre-build 3 killer demo scenarios with seed data:
  1. **"Launch a new marketing campaign"** — full multi-agent collaboration
  2. **"Onboard a new employee"** — HR + Ops + Support coordination
  3. **"Handle an angry customer escalation"** — Support + Sales + Finance
- [ ] Record a backup video demo in case live demo fails
- [ ] Write script for live demo presentation

### Phase 4: Ship (Day 10)

**Day 10 — Deploy + Present**
- [ ] Deploy frontend to Vercel
- [ ] Deploy backend to Railway or Render
- [ ] Ensure Supabase is production-ready
- [ ] Final end-to-end test of all 3 demo scenarios
- [ ] Prepare 3-minute pitch script
- [ ] Prepare slides if needed (problem → solution → demo → impact)

---

## Killer Demo Script (3 Minutes)

### Minute 1: The Problem (30s)
> "Companies spend 60% of work hours on coordination — emails, meetings, status updates, approvals. What if you could replace that overhead with an AI workforce that collaborates autonomously?"

### Minute 1-2: The Demo (90s)
> "Watch this. I'm going to type one command..."

Type: **"Launch a summer marketing campaign for our new product, budget under $20K"**

Show the dashboard as:
1. Orchestrator breaks it into sub-tasks (visible on screen)
2. Sales Agent researches competitors (live messages appear)
3. Finance Agent estimates budget and responds to Sales
4. Sales Agent creates campaign plan
5. Ops Agent creates a task timeline
6. HR Agent confirms team capacity
7. All agents converge on a final recommendation

> "Five AI agents just collaborated in 30 seconds on a task that would take a human team 2 days."

### Minute 3: Impact + Vision (30s)
> "This is an AI Operating System for businesses. Every company will have one. We're building it first."

---

## Key LLM API Patterns You'll Use

### LLM Client Abstraction (Important!)
```python
# llm_client.py — Abstract LLM calls so you can swap providers easily
import google.generativeai as genai
from groq import Groq

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

async def call_llm(prompt: str, system_prompt: str, role: str = "agent") -> str:
    """
    role="orchestrator" → Gemini 2.5 Pro (smartest)
    role="agent"        → Gemini 2.5 Flash (fast + free)
    role="fallback"     → Groq Llama 3.3 70B (backup)
    """
    if role == "orchestrator":
        model = genai.GenerativeModel(
            "gemini-2.5-pro-preview-05-06",
            system_instruction=system_prompt
        )
        response = model.generate_content(prompt)
        return response.text
    elif role == "fallback":
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000
        )
        return response.choices[0].message.content
    else:  # default: agent
        model = genai.GenerativeModel(
            "gemini-2.5-flash-preview-05-20",
            system_instruction=system_prompt
        )
        response = model.generate_content(prompt)
        return response.text
```

### 1. Agent System Prompt Pattern
```python
SALES_AGENT_PROMPT = """
You are the Sales Agent for {company_name}.
Your role: competitive analysis, lead generation, proposals, outreach.

COMPANY CONTEXT:
{company_knowledge}

CURRENT TASK:
{task_description}

MESSAGES FROM OTHER AGENTS:
{inbox_messages}

AVAILABLE TOOLS:
- research_competitor(company_name) → competitor analysis
- generate_pitch(product, audience) → pitch deck outline
- draft_outreach_email(recipient, context) → email draft
- forecast_revenue(period, assumptions) → revenue forecast

Respond with your analysis AND any requests you need from other agents.
Format agent requests as:
→ @finance_agent: [your request]
→ @hr_agent: [your request]
"""
```

### 2. Orchestrator Planning Pattern
```python
ORCHESTRATOR_PROMPT = """
You are the Task Orchestrator. Break down user requests into sub-tasks
and assign them to the right agents.

AVAILABLE AGENTS: HR, Sales, Finance, Support, Operations

USER REQUEST: {user_input}

Respond in this JSON format:
{
  "task_title": "...",
  "subtasks": [
    {
      "id": 1,
      "description": "...",
      "assigned_to": "sales_agent",
      "depends_on": [],
      "priority": "high"
    }
  ],
  "execution_order": "parallel" or "sequential" or "mixed"
}
"""
```

### 3. Tool Execution Pattern
```python
# Tools are just Python functions the agent can call
async def research_competitor(company_name: str) -> dict:
    """Simulated tool — in hackathon, use LLM to generate realistic data"""
    result = await call_llm(
        prompt=f"Generate a brief competitive analysis of {company_name}. "
               f"Include: strengths, weaknesses, market position, pricing.",
        system_prompt="You are a business analyst. Be concise and data-driven.",
        role="agent"  # Uses Gemini Flash (free)
    )
    return {"analysis": result}
```

---

## Hackathon Shortcuts (Ship Fast)

1. **Fake the tools** — Agent tools don't need real APIs. Use Gemini to generate realistic fake data (competitor reports, budgets, schedules). Judges care about the orchestration, not whether you actually called LinkedIn's API.

2. **Seed the knowledge base** — Pre-load a fake company ("NovaTech Inc.") with employees, products, policies. Makes the demo feel real instantly.

3. **WebSocket for wow** — Even basic WebSocket showing messages appear in real time creates massive visual impact. Prioritize this over complex features.

4. **Typing indicators** — Add a 1-2 second artificial delay with "Agent is thinking..." before each response. Makes it feel like real collaboration, not instant regurgitation.

5. **Agent avatars + colors** — Give each agent a distinct avatar and color. Visual differentiation makes the dashboard pop immediately.

6. **Pre-compute expensive demos** — For your main demo scenario, you can cache the responses so the demo runs smoothly even with API latency.

---

## Environment Variables Needed

```env
# .env
GEMINI_API_KEY=AIza...              # Free from https://aistudio.google.com/apikey
GROQ_API_KEY=gsk_...                # Free from https://console.groq.com
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_KEY=eyJ...

# Optional
REDIS_URL=redis://localhost:6379    # if using task queue
```

### Free Tier Limits (Know These!)

| Provider | Model | Free Limit | Enough? |
|---|---|---|---|
| Google Gemini | 2.5 Pro | 25 req/day | Yes — orchestrator only |
| Google Gemini | 2.5 Flash | 500 req/day, 1M tokens/day | Yes — all agents comfortably |
| Groq | Llama 3.3 70B | ~14,400 req/day | More than enough as fallback |

**Total project cost: $0**

---

## Judging Criteria Alignment

| Criteria | How This Project Nails It |
|---|---|
| **Innovation** | Multi-agent AI collaboration is bleeding edge — most teams won't attempt it |
| **Technical Complexity** | Agent orchestration, real-time comms, tool use, memory management |
| **Real-world Impact** | Directly applicable to every business on the planet |
| **Demo Quality** | Highly visual, real-time, interactive — judges can see agents collaborating live |
| **Completeness** | Full system: agents, orchestration, dashboard, analytics |
| **Scalability** | Architecture supports adding new agents, tools, and companies |

---

## Quick Reference: What to Tell Claude Code

When you start building in Claude Code, feed it this context:

> "I'm building an Autonomous Enterprise AI Workforce platform for a hackathon.
> Tech stack: Next.js 14 + Tailwind + shadcn/ui frontend, Python FastAPI backend, Supabase database, Google Gemini 2.5 Pro (orchestrator) + Gemini 2.5 Flash (agents) + Groq Llama 3.3 70B (fallback). All free tier.
> The system has 5 AI agents (HR, Sales, Finance, Support, Ops) that communicate with each other via a message bus to complete complex business tasks.
> Start with [specific phase/file you want to build]."

Then work through the phases in order. Reference this blueprint for architecture decisions.

---

*Good luck. Go build something that makes the judges forget every other project they saw.* 🚀
