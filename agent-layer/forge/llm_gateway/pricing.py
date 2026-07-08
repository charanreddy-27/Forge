"""Per-model pricing used for cost logging.

Prices are USD per million tokens, taken from Anthropic's published pricing
(cached 2026-06). Unknown models are logged at zero cost with a warning so a
new model never silently breaks calls — but update this table when adding one.
"""

import logging
from dataclasses import dataclass
from decimal import Decimal

logger = logging.getLogger(__name__)

_MILLION = Decimal(1_000_000)


@dataclass(frozen=True)
class ModelPricing:
    input_usd_per_mtok: Decimal
    output_usd_per_mtok: Decimal


PRICING: dict[str, ModelPricing] = {
    "claude-opus-4-8": ModelPricing(Decimal("5.00"), Decimal("25.00")),
    "claude-opus-4-7": ModelPricing(Decimal("5.00"), Decimal("25.00")),
    "claude-opus-4-6": ModelPricing(Decimal("5.00"), Decimal("25.00")),
    "claude-sonnet-5": ModelPricing(Decimal("3.00"), Decimal("15.00")),
    "claude-sonnet-4-6": ModelPricing(Decimal("3.00"), Decimal("15.00")),
    "claude-haiku-4-5": ModelPricing(Decimal("1.00"), Decimal("5.00")),
}


def cost_usd(model: str, input_tokens: int, output_tokens: int) -> Decimal:
    """Compute the cost of a call. Local (ollama) models cost zero."""
    if model.startswith("ollama:"):
        return Decimal("0")
    pricing = PRICING.get(model)
    if pricing is None:
        logger.warning(
            "No pricing for model %r — logging cost as $0. Update pricing.py.", model
        )
        return Decimal("0")
    return (
        Decimal(input_tokens) * pricing.input_usd_per_mtok
        + Decimal(output_tokens) * pricing.output_usd_per_mtok
    ) / _MILLION
