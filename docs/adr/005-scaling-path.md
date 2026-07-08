# ADR-005: Scaling path

**Status:** Accepted — 2026-07-07 (Phase 6)

## Context

Forge is a personal platform today: one box, `docker compose up`, single-digit workflows. The scalability requirements in CLAUDE.md were design constraints from day one (stateless services, queue-backed generation, budget as shared state), not features. This ADR records how the current design scales and in what order to spend effort if load grows — so future changes extend the path instead of rediscovering it.

## Decision

**Scale by adding processes, not by changing architecture.** The design already permits it:

1. **Stateless services** — the API, generation worker, and run monitor keep no in-process state. `docker compose up --scale agent-layer=3 --scale generation-worker=4` works today: BRPOP hands each queued job to exactly one worker; run-sync and diagnosis are idempotent (upsert by execution id, one unresolved incident per run), so overlapping monitor instances converge rather than duplicate.
2. **Shared-state controls in Postgres** — the daily budget and per-service rate limits are computed from the `llm_calls` table, so N gateway instances enforce one ceiling with zero coordination. This trades a small indexed query per LLM call for correctness — the right trade while LLM latency (seconds) dwarfs the query (ms).
3. **Ordered growth path** (spend effort in this order, measured by the load test):
   - **Workers first** — generation and diagnosis throughput are LLM-bound; more workers is the cheap lever.
   - **Connection pooling** — many instances × pool size exhausts Postgres connections long before CPU; add PgBouncer in front of Postgres when instance count grows.
   - **Hot-path counters to Redis** — if `llm_calls` grows to the point where the budget/rate queries show up in traces, move the *counters* to Redis (INCR + TTL windows) and keep the table as the audit log. The gateway's `budget.py` / `ratelimit.py` are the only two call sites.
   - **Partition append-only tables** — `llm_calls` and `audit_log` by month when they reach tens of millions of rows.
   - **Engine scaling** — n8n has its own queue mode (main + workers over Redis); because nothing outside `engine_adapter` knows n8n exists (ADR-001), that change is compose-only.
4. **What we deliberately did NOT build**: Kubernetes manifests, service discovery, distributed tracing, sharding. At personal-platform scale they are pure carrying cost; the load test (`loadtest/locustfile.py`) is the tripwire that tells us when that stops being true.

## Consequences

- ✅ Horizontal scaling is an operator command, not a refactor.
- ✅ Every control that must be globally consistent (budget, rate, versions, audit) already lives in shared storage.
- ✅ The upgrade path is incremental — each step replaces one bottleneck without touching the others.
- ⚠️ Postgres is the single point of coordination *by design*; it is also the single point of failure. Backups (`scripts/backup.sh`) are the mitigation until HA matters.
- ⚠️ The Redis job queue loses an in-flight job if a worker dies mid-generation (ADR-003); at higher stakes, switch `claim` to BRPOPLPUSH with a reaper. The `JobQueue` interface already isolates that change.
