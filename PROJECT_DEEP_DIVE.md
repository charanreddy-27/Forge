# Forge — Project Deep Dive

A closer look at how Forge is built: the architecture, the data flow, the folder structure,
and how the genuinely hard parts actually work. If the README is the elevator pitch, this is
the whiteboard session.

---

## 1. The problem, precisely

Workflow engines (n8n, Zapier, Airflow) all solve *execution*. None of them solve the loop
around execution:

1. **Authoring** still means clicking around a UI or hand-writing JSON.
2. **Safety** is on you — nothing stops you from shipping a workflow that deletes a table.
3. **Failure** is a notification, not a resolution. You still wake up and debug it.

Forge closes that loop with an agent layer that authors, validates, deploys, monitors, and
repairs — with humans gating only the risky moves.

---

## 2. Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│  Next.js dashboard (control surface)                                │
│  workflows · runs · incidents · costs · chat                        │
└───────────────┬────────────────────────────────────────────────────┘
                │  HTTP (proxied via /api/forge/[...path])
┌───────────────▼────────────────────────────────────────────────────┐
│  FastAPI agent layer  (STATELESS — scales horizontally)             │
│                                                                     │
│  generator ── validator ── engine_adapter ── run-monitor ── diagnostician
│      │            │              │                │              │   │
│      └── all model calls ──►  LLM Gateway  ◄──────┴──────────────┘   │
│                              (cost log · budget · retries · Ollama)  │
└───────┬───────────────────────────────┬────────────────────────────┘
        │                               │
┌───────▼─────────┐            ┌────────▼─────────┐        ┌──────────────┐
│  PostgreSQL 16  │            │     Redis 7      │        │  n8n engine  │
│  registry·runs  │            │  job queue·cache │        │  (REST only) │
│  incidents·cost │            └──────────────────┘        └──────────────┘
│  audit trail    │
└─────────────────┘
```

**The load-bearing design decision: the agent layer holds no state.** Every workflow version,
run, incident, LLM call, and audit entry lives in Postgres; the job queue lives in Redis. That
means any number of API replicas and workers can run side by side — the horizontal-scale story
is free because it was designed in on day one, not bolted on.

**The engine is swappable.** All n8n-specific logic is quarantined in an `engine_adapter`
module. Nothing else in the codebase knows what the execution engine is. Swapping n8n for
another runtime is one module, not a rewrite.

---

## 3. Data flow: one instruction, end to end

1. You type an instruction in the dashboard chat box → `POST /generate`.
2. The API **enqueues a job on Redis** and returns a `job_id` immediately. Generation is an
   LLM round-trip; it must never block the request.
3. A **generation worker** pulls the job, calls the LLM Gateway to turn the instruction into
   n8n workflow JSON.
4. The **validator** runs statically: do the node types exist? Do connections resolve? Are
   credentials referenced correctly? Is there a destructive action without an approval flag?
5. If valid (and `deploy=true`), the **engine adapter** deploys it to n8n via REST and records
   an immutable **version** in the registry — writing a backup + audit entry first.
6. The **run monitor** polls n8n executions, ingests runs, and computes per-workflow health
   (success rate, failure streaks, last-run status).
7. On a failure, the **diagnostician** pulls the execution logs + the workflow definition,
   produces a root-cause analysis, and proposes a patch. A **risk rubric** decides: low-risk
   patches auto-apply; anything risky becomes an incident `awaiting_approval` in the dashboard.

The dashboard polls the job to completion and surfaces the result inline.

---

## 4. The hard parts (and how they work)

### 4.1 Never trust generated JSON

An LLM will happily emit a workflow that *looks* right and is subtly broken — a node type that
doesn't exist, a dangling connection, a credential reference to nothing, or a delete step with
no guard. The **validator** is the real product here, not the generator. It statically checks
the graph against the engine's known node types, resolves every connection, verifies
credential references, and refuses destructive actions unless an explicit `allow_destructive`
flag was set. Generation without validation is a liability, so validation is mandatory and runs
before anything is deployed. This is covered by **golden-file tests**: known instruction →
expected workflow structure, so regressions in generation are caught deterministically.

### 4.2 Repair without recklessness

Auto-repair is genuinely useful and genuinely dangerous. The **risk rubric** (see
[docs/adr/](docs/adr/) ADR-004) scores a proposed patch. Low-risk fixes — a retry on a flaky
HTTP node, a widened backoff — apply automatically. Anything that touches credentials, deletes
data, or rewrites logic is held as an incident that waits for one-click human approval. Every
action, auto or human, writes to the audit trail *before* it executes.

### 4.3 Generation can't block the API

The API is synchronous and fast; generation is slow and variable. They're decoupled by a
**Redis job queue**. The API accepts the instruction, enqueues, and returns a `job_id`. A
separate worker process does the LLM work. This keeps the API responsive and means queued jobs
survive a restart (Redis runs with AOF persistence).

### 4.4 One throat to choke for LLM cost

Every model call in the entire system flows through a single **LLM Gateway**. It logs model,
tokens, latency, purpose, and dollars for every call to Postgres; enforces a per-service rate
limit and a hard daily budget (calls are *refused* past the cap, resetting at UTC midnight);
retries with exponential backoff; and falls back to a local Ollama model when configured. You
can't optimize what you don't measure — and you can't sleep if you can't cap it.

---

## 5. The dashboard, and demo mode

The dashboard is a Next.js 14 (App Router) app split into two surfaces that share one design
system:

- **Marketing site** (`app/(marketing)`) — the landing page (with a hand-rolled Canvas 3D
  workflow constellation), About Me, and About the Project.
- **Dashboard** (`app/dashboard`) — the real control surface: overview, incident feed, cost
  charts, per-workflow run timeline, and the chat box.

**Demo mode** is what lets the whole thing live on Vercel with no backend. Server components
call `lib/api.ts`; when `FORGE_API_URL` is unset (the Vercel case), every fetcher returns the
seeded dataset in `lib/demo.ts` instead of hitting the network — and even in live mode, a fetch
failure degrades to that snapshot rather than 500ing the page. The interactive pieces
(`ChatPanel`, incident actions) simulate the agent locally when `NEXT_PUBLIC_FORGE_DEMO=1`. The
result: a recruiter clicks the live link and explores a fully working product, while the same
code talks to a real agent layer under docker-compose.

The 3D hero is deliberately **not** Three.js — it's a single `<canvas>` rendering a
perspective-projected graph with signal pulses travelling the edges. Zero heavy dependencies
keeps first-load JS around ~100 kB and the build bulletproof.

---

## 6. Folder structure

```
Forge/
├── agent-layer/                 # FastAPI backend (the brain)
│   ├── forge/
│   │   ├── api/                 # route handlers: workflows, generation, monitoring, incidents, costs
│   │   ├── generator/           # NL → workflow JSON
│   │   ├── validator/           # static validation
│   │   ├── engine_adapter/      # the ONLY place that knows about n8n
│   │   ├── registry/            # versioned workflow registry + rollback
│   │   ├── diagnostician/       # root-cause analysis + patch proposals
│   │   ├── jobs/                # Redis queue + generation worker
│   │   ├── monitor/             # run ingestion + health
│   │   ├── db/                  # SQLAlchemy models
│   │   └── config.py            # settings (env-driven)
│   ├── alembic/                 # migrations
│   └── tests/                   # pytest + golden-file tests
├── dashboard/                   # Next.js 14 dashboard + marketing site
│   ├── app/
│   │   ├── (marketing)/         # landing, /about, /about-project
│   │   ├── dashboard/           # overview, incidents, costs, workflows/[id]
│   │   ├── api/forge/[...path]/ # proxy to the agent layer
│   │   ├── layout.tsx           # fonts, SEO, OG image
│   │   └── opengraph-image.tsx
│   ├── components/
│   │   ├── site/                # marketing sections + 3D hero canvas
│   │   └── ui/                  # icons, reveal-on-scroll
│   └── lib/                     # api.ts, demo.ts, profile.ts
├── docs/                        # architecture.md, adr/, api.md, runbook.md
├── loadtest/                    # k6 / load-test scripts
└── docker-compose.yml           # the whole platform, one command
```

---

## 7. What I'd build next

- **Streaming generation** — stream the workflow JSON as it's produced instead of polling a job.
- **Patch simulation** — dry-run a proposed repair against recorded inputs before applying it.
- **Multi-engine adapters** — prove the swap by adding a second execution backend behind the
  existing adapter interface.
- **Semantic diff on versions** — show *what changed* between workflow versions, not just JSON.

See [INTERVIEW_PREP.md](INTERVIEW_PREP.md) for the narrated version of all of this.
