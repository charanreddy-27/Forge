"""Tests for the job queue, the worker loop, and the generation handler."""

import json

import pytest

from forge.generator import WorkflowGenerator
from forge.jobs.handlers import GenerationJobHandler
from forge.jobs.queue import JobQueue
from forge.jobs.worker import run_worker
from forge.registry import WorkflowRegistry
from tests.fake_engine import FakeEngineAdapter
from tests.fake_gateway import FakeGateway
from tests.fake_redis import FakeRedis

SAFE_WORKFLOW = {
    "name": "daily-transform",
    "nodes": [
        {
            "name": "Every Day",
            "type": "n8n-nodes-base.scheduleTrigger",
            "parameters": {"rule": {"interval": [{"field": "days"}]}},
        },
        {
            "name": "Fetch",
            "type": "n8n-nodes-base.httpRequest",
            "parameters": {"url": "https://api.example.com", "method": "GET"},
        },
    ],
    "connections": {"Every Day": {"main": [[{"node": "Fetch", "type": "main", "index": 0}]]}},
    "settings": {},
}

DESTRUCTIVE_WORKFLOW = {
    **SAFE_WORKFLOW,
    "name": "daily-email",
    "nodes": SAFE_WORKFLOW["nodes"]
    + [{"name": "Mail", "type": "n8n-nodes-base.emailSend", "parameters": {}}],
}


@pytest.fixture()
def queue() -> JobQueue:
    return JobQueue(FakeRedis())


def make_handler(session_factory, llm_text: str) -> tuple[GenerationJobHandler, FakeEngineAdapter]:
    engine = FakeEngineAdapter()
    handler = GenerationJobHandler(
        generator=WorkflowGenerator(FakeGateway([llm_text])),  # type: ignore[arg-type]
        registry=WorkflowRegistry(session_factory, engine),
    )
    return handler, engine


class TestQueue:
    def test_enqueue_claim_finish_roundtrip(self, queue):
        job_id = queue.enqueue({"instruction": "do things"})
        assert queue.get(job_id)["status"] == "queued"

        claimed = queue.claim(timeout=1)
        assert claimed is not None
        claimed_id, payload = claimed
        assert claimed_id == job_id
        assert payload == {"instruction": "do things"}
        assert queue.get(job_id)["status"] == "running"

        queue.finish(job_id, "succeeded", {"answer": 42})
        record = queue.get(job_id)
        assert record["status"] == "succeeded"
        assert record["result"] == {"answer": 42}

    def test_claim_on_empty_queue_returns_none(self, queue):
        assert queue.claim(timeout=1) is None

    def test_fifo_order(self, queue):
        first = queue.enqueue({"n": 1})
        second = queue.enqueue({"n": 2})
        assert queue.claim(timeout=1)[0] == first
        assert queue.claim(timeout=1)[0] == second

    def test_unknown_job_is_none(self, queue):
        assert queue.get("nope") is None


class TestWorker:
    def test_worker_runs_handler_and_stores_result(self, queue):
        job_id = queue.enqueue({"x": 1})
        run_worker(queue, lambda payload: ("succeeded", {"echo": payload}), run_forever=False)

        record = queue.get(job_id)
        assert record["status"] == "succeeded"
        assert record["result"] == {"echo": {"x": 1}}
        assert record["finished_at"]

    def test_worker_records_handler_crash_as_failed(self, queue):
        job_id = queue.enqueue({})

        def explode(payload):
            raise ValueError("kaboom")

        run_worker(queue, explode, run_forever=False)
        record = queue.get(job_id)
        assert record["status"] == "failed"
        assert "kaboom" in record["error"]


class TestGenerationHandler:
    def test_safe_workflow_with_deploy_lands_in_registry(self, session_factory, queue):
        handler, engine = make_handler(session_factory, json.dumps(SAFE_WORKFLOW))
        job_id = queue.enqueue(
            {"instruction": "transform items daily", "deploy": True, "actor": "human"}
        )
        run_worker(queue, handler, run_forever=False)

        record = queue.get(job_id)
        assert record["status"] == "succeeded"
        assert record["result"]["workflow_id"]
        assert record["result"]["workflow_version"] == 1
        assert len(engine.workflows) == 1  # deployed to the engine

    def test_safe_workflow_without_deploy_only_stores_definition(self, session_factory, queue):
        handler, engine = make_handler(session_factory, json.dumps(SAFE_WORKFLOW))
        job_id = queue.enqueue({"instruction": "transform items daily", "deploy": False})
        run_worker(queue, handler, run_forever=False)

        record = queue.get(job_id)
        assert record["status"] == "succeeded"
        assert "workflow_id" not in record["result"]
        assert record["result"]["definition"]["name"] == "daily-transform"
        assert engine.workflows == {}

    def test_destructive_without_approval_is_gated(self, session_factory, queue):
        handler, engine = make_handler(session_factory, json.dumps(DESTRUCTIVE_WORKFLOW))
        job_id = queue.enqueue(
            {"instruction": "email me daily", "deploy": True, "allow_destructive": False}
        )
        run_worker(queue, handler, run_forever=False)

        record = queue.get(job_id)
        assert record["status"] == "requires_approval"
        assert "Mail" in record["result"]["reason"]
        assert engine.workflows == {}  # NOT deployed

    def test_destructive_with_approval_deploys(self, session_factory, queue):
        handler, engine = make_handler(session_factory, json.dumps(DESTRUCTIVE_WORKFLOW))
        job_id = queue.enqueue(
            {"instruction": "email me daily", "deploy": True, "allow_destructive": True}
        )
        run_worker(queue, handler, run_forever=False)

        assert queue.get(job_id)["status"] == "succeeded"
        assert len(engine.workflows) == 1

    def test_invalid_generation_fails_with_errors_recorded(self, session_factory, queue):
        handler, engine = make_handler(session_factory, "not json, sorry")
        job_id = queue.enqueue({"instruction": "do something", "deploy": True})
        run_worker(queue, handler, run_forever=False)

        record = queue.get(job_id)
        assert record["status"] == "failed"
        assert record["result"]["validation"]["errors"]
        assert engine.workflows == {}
