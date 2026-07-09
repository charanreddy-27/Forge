// Server-side data access for the Forge agent-layer API.
//
// Server components call these directly. When FORGE_API_URL is set (e.g. the
// docker-compose deployment) they hit the live agent layer. When it isn't — the
// default on Vercel — the dashboard runs in demo mode and serves the seeded
// dataset in ./demo.ts, so the live link is fully explorable with no backend.
//
// Even in live mode, a fetch failure falls back to demo data rather than 500ing
// the page: a transient backend blip degrades to a realistic snapshot instead of
// a broken screen.
import {
  demoCosts,
  demoHealth,
  demoIncidents,
  demoRuns,
  demoVersions,
  demoWorkflow,
  demoWorkflows,
} from "./demo";

const API_URL = process.env.FORGE_API_URL;

/** True when there's no backend to talk to (or demo mode is forced). */
export const isDemo = !API_URL || process.env.FORGE_DEMO === "1";

export interface Workflow {
  id: string;
  name: string;
  description: string | null;
  engine_workflow_id: string | null;
  status: string;
  current_version: number;
  created_at: string;
  updated_at: string;
}

export interface WorkflowHealth {
  workflow_id: string;
  status: "healthy" | "degraded" | "failing" | "unknown";
  total_runs: number;
  success_rate: number | null;
  consecutive_failures: number;
  last_run_status: string | null;
  last_run_at: string | null;
}

export interface Run {
  id: string;
  workflow_id: string;
  engine_execution_id: string | null;
  status: string;
  started_at: string;
  finished_at: string | null;
  error_message: string | null;
}

export interface WorkflowVersion {
  id: string;
  workflow_id: string;
  version: number;
  created_by: string;
  comment: string | null;
  created_at: string;
}

export interface Incident {
  id: string;
  workflow_id: string;
  run_id: string | null;
  status: string;
  severity: string;
  summary: string;
  root_cause: string | null;
  proposed_patch: Record<string, unknown> | null;
  created_at: string;
  resolved_at: string | null;
}

export interface CostSummary {
  budget_usd: number;
  spend_today_usd: number;
  days: number;
  daily: { date: string; cost_usd: number; calls: number }[];
  by_service: { service: string; cost_usd: number; calls: number }[];
}

/**
 * Fetch `path` from the live API, falling back to `fallback()` when there's no
 * backend or the request fails. Keeps the dashboard resilient by design.
 */
async function get<T>(path: string, fallback: () => T): Promise<T> {
  if (isDemo) return fallback();
  try {
    const response = await fetch(`${API_URL}${path}`, { cache: "no-store" });
    if (!response.ok) throw new Error(`GET ${path} → ${response.status}`);
    return (await response.json()) as T;
  } catch {
    return fallback();
  }
}

export const fetchWorkflows = () => get<Workflow[]>("/workflows", demoWorkflows);
export const fetchWorkflow = (id: string) => get<Workflow>(`/workflows/${id}`, () => demoWorkflow(id));
export const fetchHealth = (id: string) =>
  get<WorkflowHealth>(`/workflows/${id}/health`, () => demoHealth(id));
export const fetchRuns = (id: string) => get<Run[]>(`/workflows/${id}/runs`, () => demoRuns(id));
export const fetchVersions = (id: string) =>
  get<WorkflowVersion[]>(`/workflows/${id}/versions`, () => demoVersions(id));
export const fetchIncidents = () => get<Incident[]>("/incidents", demoIncidents);
export const fetchCosts = (days = 14) =>
  get<CostSummary>(`/costs/summary?days=${days}`, () => demoCosts(days));

export const apiUrl = API_URL ?? "";
