"""Golden-file tests: known instruction → expected workflow structure.

Each file in tests/golden/ holds an instruction, the canned model output
(optionally fenced / with prose, as real models drift), and the expected
structure. Add a file to add a case.
"""

import json
from pathlib import Path

import pytest

from forge.generator import WorkflowGenerator
from tests.fake_gateway import FakeGateway

GOLDEN_DIR = Path(__file__).parent / "golden"
GOLDEN_CASES = sorted(GOLDEN_DIR.glob("*.json"))


def render_llm_text(case: dict) -> str:
    """Build the raw model output the golden case describes."""
    body = json.dumps(case["llm_workflow"], indent=2)
    if case.get("fenced"):
        body = f"```json\n{body}\n```"
    prefix = case.get("prose_prefix")
    return f"{prefix}\n{body}" if prefix else body


@pytest.mark.parametrize("path", GOLDEN_CASES, ids=[p.stem for p in GOLDEN_CASES])
def test_golden_case(path: Path):
    case = json.loads(path.read_text())
    expect = case["expect"]

    gateway = FakeGateway([render_llm_text(case)])
    generator = WorkflowGenerator(gateway)  # type: ignore[arg-type]

    result = generator.generate(case["instruction"])

    assert result.validation.valid == expect["valid"], result.validation.errors
    assert result.validation.destructive == expect["destructive"]
    assert result.validation.destructive_nodes == expect["destructive_nodes"]

    if expect["valid"]:
        assert result.ok
        assert result.attempts == 1
        node_types = [node["type"] for node in result.definition["nodes"]]
        assert node_types == expect["node_types"]
        # The gateway was called with the generator's identity for cost logging.
        assert gateway.calls[0]["service"] == "workflow-generator"
    else:
        assert not result.ok
        # Invalid output triggers exactly one repair round before giving up.
        assert result.attempts == 2
        assert any(
            expect["error_contains"] in error for error in result.validation.errors
        )


def test_there_are_at_least_five_golden_cases():
    assert len(GOLDEN_CASES) >= 5


def test_repair_round_recovers_from_bad_first_attempt():
    good = json.loads((GOLDEN_DIR / "daily_api_transform.json").read_text())
    good_text = json.dumps(good["llm_workflow"])

    gateway = FakeGateway(["this is not json at all", good_text])
    generator = WorkflowGenerator(gateway)  # type: ignore[arg-type]

    result = generator.generate("pull items daily")

    assert result.ok
    assert result.attempts == 2
    # The repair prompt must tell the model what was wrong.
    assert "rejected by the validator" in gateway.calls[1]["prompt"]
