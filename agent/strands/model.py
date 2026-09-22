"""LangSmith LLM Gateway model configuration for Strands."""

import os

from strands.models.anthropic import AnthropicModel

DEFAULT_GATEWAY_URL = "https://gateway.smith.langchain.com/anthropic"
DEFAULT_ORCHESTRATOR_MODEL = "claude-sonnet-4-5-20250929"
DEFAULT_SPECIALIST_MODEL = "claude-haiku-4-5-20251001"
DEFAULT_MAX_TOKENS = 64000


def create_gateway_model(
    model_id: str,
    *,
    temperature: float | None = None,
) -> AnthropicModel:
    """Create a Strands Anthropic model routed through LangSmith Gateway."""
    api_key = os.environ.get("LANGSMITH_API_KEY")
    if not api_key:
        raise ValueError("LANGSMITH_API_KEY environment variable is required.")

    params = {"temperature": temperature} if temperature is not None else None
    return AnthropicModel(
        model_id=model_id,
        max_tokens=DEFAULT_MAX_TOKENS,
        params=params,
        client_args={
            "api_key": api_key,
            "base_url": os.environ.get("LANGSMITH_GATEWAY_URL", DEFAULT_GATEWAY_URL),
        },
    )
