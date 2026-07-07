# ADR-002: Workflow versioning strategy

**Status:** Accepted — 2026-07-07 (Phase 2)

## Context

Every workflow deploy must be reversible with one API call, agents will soon generate and repair workflows autonomously, and CLAUDE.md forbids silently destructive actions. We need to decide how versions are stored and what "rollback" means.

Options for rollback semantics:

1. **Roll-back (mutate)** — set `current_version` back to N and redeploy; versions created after N are effectively orphaned or deleted.
2. **Roll-forward (append)** — copy version N's definition into a *new* version (max+1) and deploy that.

## Decision

**Immutable, append-only versions with roll-forward rollback.**

- Every deploy inserts a `workflow_versions` row (`version = max + 1`, unique per workflow) **in the same transaction** that records the engine result — if the engine call fails, nothing is committed.
- `workflows.current_version` points at whatever is deployed right now.
- **Rollback = redeploy an old definition as a new version** with the comment `rollback to vN`. One API call: `POST /workflows/{id}/rollback {"target_version": N}`.
- Each version records `created_by` (human or agent service name), so agent-generated versions are always distinguishable.
- **Destructive actions snapshot first.** `DELETE` fetches the engine's *live* definition and stores it as a final `pre-delete backup` version before deleting — catching any drift from someone editing the n8n UI directly — and registry history survives the delete. Every deploy/rollback/activate/delete writes an `audit_log` row.

## Consequences

- ✅ History is never rewritten: after a bad deploy (v2) and rollback, the timeline reads v1 → v2 → v3(=v1's definition) — the incident is visible forever, which is exactly what the Phase 4 diagnostician and the audit trail need.
- ✅ Rollback and deploy are the same code path (one write path to test and reason about).
- ✅ A rollback can itself be rolled back, trivially.
- ⚠️ Version numbers grow monotonically and duplicate definitions exist across rows. JSON definitions are small (KBs); storage is a non-issue at personal-platform scale.
- ⚠️ "Which version is live" must be read from `workflows.current_version`, not "the highest version" — they're equal only until the first failed deploy or concurrent write. The API returns `current_version` on every workflow payload for this reason.
