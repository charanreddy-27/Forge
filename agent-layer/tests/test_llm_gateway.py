"""Unit tests for the LLM Gateway: cost logging, retries, budget, fallback."""

from dataclasses import dataclass, field
from decimal import Decimal

import anthropic
import httpx
import pytest
from sqlalchemy import select

from forge.db.models import LLMCall
from forge.llm_gateway import BudgetExceededError, LLMGateway, LLMUnavailableError
from forge.llm_gateway.pricing import cost_usd

# ── Fakes ────────────────────────────────────────────────────────────────────


@dataclass
class FakeUsage:
    input_tokens: int
    output_tokens: int


@dataclass
class FakeTextBlock:
    text: str
    type: str = "text"


@dataclass
class FakeMessage:
    content: list[FakeTextBlock]
    usage: FakeUsage


class FakeMessages:
    """Stands in for anthropic_client.messages; pops scripted results in order."""

    def __init__(self, script: list) -> None:
        self.script = script
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        result = self.script.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


@dataclass
class FakeAnthropicClient:
    messages: FakeMessages = field(default_factory=lambda: FakeMessages([]))


def _rate_limit_error() -> anthropic.RateLimitError:
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    response = httpx.Response(429, request=request)
    return anthropic.RateLimitError("rate limited", response=response, body=None)


def _bad_request_error() -> anthropic.BadRequestError:
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    response = httpx.Response(400, request=request)
    return anthropic.BadRequestError("bad request", response=response, body=None)


def _ok_message(text: str = "hello", input_tokens: int = 1000, output_tokens: int = 500):
    return FakeMessage(
        content=[FakeTextBlock(text=text)],
        usage=FakeUsage(input_tokens=input_tokens, output_tokens=output_tokens),
    )


def make_gateway(session_factory, settings, script: list, sleeps: list | None = None):
    client = FakeAnthropicClient(messages=FakeMessages(script))
    gateway = LLMGateway(
        session_factory=session_factory,
        settings=settings,
        anthropic_client=client,  # type: ignore[arg-type]
        sleep=(sleeps.append if sleeps is not None else lambda _: None),
    )
    return gateway, client


# ── Tests ────────────────────────────────────────────────────────────────────


class TestCompleteAndLog:
    def test_returns_text_and_computes_cost(self, session_factory, settings):
        gateway, _ = make_gateway(session_factory, settings, [_ok_message()])

        response = gateway.complete(prompt="hi", service="test-svc", purpose="unit test")

        assert response.text == "hello"
        assert response.provider == "anthropic"
        # opus 4.8: $5/MTok in, $25/MTok out → 1000 in + 500 out = $0.0175
        assert response.cost_usd == Decimal("0.017500")

    def test_logs_call_to_database(self, session_factory, settings):
        gateway, _ = make_gateway(session_factory, settings, [_ok_message()])

        gateway.complete(prompt="hi", service="test-svc", purpose="unit test")

        with session_factory() as session:
            call = session.execute(select(LLMCall)).scalar_one()
        assert call.provider == "anthropic"
        assert call.model == "claude-opus-4-8"
        assert call.service == "test-svc"
        assert call.purpose == "unit test"
        assert call.input_tokens == 1000
        assert call.output_tokens == 500
        assert call.cost_usd == Decimal("0.017500")
        assert call.success is True

    def test_system_prompt_and_model_override_are_passed_through(self, session_factory, settings):
        gateway, client = make_gateway(session_factory, settings, [_ok_message()])

        gateway.complete(
            prompt="hi",
            service="s",
            purpose="p",
            system="be terse",
            model="claude-haiku-4-5",
            max_tokens=256,
        )

        sent = client.messages.calls[0]
        assert sent["model"] == "claude-haiku-4-5"
        assert sent["system"] == "be terse"
        assert sent["max_tokens"] == 256


class TestRetries:
    def test_retries_transient_errors_with_backoff(self, session_factory, settings):
        sleeps: list[float] = []
        gateway, client = make_gateway(
            session_factory,
            settings,
            [_rate_limit_error(), _rate_limit_error(), _ok_message()],
            sleeps=sleeps,
        )

        response = gateway.complete(prompt="hi", service="s", purpose="p")

        assert response.text == "hello"
        assert len(client.messages.calls) == 3
        # base delay 0.01 doubles each retry: 0.01, 0.02
        assert sleeps == [0.01, 0.02]

    def test_gives_up_after_max_retries_and_logs_failure(self, session_factory, settings):
        # settings.llm_max_retries = 2 → 3 attempts total
        gateway, _ = make_gateway(
            session_factory,
            settings,
            [_rate_limit_error(), _rate_limit_error(), _rate_limit_error()],
        )

        with pytest.raises(LLMUnavailableError):
            gateway.complete(prompt="hi", service="s", purpose="p")

        with session_factory() as session:
            call = session.execute(select(LLMCall)).scalar_one()
        assert call.success is False
        assert call.cost_usd == Decimal("0")

    def test_does_not_retry_client_errors(self, session_factory, settings):
        gateway, client = make_gateway(session_factory, settings, [_bad_request_error()])

        with pytest.raises(LLMUnavailableError):
            gateway.complete(prompt="hi", service="s", purpose="p")

        assert len(client.messages.calls) == 1


class TestBudget:
    def test_hard_stop_when_budget_reached(self, session_factory, settings):
        with session_factory() as session:
            session.add(
                LLMCall(
                    provider="anthropic",
                    model="claude-opus-4-8",
                    service="s",
                    purpose="prior spend",
                    cost_usd=settings.llm_daily_budget_usd,  # exactly at the limit
                )
            )
            session.commit()

        gateway, client = make_gateway(session_factory, settings, [_ok_message()])

        with pytest.raises(BudgetExceededError):
            gateway.complete(prompt="hi", service="s", purpose="p")

        # The refused attempt never reached Anthropic and was itself logged.
        assert client.messages.calls == []
        with session_factory() as session:
            calls = session.execute(select(LLMCall)).scalars().all()
        blocked = [c for c in calls if c.error == "daily budget exceeded"]
        assert len(blocked) == 1
        assert blocked[0].success is False

    def test_allows_calls_under_budget(self, session_factory, settings):
        with session_factory() as session:
            session.add(
                LLMCall(
                    provider="anthropic",
                    model="claude-opus-4-8",
                    service="s",
                    purpose="prior spend",
                    cost_usd=settings.llm_daily_budget_usd - Decimal("0.01"),
                )
            )
            session.commit()

        gateway, _ = make_gateway(session_factory, settings, [_ok_message()])
        response = gateway.complete(prompt="hi", service="s", purpose="p")
        assert response.text == "hello"


class TestOllamaFallback:
    def test_falls_back_to_ollama_when_anthropic_unavailable(
        self, session_factory, settings, monkeypatch
    ):
        settings = settings.model_copy(update={"ollama_enabled": True})
        gateway, _ = make_gateway(
            session_factory,
            settings,
            [_rate_limit_error(), _rate_limit_error(), _rate_limit_error()],
        )

        def fake_post(url, **kwargs):
            assert url.endswith("/api/generate")
            request = httpx.Request("POST", url)
            return httpx.Response(
                200,
                request=request,
                json={"response": "local answer", "prompt_eval_count": 10, "eval_count": 20},
            )

        monkeypatch.setattr(httpx, "post", fake_post)

        response = gateway.complete(prompt="hi", service="s", purpose="p")

        assert response.provider == "ollama"
        assert response.text == "local answer"
        assert response.cost_usd == Decimal("0")

        with session_factory() as session:
            call = session.execute(select(LLMCall)).scalar_one()
        assert call.provider == "ollama"
        assert call.success is True

    def test_raises_when_fallback_also_fails(self, session_factory, settings, monkeypatch):
        settings = settings.model_copy(update={"ollama_enabled": True})
        gateway, _ = make_gateway(
            session_factory,
            settings,
            [_rate_limit_error(), _rate_limit_error(), _rate_limit_error()],
        )

        def fake_post(url, **kwargs):
            raise httpx.ConnectError("connection refused")

        monkeypatch.setattr(httpx, "post", fake_post)

        with pytest.raises(LLMUnavailableError, match="Ollama fallback failed"):
            gateway.complete(prompt="hi", service="s", purpose="p")


class TestPricing:
    def test_known_models(self):
        assert cost_usd("claude-opus-4-8", 1_000_000, 0) == Decimal("5.00")
        assert cost_usd("claude-opus-4-8", 0, 1_000_000) == Decimal("25.00")
        assert cost_usd("claude-sonnet-5", 1_000_000, 1_000_000) == Decimal("18.00")
        assert cost_usd("claude-haiku-4-5", 2_000_000, 0) == Decimal("2.00")

    def test_unknown_model_costs_zero(self):
        assert cost_usd("some-future-model", 1_000_000, 1_000_000) == Decimal("0")

    def test_ollama_models_cost_zero(self):
        assert cost_usd("ollama:llama3.1", 1_000_000, 1_000_000) == Decimal("0")
