"use client";

// The chat box: natural-language instruction → POST /generate → poll the job.
// In demo mode (no backend) it simulates the agent's staged progress locally so
// the interaction feels real on the live site.
import { useEffect, useRef, useState } from "react";
import { Sparkles } from "@/components/ui/icons";

interface Job {
  job_id: string;
  status: string;
  result?: {
    workflow_id?: string;
    reason?: string;
    validation?: { errors?: string[] };
  } | null;
  error?: string | null;
}

const TERMINAL = new Set(["succeeded", "failed", "requires_approval"]);

const SUGGESTIONS = [
  "Watch ML job feeds every morning and draft cold emails to the hiring managers",
  "Summarize my starred RSS items into a daily digest email",
  "Ping my public endpoints hourly and alert Slack if any drift",
];

// `demo` comes from the server (it knows whether a backend is configured), so no
// client-side env var is required for demo mode to work out of the box.
export default function ChatPanel({ demo = true }: { demo?: boolean }) {
  const [instruction, setInstruction] = useState("");
  const [deploy, setDeploy] = useState(true);
  const [allowDestructive, setAllowDestructive] = useState(false);
  const [job, setJob] = useState<Job | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);
  const timeouts = useRef<ReturnType<typeof setTimeout>[]>([]);

  useEffect(() => () => stopPolling(), []);

  function stopPolling() {
    if (timer.current) clearInterval(timer.current);
    timer.current = null;
    timeouts.current.forEach(clearTimeout);
    timeouts.current = [];
  }

  // Demo: fake the queued → generating → validating → deployed progression.
  function simulate() {
    const jobId = crypto.randomUUID();
    const stages: Job[] = [
      { job_id: jobId, status: "queued" },
      { job_id: jobId, status: "generating" },
      { job_id: jobId, status: "validating" },
      allowDestructive
        ? { job_id: jobId, status: "succeeded", result: { workflow_id: "wf_ml_jobs" } }
        : {
            job_id: jobId,
            status: "requires_approval",
            result: { reason: "Workflow contains a delete step; approve to deploy." },
          },
    ];
    // If the instruction clearly isn't destructive, just succeed.
    const finalOk: Job = { job_id: jobId, status: "succeeded", result: { workflow_id: "wf_ml_jobs" } };
    const path = /delete|remove|drop|wipe/i.test(instruction) ? stages : [...stages.slice(0, 3), finalOk];

    setSubmitting(true);
    path.forEach((stage, i) => {
      timeouts.current.push(
        setTimeout(() => {
          setJob(stage);
          if (i === path.length - 1) setSubmitting(false);
        }, i * 900),
      );
    });
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (instruction.trim().length < 5 || submitting) return;
    setJob(null);
    stopPolling();

    if (demo) {
      simulate();
      return;
    }

    setSubmitting(true);
    try {
      const response = await fetch("/api/forge/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ instruction, deploy, allow_destructive: allowDestructive }),
      });
      // No backend behind the proxy (503) → fall back to the local simulation.
      if (!response.ok) {
        simulate();
        return;
      }
      const accepted = (await response.json()) as Job;
      setJob(accepted);
      setSubmitting(false);

      timer.current = setInterval(async () => {
        const poll = await fetch(`/api/forge/generate/${accepted.job_id}`);
        const current = (await poll.json()) as Job;
        setJob(current);
        if (TERMINAL.has(current.status)) stopPolling();
      }, 2000);
    } catch {
      simulate();
    }
  }

  return (
    <section className="glass-strong rounded-3xl p-5 shadow-card sm:p-6">
      <div className="flex items-center gap-2">
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-ember-500/12 text-ember-400">
          <Sparkles className="h-4 w-4" />
        </span>
        <h2 className="font-display text-sm font-semibold text-ink">Instruct the agent</h2>
      </div>

      <form onSubmit={submit} className="mt-4 space-y-3">
        <textarea
          value={instruction}
          onChange={(event) => setInstruction(event.target.value)}
          placeholder="e.g. Watch for ML job postings on my RSS feed every morning and email me a digest"
          rows={3}
          className="field resize-none"
        />
        <div className="flex flex-wrap gap-2">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => setInstruction(s)}
              className="rounded-full border border-white/8 bg-white/[0.02] px-3 py-1 text-xs text-ink-muted transition-colors duration-200 hover:border-white/20 hover:text-ink"
            >
              {s.length > 42 ? `${s.slice(0, 42)}…` : s}
            </button>
          ))}
        </div>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex gap-4 text-xs text-ink-muted">
            <label className="flex cursor-pointer items-center gap-1.5">
              <input
                type="checkbox"
                checked={deploy}
                onChange={(event) => setDeploy(event.target.checked)}
                className="accent-ember-500"
              />
              deploy on success
            </label>
            <label className="flex cursor-pointer items-center gap-1.5">
              <input
                type="checkbox"
                checked={allowDestructive}
                onChange={(event) => setAllowDestructive(event.target.checked)}
                className="accent-ember-500"
              />
              allow destructive nodes
            </label>
          </div>
          <button
            type="submit"
            disabled={submitting || instruction.trim().length < 5}
            className="btn-primary px-5 py-2 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {submitting ? "Working…" : "Generate"}
          </button>
        </div>
      </form>

      {job && <JobStatus job={job} />}
    </section>
  );
}

function JobStatus({ job }: { job: Job }) {
  const tone =
    job.status === "succeeded"
      ? "text-run-400"
      : job.status === "failed"
        ? "text-ember-400"
        : job.status === "requires_approval"
          ? "text-amber-400"
          : "text-cyan-400";

  return (
    <div className="mt-4 rounded-xl border border-white/8 bg-base-950 p-3.5 font-mono text-xs">
      <p className="text-ink-muted">
        job <span className="text-ink-faint">{job.job_id.slice(0, 8)}</span> —{" "}
        <span className={`font-semibold ${tone}`}>{job.status.replace("_", " ")}</span>
      </p>
      {job.status === "succeeded" && job.result?.workflow_id && (
        <p className="mt-1.5 text-ink-muted">
          deployed as workflow{" "}
          <a
            href={`/dashboard/workflows/${job.result.workflow_id}`}
            className="text-ember-400 underline underline-offset-2 hover:text-ember-300"
          >
            {job.result.workflow_id}
          </a>
        </p>
      )}
      {job.status === "requires_approval" && (
        <p className="mt-1.5 text-ink-muted">{job.result?.reason}</p>
      )}
      {job.status === "failed" && (
        <ul className="mt-1.5 list-inside list-disc text-ink-muted">
          {(job.result?.validation?.errors ?? [job.error ?? "unknown error"]).map((error) => (
            <li key={error}>{error}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
