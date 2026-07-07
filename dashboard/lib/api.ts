// Server-side data access for the Forge agent-layer API.
//
// Server components call these directly (FORGE_API_URL — the compose-internal
// hostname). Browser code never talks to the API directly; it goes through
// the /api/forge/[...path] proxy route, so no CORS and no build-time URLs.

const API_URL = process.env.FORGE_API_URL ?? "http://localhost:8000";

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

async function get<T>(path: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`GET ${path} → ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const fetchWorkflows = () => get<Workflow[]>("/workflows");
export const fetchWorkflow = (id: string) => get<Workflow>(`/workflows/${id}`);
export const fetchHealth = (id: string) => get<WorkflowHealth>(`/workflows/${id}/health`);
export const fetchRuns = (id: string) => get<Run[]>(`/workflows/${id}/runs`);
export const fetchVersions = (id: string) => get<WorkflowVersion[]>(`/workflows/${id}/versions`);
export const fetchIncidents = () => get<Incident[]>("/incidents");
export const fetchCosts = (days = 14) => get<CostSummary>(`/costs/summary?days=${days}`);

export const apiUrl = API_URL;
