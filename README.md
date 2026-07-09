<div align="center">

# ⚒ Forge

### The AI operations platform that repairs its own workflows.

Describe an automation in plain English. An agent layer generates a valid workflow,
validates it, deploys it to n8n, watches every run, and fixes failures before you notice.

[**Live demo →**](https://forge-ops.vercel.app) · [Landing page](https://forge-ops.vercel.app) · [About the project](https://forge-ops.vercel.app/about-project)

<sub>Python · FastAPI · PostgreSQL · Redis · n8n · Next.js 14 · Anthropic</sub>

</div>

---

> _"Watch for ML job postings daily and draft cold emails."_
>
> Forge turns that sentence into a schema-valid n8n workflow, deploys it as an immutable
> version, and monitors its runs. When one fails, a diagnostic agent inspects the logs and
> either auto-repairs the workflow or files a human-readable incident with a proposed patch.

### ▶ [Open the live demo](https://forge-ops.vercel.app/dashboard)

Runs entirely in your browser on realistic seeded data — no backend, no login. Click through
the overview, approve a proposed patch in the incident feed, open a workflow's run timeline,
and read the LLM cost breakdown.

## Why this isn't just n8n

n8n executes workflows. Forge is the brain on top — it decides what to build, whether it's
safe, and what to do when it breaks:

- **Workflow generator** — natural language → schema-validated n8n workflow JSON (never hand-edited in the UI)
- **Static validator** — node types exist, connections resolve, credentials are referenced correctly, and destructive actions are blocked without an explicit approval flag
- **Versioned registry** — every deploy is an immutable version; rollback is one API call, with a backup + audit entry written first
- **Run monitor + diagnostician** — failures get a root-cause analysis and a proposed patch; risky patches wait for your approval
- **LLM Gateway** — every model call passes through one module with cost logging, a hard daily budget, exponential-backoff retries, and a local Ollama fallback
- **Audit trail** — no agent action is ever silently destructive

## Try it in 15 seconds

The [live demo](https://forge-ops.vercel.app/dashboard) runs entirely in your browser on
realistic seeded data — no backend, no login. Click through the overview, the incident feed
(approve a proposed patch), a workflow's run timeline, and the LLM cost breakdown.

## Run the full platform locally

```bash
cp .env.example .env      # add your ANTHROPIC_API_KEY
docker compose up -d
```

That's it. Then:

- **Dashboard** — http://localhost:3000
- **Agent layer API** — http://localhost:8000 (docs at `/docs`, health at `/health`)
- **n8n** — http://localhost:5678

## Architecture

```
Next.js dashboard  →  FastAPI agent layer  →  PostgreSQL + Redis  →  n8n (execution engine)
   (control surface)      (stateless brain)       (state + queue)        (swappable runtime)
```

Postgres 16 (state) · Redis 7 (job queue) · n8n (execution engine) · FastAPI agent layer
(stateless brain) · Next.js dashboard. See [docs/architecture.md](docs/architecture.md) for
the system diagram and data flow, [docs/adr/](docs/adr/) for design decisions,
[docs/runbook.md](docs/runbook.md) for operations, and [docs/api.md](docs/api.md) for the API
reference.

For a deeper look: **[PROJECT_DEEP_DIVE.md](PROJECT_DEEP_DIVE.md)** (how the hard parts work),
**[DEPLOYMENT.md](DEPLOYMENT.md)** (ship the dashboard to Vercel), and
**[INTERVIEW_PREP.md](INTERVIEW_PREP.md)**.

## Status

| Phase | Scope | Status |
|---|---|---|
| 1 — Foundation | Compose stack, DB schema + migrations, LLM Gateway (cost log + budget + retries + fallback) | ✅ |
| 2 — Engine adapter + registry | n8n REST wrapper, versioned deploys, one-call rollback | ✅ |
| 3 — Workflow generator | NL → validated workflow JSON as background jobs | ✅ |
| 4 — Run monitor + diagnostician | Health tracking, root-cause analysis, auto-repair with approval gates | ✅ |
| 5 — Dashboard | Next.js UI: workflows, runs, incidents, costs, chat | ✅ |
| 6 — Hardening & scale | Rate limits, backups, structured logging, load tests | ✅ |

## Development

```bash
cd agent-layer
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/pytest -q                 # tests
.venv/bin/ruff check forge tests    # lint
.venv/bin/black forge tests         # format
.venv/bin/mypy forge                # types
```

```bash
cd dashboard
npm install
npm run dev        # http://localhost:3000 (runs in demo mode with no backend)
npm run build      # production build
```

Conventional commits (`feat:`, `fix:`, `docs:`, `refactor:`). No secrets in code —
`.env` and `.env.example` stay in sync.

---

## About the developer

**Chanda Charan Reddy** — AI & Automation Engineer, Bangalore.

I ship production LLM systems — from a Springer-published model that reads chest X-rays well
enough for a radiologist to take seriously, to document pipelines that run themselves. Before
that I wrote real-time control code for jet engines at DRDO, which is where I learned that a
system failing quietly is the most dangerous kind. Forge is that instinct applied to
automation.

Forge is one project. There are more — and a few jet engines — over at
**[charanreddy.dev](https://www.charanreddy.dev)**.

[Portfolio](https://www.charanreddy.dev) · [GitHub](https://github.com/charanreddy-27) · [LinkedIn](https://www.linkedin.com/in/chandacharanreddy/) · [Book a call](https://cal.com/charanreddy-27/30min)

<sub>Crafted with intent. Available for new projects.</sub>
