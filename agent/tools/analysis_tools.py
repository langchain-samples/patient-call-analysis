"""
Analysis tools for topic extraction, adverse event detection,
and agent performance evaluation.

All tools return mock data for demo purposes, simulating the output
that would come from specialized ML models or LLM chains in production.
"""

import json

from langchain_core.tools import tool

from mock_data import (
    MOCK_SEGMENT_SENTIMENTS,
    MOCK_TOPICS,
    MOCK_ADVERSE_EVENTS,
    MOCK_TECHNICAL_COMPLAINTS,
)


@tool
def analyze_sentiment(transcript: str) -> str:
    """Analyze sentiment across a call transcript, scoring both patient and agent.

    Returns segment-level sentiment data with scores (0-1), speaker labels,
    and emotional tone descriptions. This raw data should be passed to
    run_sentiment_computation for statistical aggregation.

    Args:
        transcript: The full call transcript text.
    """
    return json.dumps(MOCK_SEGMENT_SENTIMENTS, indent=2)


@tool
def extract_topics(transcript: str) -> str:
    """Extract and categorize topics from a call transcript.

    Identifies topics across these categories:
    - SOP: Standard operating procedure touchpoints
    - safety_signal: Safety-related observations
    - adverse_event: Reported adverse events
    - enrollment: Patient enrollment and program topics

    Args:
        transcript: The full call transcript text.
    """
    return json.dumps(MOCK_TOPICS, indent=2)


@tool
def detect_adverse_events(transcript: str) -> str:
    """Detect adverse events in a call transcript with confidence scores.

    Returns each detected adverse event with:
    - Event description and severity
    - Confidence score (0-1)
    - Onset timing and frequency
    - Rationale explaining why this was flagged
    - Verbatim quote from the transcript

    Args:
        transcript: The full call transcript text.
    """
    return json.dumps(MOCK_ADVERSE_EVENTS, indent=2)


@tool
def detect_technical_complaints(transcript: str) -> str:
    """Detect technical complaints in a call transcript with confidence scores.

    Returns each detected technical complaint with:
    - Complaint description and category
    - Confidence score (0-1)
    - Rationale explaining why this was flagged
    - Verbatim quote from the transcript

    Args:
        transcript: The full call transcript text.
    """
    return json.dumps(MOCK_TECHNICAL_COMPLAINTS, indent=2)
