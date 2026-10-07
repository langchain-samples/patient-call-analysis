"""LangSmith LLM Gateway model configuration for Strands."""

import os
from typing import Any

from strands.models.anthropic import AnthropicModel

DEFAULT_GATEWAY_URL = "https://gateway.smith.langchain.com/anthropic"
DEFAULT_ORCHESTRATOR_MODEL = "claude-sonnet-4-5-20250929"
DEFAULT_SPECIALIST_MODEL = "claude-haiku-4-5-20251001"
DEFAULT_MAX_TOKENS = 64000
DEFAULT_THINKING_BUDGET = 4000


def create_gateway_model(
    model_id: str,
    *,
    temperature: float | None = None,
    enable_thinking: bool = False,
    thinking_budget: int = DEFAULT_THINKING_BUDGET,
) -> AnthropicModel:
    """Create a Strands Anthropic model routed through LangSmith Gateway."""
    api_key = os.environ.get("LANGSMITH_API_KEY")
    if not api_key:
        raise ValueError("LANGSMITH_API_KEY environment variable is required.")

    params: dict[str, Any] = {}
    if temperature is not None:
        params["temperature"] = temperature

    if enable_thinking:
        # Extended thinking requires max_tokens > budget and no custom temperature.
        # Keep the budget bounded so it can never exceed the response budget.
        budget = max(1024, min(thinking_budget, DEFAULT_MAX_TOKENS - 1024))
        params.pop("temperature", None)
        params["thinking"] = {"type": "enabled", "budget_tokens": budget}

    return AnthropicModel(
        model_id=model_id,
        max_tokens=DEFAULT_MAX_TOKENS,
        params=params or None,
        client_args={
            "api_key": api_key,
            "base_url": os.environ.get("LANGSMITH_GATEWAY_URL", DEFAULT_GATEWAY_URL),
        },
    )
