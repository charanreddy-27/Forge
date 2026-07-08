"""Load test for the agent-layer API.

Read-heavy by default — the traffic shape the dashboard produces. Generation
submissions are opt-in (they enqueue real jobs and, with a worker running,
real LLM spend).

Run (against a running stack):

    pip install locust
    locust -f loadtest/locustfile.py --host http://localhost:8000 \
        --headless -u 20 -r 5 -t 30s

Opt into POST /generate load (queue-only; keep the worker stopped unless you
mean it):

    LOADTEST_SUBMIT=1 locust -f loadtest/locustfile.py ...
"""

import os
import random

from locust import HttpUser, between, task


class DashboardReader(HttpUser):
    """Simulates the dashboard: health checks, lists, costs, drill-downs."""

    wait_time = between(0.2, 1.0)
    workflow_ids: list[str] = []

    def on_start(self) -> None:
        response = self.client.get("/workflows")
        if response.ok:
            self.workflow_ids = [w["id"] for w in response.json()]

    @task(5)
    def health(self) -> None:
        self.client.get("/health")

    @task(4)
    def list_workflows(self) -> None:
        self.client.get("/workflows")

    @task(3)
    def cost_summary(self) -> None:
        self.client.get("/costs/summary?days=14")

    @task(2)
    def incidents(self) -> None:
        self.client.get("/incidents")

    @task(2)
    def workflow_drilldown(self) -> None:
        if not self.workflow_ids:
            return
        workflow_id = random.choice(self.workflow_ids)
        self.client.get(f"/workflows/{workflow_id}/runs", name="/workflows/[id]/runs")
        self.client.get(
            f"/workflows/{workflow_id}/health", name="/workflows/[id]/health"
        )


class GenerationSubmitter(HttpUser):
    """Opt-in write path: enqueues generation jobs (LOADTEST_SUBMIT=1)."""

    wait_time = between(2, 5)
    weight = 1 if os.environ.get("LOADTEST_SUBMIT") == "1" else 0

    @task
    def submit(self) -> None:
        self.client.post(
            "/generate",
            json={
                "instruction": "load test: fetch example.com daily and reshape the items",
                "deploy": False,
            },
        )
