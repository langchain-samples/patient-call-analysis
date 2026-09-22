"""Patient Call Analysis Orchestrator — Strands configuration."""

from strands import Agent

from .middleware import HallucinationLeakageGuard
from .model import (
    DEFAULT_ORCHESTRATOR_MODEL,
    DEFAULT_SPECIALIST_MODEL,
    create_gateway_model,
)
from .pii_review import create_final_review_tool
from .prompts import ORCHESTRATOR_PROMPT
from .subagents.agent_performance import create_agent_performance_subagent
from .subagents.sentiment import create_sentiment_subagent
from .subagents.topic_and_ae import create_topic_and_ae_subagent
from .telemetry import setup_telemetry
from .tools.transcript_tools import transcribe_call


def create_orchestrator(
    model: str = DEFAULT_ORCHESTRATOR_MODEL,
    *,
    system_prompt: str = ORCHESTRATOR_PROMPT,
    enable_guard: bool = True,
) -> Agent:
    """Create and return the Strands patient call analysis orchestrator."""
    setup_telemetry()

    sentiment = create_sentiment_subagent(
        create_gateway_model(DEFAULT_SPECIALIST_MODEL),
    )
    topic_and_ae = create_topic_and_ae_subagent(
        create_gateway_model(DEFAULT_SPECIALIST_MODEL),
    )
    agent_performance = create_agent_performance_subagent(
        create_gateway_model(DEFAULT_SPECIALIST_MODEL),
    )

    return Agent(
        name="call-analysis-orchestrator",
        model=create_gateway_model(model),
        system_prompt=system_prompt,
        tools=[
            transcribe_call,
            create_final_review_tool(),
            sentiment.as_tool(),
            topic_and_ae.as_tool(),
            agent_performance.as_tool(),
        ],
        hooks=[HallucinationLeakageGuard()] if enable_guard else [],
        callback_handler=None,
    )
