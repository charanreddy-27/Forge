# ADR-004: Patch risk rubric (diagnostician auto-repair)

**Status:** Accepted — 2026-07-07 (Phase 4)

## Context

When a run fails, the diagnostician asks the LLM for a root-cause analysis and, when the failure is fixable by editing the workflow, a patch (a full corrected definition). Applying LLM-authored patches automatically is the point of Forge — but also its biggest hazard. We need a deterministic line between "apply it" and "ask a human", and it must not rely on the LLM's own confidence claims.

## Decision

**Mechanical, shape-based rubric.** A patch is first validated like any generated workflow (schema, node whitelist, connections, credential hygiene — an invalid patch is discarded outright and an OPEN incident filed). A valid patch is then compared structurally against the currently deployed definition:

| # | Rule | Risk |
|---|---|---|
| 1 | Introduces destructive behavior absent before — a new email/Slack/Gmail node, or an existing `httpRequest` changing from GET/HEAD to a mutating method | **HIGH** |
| 2 | Changes what triggers the workflow (schedule ↔ webhook ↔ manual) | **HIGH** |
| 3 | Restructures the workflow: more than 2 nodes added + removed combined | **HIGH** |
| 4 | Touches credentials: changes a node's credential reference, or adds a node carrying one | **HIGH** |
| 5 | Anything else — parameter fixes (URLs, expressions, schedules), connection corrections, small non-destructive additions | **LOW** |

**LOW → auto-apply** (when `DIAGNOSTICIAN_AUTO_APPLY=true`, the default): the patch is deployed through the registry, which by construction creates the versioned backup and audit entry (ADR-002); a RESOLVED incident records the analysis and the applied patch. **HIGH → incident `awaiting_approval`** with the patch attached; `POST /incidents/{id}/approve` applies it (again via the registry), `.../dismiss` discards it. With auto-apply off, even LOW-risk patches park for approval.

The rubric asks "what does this change *do*", not "how big is the diff": rules 1–4 are exactly the ways a repair can act on the outside world differently (new side effects, different activation, different identity) or stop being a repair (a rewrite). A one-line diff that flips GET to POST is HIGH; a 50-line diff fixing URLs across nodes is LOW.

## Consequences

- ✅ Deterministic and unit-testable (`tests/test_risk.py` covers every rule) — no LLM in the decision loop.
- ✅ Auto-repair is never silently destructive: the worst a LOW patch can do is keep failing, and every application is a rollbackable version + audit row.
- ✅ Conservative by default: false HIGHs cost a human click; false LOWs are bounded by rule 1 (no new side effects) and one-call rollback.
- ⚠️ The rubric can't see *semantic* changes inside parameters (e.g. a different recipient on an email node that already existed). Mitigation: the node was already destructive and approved once; tighten by adding per-field rules if this bites.
- ⚠️ Thresholds (2-node delta) are judgment calls; tune them in `forge/diagnostician/risk.py` as real incidents accumulate.
