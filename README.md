# HiveMindOS

> **An AI Operating System for businesses.** Deploy a team of specialized AI agents that collaborate, delegate, and execute autonomously — visible in real time.

[![Live Demo](https://img.shields.io/badge/live%20demo-hivemindos.vercel.app-22c55e?style=for-the-badge)](https://hivemindos.vercel.app)
[![API](https://img.shields.io/badge/api-aiworkforce--backend.onrender.com-3b82f6?style=for-the-badge)](https://aiworkforce-backend.onrender.com/health)
[![GitHub](https://img.shields.io/badge/source-priyansh1210%2FHiveMindOS-181717?style=for-the-badge&logo=github)](https://github.com/priyansh1210/HiveMindOS)

One prompt → five specialised AI agents (**HR · Sales · Finance · Support · Ops**) plan, delegate to each other, and execute a full business workflow in under 90 seconds. Watch it happen live on a real-time dashboard backed by WebSockets and Postgres.

---

## Table of Contents

1. [The Problem](#the-problem)
2. [The Solution](#the-solution)
3. [Try It Right Now](#try-it-right-now)
4. [What Makes This Different](#what-makes-this-different) — *innovation*
5. [Real-World Use Cases](#real-world-use-cases) — *applicability*
6. [Architecture](#architecture) — *technical*
7. [Tech Stack](#tech-stack)
8. [Two Demo Surfaces](#two-demo-surfaces)
9. [Run Locally](#run-locally)
10. [Project Structure](#project-structure)
11. [API Reference](#api-reference)
12. [Roadmap](#roadmap)
13. [Credits](#credits)

---

## The Problem

Companies spend **60% of work hours on coordination** — emails, status meetings, approvals, hand-offs between departments. A "launch a campaign" request becomes 40 Slack messages across Sales, Finance, Ops, and HR.

Single-bot solutions can't solve this. A Sales Bot can write copy, but it can't *ask Finance for a budget*, *get sign-off from Ops on timing*, and *check with HR about team capacity* — all without you in the loop.

What if your AI workforce could talk to **each other**?

---

## The Solution

HiveMindOS is a multi-agent orchestration platform. Type a business request in natural language; an orchestrator plans it, breaks it into sub-tasks, assigns them to specialist agents, and **lets agents delegate to each other dynamically** via natural-language mentions (`→ @finance_agent: need a budget estimate`).

Every message, every status change, every task completion streams to a live dashboard. You can:

- **Dispatch a task** from the command bar and watch agents collaborate in real time
- **Chat one-on-one** with any individual agent (HR, Sales, Finance, Support, Ops) — each acts as a standalone bot
- **Replay any past task** through a timeline modal showing the full delegation graph
- **See live analytics** — task completion rate, top-agent activity, real-time event log

The hackathon brief asked for *one* targeted bot. We built the platform that makes *five* bots collaborate.

---

## Try It Right Now

**Frontend:** https://hivemindos.vercel.app
**Backend (live API):** https://aiworkforce-backend.onrender.com/docs
**Source:** https://github.com/priyansh1210/HiveMindOS

### The 30-second tour

1. Open the live URL → land on the **Agents** view, see all 5 specialists with status indicators.
2. Click any one of the three example prompts in the command bar, e.g. *"Launch a summer marketing campaign for our new product, budget under $20K"*.
3. A toast confirms dispatch. Click the **Chat** tab → watch Sales ask Finance for a budget, Finance reply with a $15K breakdown that respects your constraint, Ops cut content costs to fit, all in real time.
4. Switch to **Analytics** → see live metrics update as the task runs.
5. Switch to **Bots** → click any agent → chat with it one-on-one like a standalone product.
6. Switch to **Tasks** → click any past task → see the full subtask timeline with dependencies.

**Backup demo path** (works even if LLM quotas are exhausted): Tasks → click the "Summer Marketing Campaign" task with `Completed` status → the timeline modal shows the full collaboration replay.

> Cold-start note: Render's free tier sleeps after 15 min of inactivity. First request may take ~30 s; subsequent requests are fast.

---

## What Makes This Different

Most multi-agent demos at hackathons stop at *"watch GPT call GPT"*. We went deeper.

### 1. Mention-driven dynamic delegation
Agents don't follow a hardcoded DAG. The planner produces an initial 3–5 sub-task plan, but agents can spawn **new** sub-tasks at runtime by mentioning another agent in their response:

```
Sales Agent: "...the estimated revenue lift is $9.2M.
              → @finance_agent: please validate this forecast"
```

The orchestrator parses these mentions, deduplicates (so agents can't ping-pong forever), enforces caps (`MAX_DYNAMIC_PER_AGENT=2`, `MAX_ROUNDS=6`, `MAX_SUBTASKS=10`), and re-routes them as fresh sub-tasks. **The collaboration graph is emergent, not scripted.**

### 2. Provider-agnostic LLM failover (three providers, one call)
Every LLM call walks a sequential failover chain:

```
Gemini Flash key 1  →  Gemini Flash key 2  →  Groq Llama 3.3 70B  →  raise
```

This isn't a wrapper around LangChain — it's ~50 lines of explicit, debuggable code in `backend/llm_client.py`. We hit a real quota wall during testing; the chain saved us. Built-in module-level `asyncio.Lock` around Gemini's global-state SDK + 45s hard timeout per call + Groq SDK `max_retries=1` mean the system **fails fast, never hangs**.

### 3. Text-protocol tool calling (no vendor lock-in)
Instead of using Gemini's native function calling (which would lock us out of Groq fallback), each agent emits structured `tool_call` JSON blocks inside fenced markdown:

````
```tool_call
{"name": "estimate_budget", "args": {"category": "marketing", "ceiling_usd": 20000}}
```
````

The agent runner parses these and dispatches to Python functions. **Same protocol works on every LLM provider.** Tool results feed back as conversation turns until the agent emits a final answer.

### 4. Two front-end surfaces, one backend
The same 5 agents power two completely different UX patterns:
- **Orchestrated mode** (`/dashboard` → CommandBar): submit a business request, multi-agent collaboration ensues
- **Direct mode** (`/dashboard/bots`): pick one agent, chat with it 1-on-1, see its tool calls live

This proves the architecture's separation of concerns — agents are independent units that orchestration *composes*, rather than being defined by the orchestration.

### 5. Real-time observability built in, not bolted on
WebSocket broadcaster (`/ws`) emits 4 event types: `connected`, `message`, `task_status`, `agent_status`. Every component (chat feed, task list, analytics activity feed, toast notifications) subscribes to the same stream and reacts independently. Stale connections are reaped on broadcast failure. **No polling, no Server-Sent Events fallback complexity.**

---

## Real-World Use Cases

Three pre-built scenarios demonstrate cross-functional collaboration that no single bot could handle:

| Scenario | What gets exercised | Real-world analogue |
|---|---|---|
| **Marketing Campaign Launch** | Sales → Finance → Ops → HR delegation, budget constraint enforcement, revenue forecasting, timeline creation | The "Q3 launch kickoff" meeting that takes 4 teams a week of email |
| **New Hire Onboarding** | HR + Ops + Finance + Support coordination, contract drafting, IT provisioning, KB seeding | Day-0 onboarding workflows that touch 5+ systems |
| **Customer Escalation** | Support + Sales + Finance triage, sentiment-aware response, retention offer calculation | The angry-VIP email that needs a CSM, AE, and Finance approval in 24h |

Each one is one click from the dashboard command bar.

### Mapping to common bot categories

| Bot category from the brief | What we ship |
|---|---|
| Sales Bot | **Sales Agent** — competitor analysis, proposals, outreach, revenue forecasting |
| Support Chat Bot | **Support Agent** — ticketing, KB search, response drafting, escalation |
| Customer Care Bot | **Support Agent** in retention mode — handles the angry-customer scenario above |
| (Bonus) HR Bot | **HR Agent** — hiring, onboarding, policy lookups |
| (Bonus) Finance Bot | **Finance Agent** — budgeting, ROI, financial forecasting |
| (Bonus) Ops Bot | **Ops Agent** — task management, scheduling, reporting |

You get the three asked-for bots **plus three more, all able to talk to each other**.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                       NEXT.JS 16 FRONTEND                     │
│  Agents Grid · Bots Chat · Tasks Timeline · Live Analytics    │
└────────────────┬─────────────────────────────────┬───────────┘
                 │ REST                       WebSocket
                 ▼                                 ▼
┌──────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND                          │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐     │
│  │              Orchestrator Engine                    │     │
│  │  Planner (Gemini Flash, JSON-mode, auto-repair)     │     │
│  │  Executor (parallel, dependency-aware)              │     │
│  │  Mention parser → dynamic delegation                │     │
│  │  Caps: MAX_SUBTASKS=10, MAX_ROUNDS=6                │     │
│  └────┬──────┬──────┬──────┬──────┬─────────────────────┘     │
│       │      │      │      │      │                           │
│   ┌───▼──┐┌──▼───┐┌─▼────┐┌▼─────┐┌▼─────┐                   │
│   │  HR  ││Sales ││Finance││Support││ Ops │                   │
│   └──┬───┘└──┬───┘└──┬───┘└──┬────┘└──┬───┘                  │
│      └──────┴──────┴──────┴────────┴───┘                      │
│                       │                                       │
│              ┌────────▼────────┐                              │
│              │  Message Bus    │ ──► WebSocket broadcaster    │
│              │  (persists +    │ ──► In-memory inbox cache    │
│              │   broadcasts)   │                              │
│              └────────┬────────┘                              │
│                       │                                       │
│       ┌───────────────┴───────────────┐                       │
│       ▼                               ▼                       │
│  ┌─────────────┐              ┌───────────────────┐           │
│  │ LLM Client  │              │   Supabase        │           │
│  │ Gemini ×2 → │              │   Postgres + RT   │           │
│  │ Groq tail   │              │                   │           │
│  └─────────────┘              └───────────────────┘           │
└──────────────────────────────────────────────────────────────┘
```

### Request lifecycle

1. **User submits prompt** → `POST /api/tasks`
2. **Planner** (Gemini Flash, JSON mode) decomposes into 3–5 dependency-aware sub-tasks
3. **Engine** dispatches sub-tasks in parallel (respecting `depends_on`), each to its assigned agent
4. **Agent** runs its prompt loop: think → call tools → emit response or `→ @other_agent` mentions
5. **Bus** persists every message to Postgres AND broadcasts over WebSocket
6. **Orchestrator** parses mentions, spawns new sub-tasks (capped, deduped), repeats
7. **Final summary** posted to user when all sub-tasks settled

### Failure handling
- LLM provider down → cascading failover (Gemini key 1 → key 2 → Groq)
- Provider hangs → 45 s hard timeout per call (`asyncio.wait_for`)
- Agent infinite loop → `MAX_ROUNDS=6`, `MAX_DYNAMIC_PER_AGENT=2`, mention deduplication
- Planner produces invalid JSON → auto-repair retry, then surface error to UI as `PlannerError`
- WebSocket client dies → silent reap on next broadcast failure
- Backend cold start → `/health` endpoint always responds; frontend renders "Connecting…" pill

---

## Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | **Next.js 16** (App Router, Turbopack) + **React 19** + **TypeScript 5** + **Tailwind 4** + **Recharts 3** | Server components for fast SSR; client components only where interactivity demands |
| Backend | **Python 3.11 + FastAPI** + **Pydantic v2** + **uvicorn** | Async-native, automatic OpenAPI, strict request validation |
| LLM (primary) | **Google Gemini 2.5 Flash** (×2 keys) | Fast + generous free tier; JSON mode for the planner |
| LLM (fallback) | **Groq Llama 3.3 70B** | Sub-second TTFT, deep free quota |
| Database | **Supabase Postgres** + Realtime publication | Free tier, RLS-ready, websocket-native |
| Persistence | Tables: `companies`, `agents`, `tasks`, `messages`, `knowledge`, `activity_log` | See `database/schema.sql` |
| Realtime | **FastAPI WebSocket** broadcaster | Single endpoint `/ws`, 4 event types |
| Hosting (FE) | **Vercel** — `hivemindos.vercel.app` | Native Next 16, instant rollback |
| Hosting (BE) | **Render** Blueprint — `aiworkforce-backend.onrender.com` | One-click from `backend/render.yaml` |

**Total operating cost:** $0. Every service is on a free tier.

---

## Two Demo Surfaces

| Surface | URL | What it shows |
|---|---|---|
| **Orchestrated workflow** | `/dashboard` → click chip → switch to `/dashboard/chat` | Multi-agent collaboration: agent-to-agent delegation, constraint enforcement, real-time message stream |
| **Direct per-agent chat** | `/dashboard/bots` | Each agent as a standalone bot; tool calls visible; per-agent memory + reset |
| **Past-task replay** | `/dashboard/tasks` → click any | Full subtask timeline with dependencies, agent assignments, expandable results |
| **Live analytics** | `/dashboard/analytics` | Donut + bar chart + scrolling event log driven by the same WebSocket stream |

---

## Run Locally

### Prerequisites
- **Python 3.11** (3.12 also works)
- **Node.js 20+**
- Free API keys: [Gemini](https://aistudio.google.com/apikey) (one minimum, two recommended for failover), [Groq](https://console.groq.com)
- A [Supabase](https://supabase.com) project (free tier)

### 1. Clone & configure

```bash
git clone https://github.com/priyansh1210/HiveMindOS.git
cd HiveMindOS
cp .env.example backend/.env   # fill in API keys + Supabase creds
```

### 2. Seed the database

In your Supabase SQL editor, run `database/schema.sql` then `database/seed.sql`. This creates the `NovaTech Inc.` demo workspace with 5 agents and seed knowledge.

### 3. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate           # PowerShell — use .venv/bin/activate on Unix
pip install -r requirements.txt
python main.py                   # http://localhost:8000
```

Visit `http://localhost:8000/docs` for the interactive OpenAPI playground.

### 4. Frontend

```bash
cd frontend
npm install
npm run dev                      # http://localhost:3000
```

### 5. Dispatch your first task

Open `http://localhost:3000`, click the *"Launch a summer marketing campaign…"* chip, switch to the **Chat** tab, and watch the agents collaborate.

### Quota check (run before any live demo)

```bash
cd backend
python scripts/quota_check.py    # prints OK/FAIL for Gemini and Groq
```

---

## Project Structure

```
HiveMindOS/
├── backend/                         # FastAPI service
│   ├── main.py                      # App factory + healthcheck
│   ├── config.py                    # Pydantic Settings, CSV-parsed CORS
│   ├── llm_client.py                # 3-provider failover chain
│   ├── Procfile                     # web: uvicorn …
│   ├── render.yaml                  # One-click Render Blueprint
│   ├── routers/
│   │   ├── tasks.py                 # POST /api/tasks (plan + execute)
│   │   ├── agents.py                # CRUD + /roles/{role}/invoke
│   │   ├── messages.py              # GET /api/messages
│   │   ├── analytics.py             # /tasks, /agents, /activity
│   │   └── websocket.py             # /ws broadcaster
│   ├── agents/
│   │   ├── base.py                  # Agent run loop + memory
│   │   ├── registry.py              # In-process singleton registry
│   │   ├── {hr,sales,finance,support,ops}.py
│   │   └── tools/                   # 25 LLM-backed fake tools
│   ├── orchestrator/
│   │   ├── planner.py               # JSON-mode plan decomposition
│   │   ├── engine.py                # Parallel, mention-driven executor
│   │   └── bus.py                   # Persist + broadcast + inbox cache
│   ├── database/
│   │   ├── client.py                # Supabase client (graceful no-op)
│   │   └── models.py                # Pydantic models matching schema
│   └── scripts/
│       ├── quota_check.py           # Pre-demo provider probe
│       ├── run_demo_scenarios.py    # Batch-run all 3 scenarios
│       └── run_one_scenario.py      # Single-scenario re-test
│
├── frontend/                        # Next.js 16
│   └── src/
│       ├── app/
│       │   ├── layout.tsx           # Root metadata + dark theme
│       │   └── dashboard/
│       │       ├── layout.tsx       # Sidebar + Header + LiveToaster + ToastProvider
│       │       ├── page.tsx         # Agent Grid + CommandBar
│       │       ├── bots/page.tsx    # Direct per-agent chat
│       │       ├── chat/page.tsx    # Live multi-agent feed
│       │       ├── tasks/page.tsx   # Task list + TaskDetail modal
│       │       └── analytics/page.tsx
│       ├── components/
│       │   ├── layout/              # Sidebar, Header, CommandBar, LiveToaster, BackendStatus
│       │   ├── agents/              # AgentCard, AgentGrid
│       │   ├── bots/                # BotsPanel, AgentSelector, AgentChat
│       │   ├── chat/                # ChatFeed, MessageBubble, TypingIndicators
│       │   ├── tasks/               # TaskCard, TaskTimeline, TaskList, TaskDetail
│       │   └── analytics/           # StatTile, TaskStatusChart, AgentPerformanceChart, LiveActivityFeed
│       ├── hooks/useLiveEvents.ts   # WebSocket subscriber with auto-reconnect
│       └── lib/
│           ├── api.ts               # Typed REST client
│           ├── types.ts             # TS mirrors of backend models
│           └── toast.tsx            # Provider + hook for notifications
│
├── database/
│   ├── schema.sql                   # Postgres schema + Realtime publication
│   └── seed.sql                     # NovaTech demo workspace
│
├── DEMO.md                          # 3-minute pitch script + quota recipe
└── README.md                        # You are here
```

---

## API Reference

Auto-generated OpenAPI docs live at: **https://aiworkforce-backend.onrender.com/docs**

Highlights:

| Endpoint | Purpose |
|---|---|
| `POST /api/tasks` | Submit a user prompt; planner + orchestrator run in background |
| `GET /api/tasks` / `GET /api/tasks/{id}` | List or fetch a task with plan + result |
| `GET /api/agents` | List all agents (id, role, color, status, system_prompt) |
| `POST /api/agents/roles/{role}/invoke` | Direct single-agent invocation (no orchestrator) |
| `POST /api/agents/roles/{role}/reset` | Clear an agent's memory |
| `GET /api/messages?task_id=…` | Full message trail for a task |
| `GET /api/analytics/tasks` | Aggregate task metrics |
| `GET /api/analytics/agents` | Per-agent activity (messages sent, tasks touched) |
| `WS  /ws` | Live event stream: `connected`, `message`, `task_status`, `agent_status` |

---

## Roadmap

The platform was designed to extend without orchestration rewrites.

**Near-term**
- Pause/resume per-agent control (endpoint exists; orchestrator skip logic pending)
- Token-usage instrumentation in `activity_log` for cost dashboards
- Live agent-status reflection on the dashboard grid (needs client wrapper)

**Phase 2 — production hardening**
- Swap fake tools for real integrations: Slack, Linear, HubSpot, Stripe, Calendar
- Per-tenant RLS (Supabase) — currently single-workspace demo
- Auth (Supabase Auth or Clerk)
- Add new specialist agents in ~80 LOC each (Engineering, Legal, Procurement, BD)

**Phase 3 — agent autonomy**
- Cron-triggered tasks (the agents wake themselves up)
- Inter-task memory: agents recall prior collaborations
- Cost-aware planner: choose cheaper models for low-stakes sub-tasks

---

## Credits

Built solo over 10 days by **[@priyansh1210](https://github.com/priyansh1210)** for the hackathon.

Stack credits: [FastAPI](https://fastapi.tiangolo.com), [Next.js](https://nextjs.org), [Supabase](https://supabase.com), [Google Gemini](https://aistudio.google.com), [Groq](https://groq.com), [Recharts](https://recharts.org), [Tailwind CSS](https://tailwindcss.com).

Inspired by the realization that the productivity bottleneck in modern companies isn't *doing the work* — it's *coordinating who does the work*. We think that's a job for an AI workforce.

---

<p align="center">
  <strong>One prompt. Five agents. Real collaboration.</strong><br>
  <a href="https://hivemindos.vercel.app">Try it live →</a>
</p>
