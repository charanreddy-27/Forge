"""The LLM Gateway itself.

Call flow for :meth:`LLMGateway.complete`:

1. Budget check — hard stop if today's logged spend >= the daily budget.
2. Anthropic call with exponential-backoff retries on transient errors.
3. If Anthropic is still failing and Ollama fallback is enabled, try Ollama.
4. Log the call (success or failure) to the llm_calls table.
"""

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal

import anthropic
import httpx
from sqlalchemy.orm import sessionmaker

from forge.config import Settings
from forge.db.models import LLMCall
from forge.llm_gateway.budget import budget_exhausted
from forge.llm_gateway.errors import BudgetExceededError, LLMUnavailableError
from forge.llm_gateway.pricing import cost_usd

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LLMResponse:
    """What callers get back — enough to use the text and account for the call."""

    text: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: Decimal
    latency_ms: int


class LLMGateway:
    """Single entry point for all LLM calls.

    The gateway is stateless: budget state lives in Postgres (the llm_calls
    table), so any number of instances enforce the same limit.
    """

    def __init__(
        self,
        session_factory: sessionmaker,
        settings: Settings,
        anthropic_client: anthropic.Anthropic | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._session_factory = session_factory
        self._settings = settings
        # max_retries=0: the SDK's built-in retry would stack multiplicatively
        # with our own backoff loop, so we disable it and own the policy here.
        self._client = anthropic_client or anthropic.Anthropic(
            api_key=settings.anthropic_api_key, max_retries=0
        )
        self._sleep = sleep

    def complete(
        self,
        *,
        prompt: str,
        service: str,
        purpose: str,
        system: str | None = None,
        model: str | None = None,
        max_tokens: int = 16000,
    ) -> LLMResponse:
        """Run a completion and log it.

        Args:
            prompt: The user-turn content.
            service: Calling agent service (e.g. "workflow-generator").
            purpose: Short human-readable purpose for the cost dashboard.
            system: Optional system prompt.
            model: Override the configured default model.
            max_tokens: Output token cap.

        Raises:
            BudgetExceededError: today's spend already hit the daily budget.
            LLMUnavailableError: Anthropic failed after retries and no
                fallback was available or the fallback failed too.
        """
        model = model or self._settings.anthropic_model

        with self._session_factory() as session:
            if budget_exhausted(session, self._settings.llm_daily_budget_usd):
                self._log_call(
                    provider="anthropic",
                    model=model,
                    service=service,
                    purpose=purpose,
                    success=False,
                    error="daily budget exceeded",
                )
                raise BudgetExceededError(
                    f"Daily LLM budget of ${self._settings.llm_daily_budget_usd} reached; "
                    "call refused."
                )

        try:
            response = self._call_anthropic(
                prompt=prompt, system=system, model=model, max_tokens=max_tokens
            )
        except LLMUnavailableError as anthropic_error:
            if not self._settings.ollama_enabled:
                self._log_call(
                    provider="anthropic",
                    model=model,
                    service=service,
                    purpose=purpose,
                    success=False,
                    error=str(anthropic_error),
                )
                raise
            logger.warning("Anthropic unavailable, falling back to Ollama: %s", anthropic_error)
            try:
                response = self._call_ollama(prompt=prompt, system=system)
            except LLMUnavailableError as ollama_error:
                self._log_call(
                    provider="ollama",
                    model=f"ollama:{self._settings.ollama_model}",
                    service=service,
                    purpose=purpose,
                    success=False,
                    error=str(ollama_error),
                )
                raise

        self._log_call(
            provider=response.provider,
            model=response.model,
            service=service,
            purpose=purpose,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            cost=response.cost_usd,
            latency_ms=response.latency_ms,
            success=True,
        )
        return response

    def _call_anthropic(
        self, *, prompt: str, system: str | None, model: str, max_tokens: int
    ) -> LLMResponse:
        last_error: Exception | None = None
        for attempt in range(self._settings.llm_max_retries + 1):
            if attempt > 0:
                # 2s, 4s, 8s, ... — cheap insurance against rate limits and blips.
                self._sleep(self._settings.llm_retry_base_delay_seconds * 2 ** (attempt - 1))
            started = time.monotonic()
            try:
                if system is not None:
                    message = self._client.messages.create(
                        model=model,
                        max_tokens=max_tokens,
                        system=system,
                        messages=[{"role": "user", "content": prompt}],
                    )
                else:
                    message = self._client.messages.create(
                        model=model,
                        max_tokens=max_tokens,
                        messages=[{"role": "user", "content": prompt}],
                    )
            except (anthropic.RateLimitError, anthropic.APIConnectionError) as exc:
                last_error = exc
                continue
            except anthropic.APIStatusError as exc:
                if exc.status_code >= 500:
                    last_error = exc
                    continue
                # 4xx (except 429) means the request itself is wrong — retrying
                # would just burn budget.
                raise LLMUnavailableError(f"Anthropic rejected the request: {exc}") from exc

            latency_ms = int((time.monotonic() - started) * 1000)
            text = "".join(block.text for block in message.content if block.type == "text")
            return LLMResponse(
                text=text,
                provider="anthropic",
                model=model,
                input_tokens=message.usage.input_tokens,
                output_tokens=message.usage.output_tokens,
                cost_usd=cost_usd(model, message.usage.input_tokens, message.usage.output_tokens),
                latency_ms=latency_ms,
            )

        raise LLMUnavailableError(
            f"Anthropic call failed after {self._settings.llm_max_retries + 1} attempts: "
            f"{last_error}"
        ) from last_error

    def _call_ollama(self, *, prompt: str, system: str | None) -> LLMResponse:
        model = self._settings.ollama_model
        started = time.monotonic()
        try:
            resp = httpx.post(
                f"{self._settings.ollama_base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    **({"system": system} if system else {}),
                    "stream": False,
                },
                timeout=120,
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise LLMUnavailableError(f"Ollama fallback failed: {exc}") from exc

        data = resp.json()
        latency_ms = int((time.monotonic() - started) * 1000)
        return LLMResponse(
            text=data.get("response", ""),
            provider="ollama",
            model=f"ollama:{model}",
            input_tokens=data.get("prompt_eval_count", 0),
            output_tokens=data.get("eval_count", 0),
            cost_usd=Decimal("0"),
            latency_ms=latency_ms,
        )

    def _log_call(
        self,
        *,
        provider: str,
        model: str,
        service: str,
        purpose: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost: Decimal = Decimal("0"),
        latency_ms: int = 0,
        success: bool,
        error: str | None = None,
    ) -> None:
        with self._session_factory() as session:
            session.add(
                LLMCall(
                    provider=provider,
                    model=model,
                    service=service,
                    purpose=purpose,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cost_usd=cost,
                    latency_ms=latency_ms,
                    success=success,
                    error=error,
                )
            )
            session.commit()
