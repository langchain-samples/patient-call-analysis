"""
LangGraph Studio entry point.

Exposes the compiled patient call analysis agent graph for
visualization and execution in LangGraph Studio.
"""

import os
import sys

_AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _AGENT_DIR)

from dotenv import load_dotenv
load_dotenv(override=True)

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain_anthropic import ChatAnthropic
from langsmith.wrappers import wrap_anthropic

from subagents.sentiment import sentiment_subagent
from subagents.topic_and_ae import topic_and_ae_subagent
from subagents.agent_performance import agent_performance_subagent
from tools.transcript_tools import transcribe_call
from middleware import PIIDetectionMiddleware, HallucinationLeakageGuard
from prompts import ORCHESTRATOR_PROMPT

_llm = ChatAnthropic(model="claude-sonnet-4-5-20250929")
wrap_anthropic(_llm)

graph = create_deep_agent(
    name="call-analysis-orchestrator",
    model=_llm,
    system_prompt=ORCHESTRATOR_PROMPT,
    tools=[transcribe_call],
    subagents=[
        sentiment_subagent,
        topic_and_ae_subagent,
        agent_performance_subagent,
    ],
    backend=FilesystemBackend(root_dir=_AGENT_DIR, virtual_mode=True),
    skills=[os.path.join(_AGENT_DIR, "skills") + "/"],
    middleware=[PIIDetectionMiddleware(), HallucinationLeakageGuard()],
)
