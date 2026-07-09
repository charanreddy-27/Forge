// Seed data for demo mode — the dataset the dashboard renders when there's no
// backend (e.g. the Vercel deployment). It mirrors the shapes in ./api.ts so the
// UI behaves identically to production, just with static, realistic content.
import type {
  CostSummary,
  Incident,
  Run,
  Workflow,
  WorkflowHealth,
  WorkflowVersion,
} from "./api";

// A fixed "now" keeps the seeded timestamps stable across renders.
const NOW = new Date("2026-07-09T14:30:00Z").getTime();
const H = 3_600_000;
const D = 24 * H;
const iso = (msAgo: number) => new Date(NOW - msAgo).toISOString();

type Seed = {
  id: string;
  name: string;
  description: string;
  status: string;
  current_version: number;
  health: WorkflowHealth["status"];
  success_rate: number | null;
  total_runs: number;
  consecutive_failures: number;
};

const seeds: Seed[] = [
  { id: "wf_ml_jobs", name: "ml-jobs-outreach", description: "Watch ML job feeds daily, draft cold emails.", status: "active", current_version: 3, health: "healthy", success_rate: 0.98, total_runs: 61, consecutive_failures: 0 },
  { id: "wf_rss_digest", name: "rss-digest-email", description: "Summarize starred RSS items into a morning digest.", status: "active", current_version: 1, health: "healthy", success_rate: 1.0, total_runs: 44, consecutive_failures: 0 },
  { id: "wf_invoice", name: "invoice-ocr-to-sheet", description: "OCR incoming invoices, append rows to a sheet.", status: "active", current_version: 4, health: "healthy", success_rate: 0.96, total_runs: 128, consecutive_failures: 0 },
  { id: "wf_health_check", name: "hourly-health-check", description: "Ping public endpoints hourly, alert on drift.", status: "active", current_version: 5, health: "degraded", success_rate: 0.82, total_runs: 210, consecutive_failures: 1 },
  { id: "wf_slack_alert", name: "webhook-slack-alert", description: "Fan critical webhooks into a Slack channel.", status: "error", current_version: 2, health: "failing", success_rate: 0.61, total_runs: 37, consecutive_failures: 4 },
  { id: "wf_lead_enrich", name: "lead-enrichment", description: "Enrich new CRM leads with company data.", status: "active", current_version: 2, health: "healthy", success_rate: 0.99, total_runs: 89, consecutive_failures: 0 },
  { id: "wf_daily_report", name: "daily-metrics-report", description: "Roll up product metrics into a PDF at 8am.", status: "active", current_version: 6, health: "healthy", success_rate: 0.94, total_runs: 152, consecutive_failures: 0 },
  { id: "wf_pr_triage", name: "github-pr-triage", description: "Label and route new pull requests by area.", status: "active", current_version: 2, health: "degraded", success_rate: 0.88, total_runs: 73, consecutive_failures: 0 },
  { id: "wf_backup", name: "nightly-db-backup", description: "Snapshot Postgres and ship to object storage.", status: "active", current_version: 1, health: "healthy", success_rate: 1.0, total_runs: 30, consecutive_failures: 0 },
  { id: "wf_sentiment", name: "review-sentiment", description: "Score new app-store reviews, flag the angry ones.", status: "inactive", current_version: 3, health: "unknown", success_rate: null, total_runs: 0, consecutive_failures: 0 },
  { id: "wf_calendar", name: "calendar-brief", description: "Draft a morning brief from tomorrow's calendar.", status: "active", current_version: 2, health: "healthy", success_rate: 0.97, total_runs: 58, consecutive_failures: 0 },
  { id: "wf_expenses", name: "expense-categorizer", description: "Categorize card transactions, tag for taxes.", status: "active", current_version: 4, health: "healthy", success_rate: 0.93, total_runs: 96, consecutive_failures: 0 },
];

export function demoWorkflows(): Workflow[] {
  return seeds.map((s, i) => ({
    id: s.id,
    name: s.name,
    description: s.description,
    engine_workflow_id: `n8n_${1000 + i}`,
    status: s.status,
    current_version: s.current_version,
    created_at: iso((40 - i) * D),
    updated_at: iso(i * 5 * H + 2 * H),
  }));
}

export function demoWorkflow(id: string): Workflow {
  return demoWorkflows().find((w) => w.id === id) ?? demoWorkflows()[0];
}

export function demoHealth(id: string): WorkflowHealth {
  const s = seeds.find((x) => x.id === id) ?? seeds[0];
  return {
    workflow_id: s.id,
    status: s.health,
    total_runs: s.total_runs,
    success_rate: s.success_rate,
    consecutive_failures: s.consecutive_failures,
    last_run_status: s.total_runs === 0 ? null : s.consecutive_failures > 0 ? "failed" : "success",
    last_run_at: s.total_runs === 0 ? null : iso(2 * H),
  };
}

export function demoRuns(id: string): Run[] {
  const s = seeds.find((x) => x.id === id) ?? seeds[0];
  if (s.total_runs === 0) return [];
  // Recent runs: bias failures toward the top for unhealthy workflows.
  const statuses =
    s.health === "failing"
      ? ["failed", "failed", "failed", "success", "failed", "success", "success"]
      : s.health === "degraded"
        ? ["success", "failed", "success", "success", "failed", "success", "success"]
        : ["success", "success", "success", "success", "success", "success", "success"];
  return statuses.map((status, i) => ({
    id: `${s.id}_run_${i}`,
    workflow_id: s.id,
    engine_execution_id: String(90210 - i),
    status,
    started_at: iso((i * 3 + 2) * H),
    finished_at: iso((i * 3 + 2) * H - 40_000),
    error_message:
      status === "failed"
        ? "HTTP node returned 429 Too Many Requests from api.upstream.dev"
        : null,
  }));
}

export function demoVersions(id: string): WorkflowVersion[] {
  const s = seeds.find((x) => x.id === id) ?? seeds[0];
  const authors = ["agent:generator", "human:dashboard", "agent:diagnostician"];
  const comments = [
    "initial deploy from instruction",
    "adjusted schedule to 09:00",
    "auto-repair: added retry to HTTP node",
    "human review: widened rate-limit backoff",
    "auto-repair: fixed credential reference",
    "manual rollback to stable graph",
  ];
  return Array.from({ length: s.current_version }, (_, i) => {
    const v = s.current_version - i;
    return {
      id: `${s.id}_v${v}`,
      workflow_id: s.id,
      version: v,
      created_by: authors[v % authors.length],
      comment: comments[v % comments.length],
      created_at: iso((i * 4 + 1) * D),
    };
  });
}

export function demoIncidents(): Incident[] {
  return [
    {
      id: "inc_slack_429",
      workflow_id: "wf_slack_alert",
      run_id: "wf_slack_alert_run_0",
      status: "awaiting_approval",
      severity: "high",
      summary: "webhook-slack-alert failing: Slack node rejecting payloads (4 runs in a row).",
      root_cause:
        "The Slack node posts a `blocks` array that exceeds the 50-block limit when more than ~12 webhooks arrive in one window. Slack returns invalid_blocks and the node throws.",
      proposed_patch: {
        node: "Slack",
        change: "chunk blocks into batches of 45 and post sequentially",
        risk: "medium",
        diff: {
          "parameters.batching.enabled": true,
          "parameters.batching.batchSize": 45,
        },
      },
      created_at: iso(3 * H),
      resolved_at: null,
    },
    {
      id: "inc_health_timeout",
      workflow_id: "wf_health_check",
      run_id: "wf_health_check_run_1",
      status: "open",
      severity: "medium",
      summary: "hourly-health-check: one endpoint timing out intermittently.",
      root_cause:
        "status.partner-api.com exceeds the 5s HTTP timeout roughly 1 run in 6; the endpoint itself is the bottleneck, not the workflow.",
      proposed_patch: null,
      created_at: iso(9 * H),
      resolved_at: null,
    },
    {
      id: "inc_invoice_ocr",
      workflow_id: "wf_invoice",
      run_id: null,
      status: "resolved",
      severity: "low",
      summary: "invoice-ocr-to-sheet: OCR mis-parsed a rotated scan.",
      root_cause: "A single landscape PDF wasn't auto-rotated before OCR.",
      proposed_patch: null,
      created_at: iso(2 * D),
      resolved_at: iso(2 * D - 6 * H),
    },
  ];
}

export function demoCosts(days = 14): CostSummary {
  // A gently rising spend curve with believable per-day call counts.
  const daily = Array.from({ length: days }, (_, i) => {
    const date = new Date(NOW - (days - 1 - i) * D).toISOString().slice(0, 10);
    const base = 0.12 + i * 0.015;
    const wobble = ((i * 7) % 5) * 0.02;
    const cost = Number((base + wobble).toFixed(4));
    return { date, cost_usd: cost, calls: 40 + ((i * 13) % 60) };
  });
  const spend_today_usd = daily[daily.length - 1].cost_usd + 3.28;
  return {
    budget_usd: 8.0,
    spend_today_usd: Number(spend_today_usd.toFixed(2)),
    days,
    daily,
    by_service: [
      { service: "workflow-generator", cost_usd: 1.9123, calls: 214 },
      { service: "diagnostician", cost_usd: 0.8842, calls: 96 },
      { service: "workflow-validator", cost_usd: 0.4011, calls: 402 },
      { service: "run-monitor", cost_usd: 0.2187, calls: 611 },
    ],
  };
}
