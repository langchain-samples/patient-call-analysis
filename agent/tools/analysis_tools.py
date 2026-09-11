"""
Analysis tools for topic extraction, adverse event detection,
and agent performance evaluation.

All tools return mock data for demo purposes, simulating the output
that would come from specialized ML models or LLM chains in production.
"""

import json
import re

from langchain_core.tools import tool
from middleware import PII_PATTERNS
from mock_data import (
    INTERNAL_ONLY_TERMS,
    MOCK_ADVERSE_EVENTS,
    MOCK_SEGMENT_SENTIMENTS,
    MOCK_TECHNICAL_COMPLAINTS,
    MOCK_TOPICS,
)
from prompts import REQUIRED_REPORT_HEADINGS

REFERENCE_TOKEN_PATTERN = re.compile(
    r"\b(?:SF|SFDC|CRM|CASE|TICKET)-[A-Za-z0-9-]{4,}\b"
)
PATIENT_NAME_PATTERN = re.compile(
    r"\b(?:my name is|patient(?:'s)? name is)\s+([A-Z][A-Za-z'-]+(?:\s+[A-Z][A-Za-z'-]+)+)",
    re.IGNORECASE,
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


@tool
def final_review(report: str, allowed_inputs: list[str]) -> str:
    """Review a draft report against privacy, grounding, and format requirements."""
    findings = []
    source_text = "\n".join(allowed_inputs)

    for pii_type, pattern in PII_PATTERNS.items():
        for match in pattern.finditer(report):
            findings.append(
                {
                    "type": "pii",
                    "category": pii_type,
                    "matched": match.group(0),
                    "message": f"Remove {pii_type} from the report.",
                }
            )

    for source_input in allowed_inputs:
        for match in PATIENT_NAME_PATTERN.finditer(source_input):
            patient_name = match.group(1).strip(" .,;:")
            if re.search(re.escape(patient_name), report, re.IGNORECASE):
                findings.append(
                    {
                        "type": "patient_name",
                        "matched": patient_name,
                        "message": "Remove the patient's name from the report.",
                    }
                )

    for term in INTERNAL_ONLY_TERMS:
        for match in re.finditer(re.escape(term), report, re.IGNORECASE):
            findings.append(
                {
                    "type": "internal_only_term",
                    "matched": match.group(0),
                    "message": f"Remove internal-only term {term} from the report.",
                }
            )

    for match in REFERENCE_TOKEN_PATTERN.finditer(report):
        token = match.group(0)
        if token not in source_text:
            findings.append(
                {
                    "type": "ungrounded_reference",
                    "matched": token,
                    "message": "Remove or ground this reference in the allowed source inputs.",
                }
            )

    word_count = len(re.findall(r"\b[\w'-]+\b", report))
    if word_count > 800:
        findings.append(
            {
                "type": "length",
                "matched": word_count,
                "message": "Shorten the report to 800 words or fewer.",
            }
        )

    for heading in REQUIRED_REPORT_HEADINGS:
        if heading not in report:
            findings.append(
                {
                    "type": "missing_section",
                    "matched": heading,
                    "message": f"Add the required section heading {heading}.",
                }
            )

    return json.dumps({"label": "fail" if findings else "pass", "findings": findings})
