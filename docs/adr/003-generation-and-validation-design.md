# ADR-003: Workflow generation & validation design

**Status:** Accepted — 2026-07-07 (Phase 3)

## Context

The workflow-generator turns natural-language instructions into n8n workflow JSON via the LLM Gateway. LLM output is untrusted: it can be malformed, reference nodes we don't want agents using, embed secrets, or have side effects the user never approved. Generation is also slow (seconds), so it must not block API requests. Three designs needed deciding: how to constrain generation, how to validate, and how to queue.

## Decision

**1. Whitelist-driven generation from a single node catalog.**
`forge/nodes.py` is the one source of truth: a catalog of allowed n8n node types with descriptions, example parameters, and a destructive flag. The generator renders the catalog into the system prompt (with few-shot examples pinning n8n's exact JSON shape), and the validator enforces the same catalog. Prompt and enforcement can never drift apart. Growing agent capability = adding a catalog entry.

**2. Static validation with one repair round.**
`validate_workflow()` checks, in order: schema (required keys, node shape, unique names), node whitelist, connection integrity (every edge references an existing node), credential hygiene (references by `{id, name}` only; recursive scan rejects parameter keys that look like inline secrets), and destructive-action detection. Destructive = catalog-flagged types (email, Slack, Gmail) plus `httpRequest` with any method other than GET/HEAD.

If the first LLM attempt fails validation, the errors are fed back to the model **once** (`repair_prompt`). Still invalid → the job fails with the errors and the raw definition recorded for inspection. One round bounds cost (each retry is billed) while recovering the common failure modes (fences, one bad node); deeper repair is the Phase 4 diagnostician's job.

**3. Approval gate for destructive workflows.**
A valid-but-destructive workflow is only deployed when the request set `allow_destructive=true`; otherwise the job parks at `requires_approval` with the definition stored and a human-readable reason (CLAUDE.md: no destructive actions without an approval flag). The gate lives in the job handler, not the validator — validation states facts; policy is applied where deployment is decided.

**4. Minimal hand-rolled Redis queue, not a job framework.**
Generation runs on a separate worker process (`python -m forge.jobs.worker`, the `generation-worker` compose service) consuming a Redis list via BRPOP; job state lives in a per-job Redis hash with a 24h TTL (`queued → running → succeeded | failed | requires_approval`). We chose ~100 lines over rq/Celery/arq because the need is one queue with one consumer type; BRPOP already gives exactly-one-worker delivery and blocking semantics; and the approved stack lists Redis, not a job framework. Durable outcomes (workflows, versions, audit) land in Postgres via the registry — Redis only carries transient job state.

## Consequences

- ✅ LLM output is data, validated before it can touch the engine; the catalog bounds the blast radius of a bad generation.
- ✅ API stays fast: `POST /generate` returns 202 in milliseconds regardless of LLM latency; workers scale horizontally (BRPOP distributes jobs).
- ✅ Golden-file tests (`tests/golden/`) pin instruction → structure behavior; adding a case is adding a JSON file.
- ⚠️ The catalog is deliberately small (14 node types). Instructions needing other nodes will fail validation until the catalog grows — that's the intended control point, not a bug.
- ⚠️ A job crash after BRPOP but before the result write loses the in-flight job (visible as stuck `running`). Acceptable for personal-platform scale; revisit with a reliable-queue pattern (BRPOPLPUSH + janitor) in Phase 6 if needed.
- ⚠️ Job state expires after 24h; results that matter must be deployed (Postgres) or re-generated.
