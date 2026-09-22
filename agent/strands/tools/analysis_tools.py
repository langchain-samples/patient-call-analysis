"""Deterministic mock analysis tools for the Strands implementation."""

import json

from strands import tool

from ..mock_data import (
    MOCK_ADVERSE_EVENTS,
    MOCK_SEGMENT_SENTIMENTS,
    MOCK_TECHNICAL_COMPLAINTS,
    MOCK_TOPICS,
)


@tool
def analyze_sentiment(transcript: str) -> str:
    """Analyze sentiment across a call transcript for both speakers."""
    return json.dumps(MOCK_SEGMENT_SENTIMENTS, indent=2)


@tool
def extract_topics(transcript: str) -> str:
    """Extract and categorize topics from a call transcript."""
    return json.dumps(MOCK_TOPICS, indent=2)


@tool
def detect_adverse_events(transcript: str) -> str:
    """Detect adverse events in a call transcript with confidence scores."""
    return json.dumps(MOCK_ADVERSE_EVENTS, indent=2)


@tool
def detect_technical_complaints(transcript: str) -> str:
    """Detect technical complaints in a call transcript with confidence scores."""
    return json.dumps(MOCK_TECHNICAL_COMPLAINTS, indent=2)
