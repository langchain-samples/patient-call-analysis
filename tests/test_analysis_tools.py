import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "agent"))

from mock_data import MOCK_TRANSCRIPT
from prompts import REQUIRED_REPORT_HEADINGS
from tools.analysis_tools import final_review


def review(report, allowed_inputs):
    return json.loads(
        final_review.invoke(
            {
                "report": report,
                "allowed_inputs": allowed_inputs,
            }
        )
    )


def complete_report():
    return "\n".join(["## Call Analysis Report", *REQUIRED_REPORT_HEADINGS])


def test_review_flags_fixture_identifiers_and_internal_terms():
    report = (
        complete_report()
        + "\nMargaret Chen, March 15, 1958, PAT-20241087, VoiceIQ, and Project Titan."
    )

    result = review(report, [MOCK_TRANSCRIPT])

    assert result["label"] == "fail"
    matched = {finding["matched"] for finding in result["findings"]}
    assert {
        "Margaret Chen",
        "March 15, 1958",
        "PAT-20241087",
        "VoiceIQ",
        "Project Titan",
    } <= matched


def test_review_flags_ungrounded_reference():
    result = review(
        complete_report() + "\nSee CASE-9999 for details.",
        ["The transcript contains no case reference."],
    )

    assert result["label"] == "fail"
    assert any(finding["matched"] == "CASE-9999" for finding in result["findings"])


def test_review_flags_overlong_and_incomplete_report():
    report = "## Call Analysis Report\n" + ("word " * 801)

    result = review(report, [])

    assert result["label"] == "fail"
    assert any(finding["type"] == "length" for finding in result["findings"])
    assert (
        sum(finding["type"] == "missing_section" for finding in result["findings"]) == 6
    )


def test_review_passes_clean_compliant_report():
    result = review(complete_report(), [MOCK_TRANSCRIPT])

    assert result == {"label": "pass", "findings": []}
