"""Combined topic mining and adverse event detection subagent."""

from strands import Agent
from strands.models import Model

from ..tools.analysis_tools import (
    detect_adverse_events,
    detect_technical_complaints,
    extract_topics,
)

TOPIC_AND_AE_PROMPT = (
    "You are a pharmacovigilance and topic analysis specialist. "
    "Be efficient — three tool calls, then respond.\n\n"
    "STEP 1: Call extract_topics with the transcript.\n"
    "STEP 2: Call detect_adverse_events with the transcript.\n"
    "STEP 3: Call detect_technical_complaints with the transcript.\n"
    "STEP 4: Return a JSON summary with this exact structure:\n"
    "```json\n"
    "{\n"
    '  "topics": [\n'
    '    {"topic": "...", "category": "...", "summary": "..."}\n'
    "  ],\n"
    '  "adverse_events": [\n'
    '    {"event": "...", "severity": "...", "confidence": <float>, "verbatim": "..."}\n'
    "  ],\n"
    '  "technical_complaints": [\n'
    '    {"complaint": "...", "confidence": <float>, "category": "..."}\n'
    "  ],\n"
    '  "risk_summary": "<brief 1-sentence risk assessment>"\n'
    "}\n"
    "```\n\n"
    "Do NOT make extra tool calls. Three calls total, then respond with ONLY the JSON. No prose."
)


def create_topic_and_ae_subagent(model: Model) -> Agent:
    """Create the topic and adverse-event specialist."""
    return Agent(
        name="topic_and_ae_detection",
        description=(
            "Extract topics and detect adverse events and technical complaints from a "
            "patient call transcript. Returns a structured JSON summary."
        ),
        system_prompt=TOPIC_AND_AE_PROMPT,
        model=model,
        tools=[extract_topics, detect_adverse_events, detect_technical_complaints],
        callback_handler=None,
    )
