"""
Patient Call Analysis Orchestrator — Deep Agent Configuration

Creates and returns the call analysis orchestrator agent with all
subagents, tools, skills, middleware, and memory wiring.
"""

import os

from deepagents import create_deep_agent
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore

from subagents.sentiment import sentiment_subagent
from subagents.topic_and_ae import topic_and_ae_subagent
from subagents.agent_performance import agent_performance_subagent
from tools.transcript_tools import transcribe_call
from middleware import (
    PIIDetectionMiddleware,
    HallucinationLeakageGuard,
    ForbiddenToolGuard,
)
from prompts import ORCHESTRATOR_PROMPT

_AGENT_DIR = os.path.dirname(os.path.abspath(__file__))


def create_orchestrator(store: InMemoryStore | None = None, model: str = "claude-sonnet-4-5-20250929"):
    """Create and return the patient call analysis orchestrator agent.

    Args:
        store: Optional InMemoryStore instance. If not provided, a new one
               is created.
        model: Model identifier for the orchestrator LLM.

    Returns:
        Tuple of (agent, store) — the compiled agent and its backing store.
    """
    if store is None:
        store = InMemoryStore()

    agent = create_deep_agent(
        name="call-analysis-orchestrator",
        model=model,
        system_prompt=ORCHESTRATOR_PROMPT,
        tools=[transcribe_call],
        subagents=[
            sentiment_subagent,
            topic_and_ae_subagent,
            agent_performance_subagent,
        ],
        # Drop deepagents built-in fs tools — the orchestrator must not write
        # files, and exposing them inflates prompt tokens and pollutes the
        # trajectory. ForbiddenToolGuard is a belt-and-suspenders defense in
        # case a future refactor re-introduces them.
        backend=None,
        skills=[os.path.join(_AGENT_DIR, "skills") + "/"],
        store=store,
        checkpointer=MemorySaver(),
        middleware=[
            PIIDetectionMiddleware(),
            HallucinationLeakageGuard(),
            ForbiddenToolGuard(),
        ],
    )

    return agent, store
