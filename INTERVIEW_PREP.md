# Forge — Interview Prep

Everything you need to talk about Forge convincingly. Rehearse the pitches out loud until they
feel like yours, not a script.

---

## The 30-second elevator pitch

> Forge is a self-hosted AI operations platform. You describe an automation in plain English —
> "watch for ML job posts daily and draft cold emails" — and an agent layer generates a valid
> n8n workflow, validates it, deploys it, and monitors every run. When something fails, a
> diagnostic agent finds the root cause and either auto-repairs it or files an incident with a
> proposed patch for me to approve. n8n runs workflows; Forge is the brain that authors and
> operates them.

---

## The 2-minute walkthrough

> Most workflow tools solve execution but leave you three jobs: authoring, safety, and failure
> recovery. Forge automates all three.
>
> **The stack is four clean layers.** A Next.js dashboard on top; a stateless FastAPI agent
> layer that's the brain; Postgres and Redis for state and the job queue; and n8n as a
> swappable execution engine, driven only through its REST API behind an adapter module.
>
> **The flow:** I type an instruction. The API enqueues a Redis job and returns immediately —
> generation is an LLM round-trip, so it can't block the request. A worker turns the
> instruction into n8n workflow JSON, then a static validator checks it: do the node types
> exist, do connections resolve, are credentials referenced correctly, is there anything
> destructive without an approval flag? Only then does it deploy — as an immutable version in
> a registry, with a backup and an audit entry written first, so rollback is one API call.
>
> **After deploy**, a run monitor ingests executions and computes health. On a failure, a
> diagnostician pulls the logs and the definition, writes a root cause, and proposes a patch. A
> risk rubric decides whether it auto-applies or waits for me. Nothing destructive ever happens
> silently.
>
> **One detail I'm proud of:** every LLM call in the system flows through a single gateway that
> logs tokens, latency, and cost, enforces a hard daily budget, retries with backoff, and can
> fall back to a local Ollama model. Cost is a first-class metric, not an afterthought.
>
> **And it's designed to scale:** the agent layer is completely stateless, so API replicas and
> workers scale horizontally — that was a day-one decision, not a retrofit.

---

## STAR stories

### STAR 1 — Trusting generated output (the validator)

- **Situation:** Getting an LLM to emit workflow JSON was quick. Trusting it was not — I was
  getting half-valid graphs, phantom node types, and a delete step with no guard.
- **Task:** Make generated workflows safe to deploy automatically.
- **Action:** I built a static validator that runs before any deploy: it checks node types
  against the engine's known set, resolves every connection, verifies credential references,
  and blocks destructive actions unless an explicit approval flag is set. I locked the behavior
  in with golden-file tests — known instruction → expected structure — so generation
  regressions are caught deterministically.
- **Result:** Generation went from "impressive demo" to "safe to run unattended." The validator,
  not the generator, is the part that makes the whole system trustworthy.

### STAR 2 — Auto-repair without recklessness (the risk rubric)

- **Situation:** Auto-repair is the headline feature and also the scariest one — an agent
  editing production workflows.
- **Task:** Let the system fix failures on its own without ever making a dangerous change
  silently.
- **Action:** I designed a risk rubric (documented as an ADR) that scores each proposed patch.
  Low-risk fixes — a retry on a flaky HTTP node, a wider backoff — auto-apply. Anything touching
  credentials, deleting data, or rewriting logic becomes an incident that waits for one-click
  approval. Every action writes to an audit trail before it runs.
- **Result:** The common, boring failures fix themselves; the rare, dangerous ones stop and ask.
  I get the automation benefit without handing an agent an unsupervised delete key.

### STAR 3 — Keeping the API fast (the job queue)

- **Situation:** Generation takes seconds and is variable; the API needs to be instant.
- **Task:** Decouple the slow LLM work from request/response.
- **Action:** Generation runs as a Redis-queued background job. The API accepts the instruction,
  enqueues it, and returns a job id; a separate worker does the LLM work; the dashboard polls to
  completion. Redis runs with AOF persistence so queued jobs survive a restart.
- **Result:** The API stays responsive under load, and generation work is durable and
  independently scalable.

---

## Likely technical Q&A

**Q: Why n8n instead of building your own executor?**
Execution is a solved problem and a deep rabbit hole. n8n gives me a mature engine for free.
The interesting work is the loop around it — authoring, validation, repair — so I put my
effort there and kept n8n behind an adapter so it's swappable.

**Q: How do you keep the agent layer stateless?**
No in-process state at all. Every workflow version, run, incident, LLM call, and audit entry is
in Postgres; the job queue and cache are in Redis. Any replica can serve any request, which is
what makes horizontal scaling trivial.

**Q: What stops the agent from doing something destructive?**
Two gates. The validator blocks destructive node actions at generation time unless an explicit
approval flag is set. The diagnostician's risk rubric blocks risky *repairs* at runtime, holding
them for human approval. And overwrites/deletes always write a versioned backup + audit entry
first — rollback is one API call.

**Q: How do you control LLM cost?**
One gateway that every call passes through. It logs tokens/latency/cost per call, enforces a
per-service rate limit and a hard daily budget (calls are refused past the cap), retries with
exponential backoff, and can fall back to local Ollama.

**Q: How is generation tested?**
Golden-file tests: a set of known instructions with expected workflow structures. Plus unit
tests per agent service. The validator has explicit cases for invalid node types, broken
connections, and unguarded destructive actions.

**Q: The live demo has no backend — how?**
Demo mode. Server components read through a data layer that returns a seeded dataset when
`FORGE_API_URL` is unset, and the interactive components simulate the agent client-side. The
same code talks to the real FastAPI agent layer under docker-compose. So the Vercel deployment
is a fully explorable product with zero infrastructure.

**Q: Why a hand-rolled canvas for the hero instead of Three.js?**
Reliability and weight. The 3D workflow constellation is a single `<canvas>` with a
perspective-projected graph — no WebGL dependency, ~100 kB first load, and nothing to break in
the build. It also honors `prefers-reduced-motion`.

**Q: How would this scale to thousands of workflows?**
The monitor and workers are independent processes that scale out; Postgres holds the state;
Redis holds the queue. The bottleneck becomes n8n and the database, both of which scale with
standard techniques (read replicas, partitioning runs by time). Nothing in the agent layer has
to change.

---

## What I'd improve next

- Stream generation output instead of polling a job.
- Dry-run proposed patches against recorded inputs before applying them.
- Add a second execution engine behind the adapter to *prove* the swap, not just claim it.
- Semantic diffing between workflow versions so the timeline shows what changed, not raw JSON.

---

## Smart questions to ask the interviewer

- Where does the team draw the line today between agent autonomy and human approval?
- How do you measure and cap LLM cost across services right now?
- What's your approach to testing non-deterministic (LLM) components in CI?
- When a background job system fails, how do you make the work durable and observable?
- What does "stateless service" discipline look like on your team in practice?
