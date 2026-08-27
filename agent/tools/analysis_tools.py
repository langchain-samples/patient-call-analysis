"""
Analysis tools for topic extraction, adverse event detection,
and agent performance evaluation.

All tools return mock data for demo purposes, simulating the output
that would come from specialized ML models or LLM chains in production.
"""

import json

from langchain_core.tools import tool
from mock_data import (
    MOCK_ADVERSE_EVENTS,
    MOCK_SEGMENT_SENTIMENTS,
    MOCK_TECHNICAL_COMPLAINTS,
    MOCK_TOPICS,
)

MANDATED_REPORT_HEADINGS = [
    "### 1. Call Summary",
    "### 2. Sentiment Analysis",
    "### 3. Topic Analysis",
    "### 4. Adverse Events & Technical Complaints",
    "### 5. Agent Performance Review",
    "### 6. Overall Assessment & Recommendations",
]


def validate_report_structure(report: str) -> tuple[list[str], int]:
    """Return missing mandated headings and the report word count."""
    missing_headings = [heading for heading in MANDATED_REPORT_HEADINGS if heading not in report]
    word_count = len(report.split())
    return missing_headings, word_count


@tool
def final_review(report: str) -> dict:
    """Validate mandated report headings and the 800-word limit."""
    missing_sections, word_count = validate_report_structure(report)
    if missing_sections or word_count > 800:
        return {
            "label": "fail",
            "missing_sections": missing_sections,
            "word_count": word_count,
        }
    return {"label": "pass"}


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
