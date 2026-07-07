"use client";

// The chat box: natural-language instruction → POST /generate → poll the job.
import { useEffect, useRef, useState } from "react";

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

export default function ChatPanel() {
  const [instruction, setInstruction] = useState("");
  const [deploy, setDeploy] = useState(true);
  const [allowDestructive, setAllowDestructive] = useState(false);
  const [job, setJob] = useState<Job | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => () => stopPolling(), []);

  function stopPolling() {
    if (timer.current) clearInterval(timer.current);
    timer.current = null;
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (instruction.trim().length < 5 || submitting) return;
    setSubmitting(true);
    setJob(null);
    stopPolling();

    const response = await fetch("/api/forge/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ instruction, deploy, allow_destructive: allowDestructive }),
    });
    const accepted = (await response.json()) as Job;
    setJob(accepted);
    setSubmitting(false);

    timer.current = setInterval(async () => {
      const poll = await fetch(`/api/forge/generate/${accepted.job_id}`);
      const current = (await poll.json()) as Job;
      setJob(current);
      if (TERMINAL.has(current.status)) stopPolling();
    }, 2000);
  }

  return (
    <section className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
      <h2 className="text-sm font-semibold text-zinc-300">Instruct the agent</h2>
      <form onSubmit={submit} className="mt-3 space-y-3">
        <textarea
          value={instruction}
          onChange={(event) => setInstruction(event.target.value)}
          placeholder="e.g. Watch for ML job postings on my RSS feed every morning and email me a digest"
          rows={3}
          className="w-full resize-none rounded-lg border border-zinc-700 bg-zinc-950 p-3 text-sm placeholder:text-zinc-600 focus:border-orange-600 focus:outline-none"
        />
        <div className="flex items-center justify-between">
          <div className="flex gap-4 text-xs text-zinc-400">
            <label className="flex items-center gap-1.5">
              <input
                type="checkbox"
                checked={deploy}
                onChange={(event) => setDeploy(event.target.checked)}
                className="accent-orange-600"
              />
              deploy on success
            </label>
            <label className="flex items-center gap-1.5">
              <input
                type="checkbox"
                checked={allowDestructive}
                onChange={(event) => setAllowDestructive(event.target.checked)}
                className="accent-orange-600"
              />
              allow destructive nodes
            </label>
          </div>
          <button
            type="submit"
            disabled={submitting || instruction.trim().length < 5}
            className="rounded-lg bg-orange-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-orange-500 disabled:opacity-40"
          >
            Generate
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
      ? "text-emerald-400"
      : job.status === "failed"
        ? "text-red-400"
        : job.status === "requires_approval"
          ? "text-orange-400"
          : "text-sky-400";

  return (
    <div className="mt-4 rounded-lg border border-zinc-800 bg-zinc-950 p-3 text-xs">
      <p>
        job <span className="font-mono text-zinc-500">{job.job_id.slice(0, 8)}</span> —{" "}
        <span className={`font-semibold ${tone}`}>{job.status.replace("_", " ")}</span>
      </p>
      {job.status === "succeeded" && job.result?.workflow_id && (
        <p className="mt-1 text-zinc-400">
          deployed as workflow{" "}
          <a href={`/workflows/${job.result.workflow_id}`} className="text-orange-400 underline">
            {job.result.workflow_id.slice(0, 8)}
          </a>
        </p>
      )}
      {job.status === "requires_approval" && (
        <p className="mt-1 text-zinc-400">{job.result?.reason}</p>
      )}
      {job.status === "failed" && (
        <ul className="mt-1 list-inside list-disc text-zinc-400">
          {(job.result?.validation?.errors ?? [job.error ?? "unknown error"]).map((error) => (
            <li key={error}>{error}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
