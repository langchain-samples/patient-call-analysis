"""
Combined topic mining and adverse event detection subagent.

Merges topic extraction and AE/TC detection into a single subagent.
Returns a structured JSON summary.
"""

from tools.analysis_tools import (
    extract_topics,
    detect_adverse_events,
    detect_technical_complaints,
)

topic_and_ae_subagent = {
    "name": "topic_and_ae_detection",
    "description": (
        "Extract topics and detect adverse events and technical complaints from a "
        "patient call transcript. Returns a structured JSON summary."
    ),
    "system_prompt": (
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
    ),
    "model": "claude-haiku-4-5-20251001",
    "tools": [extract_topics, detect_adverse_events, detect_technical_complaints],
}
