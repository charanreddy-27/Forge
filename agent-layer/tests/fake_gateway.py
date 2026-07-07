"""Fake LLM gateway for generator/worker tests (mocks live only in tests)."""

from decimal import Decimal

from forge.llm_gateway import LLMResponse


class FakeGateway:
    """Returns scripted responses; repeats the last one if attempts exceed it."""

    def __init__(self, responses: list[str]) -> None:
        self._responses = responses
        self.calls: list[dict] = []

    def complete(self, **kwargs) -> LLMResponse:
        self.calls.append(kwargs)
        index = min(len(self.calls) - 1, len(self._responses) - 1)
        return LLMResponse(
            text=self._responses[index],
            provider="anthropic",
            model="claude-opus-4-8",
            input_tokens=100,
            output_tokens=200,
            cost_usd=Decimal("0.01"),
            latency_ms=5,
        )
