"""Regression tests for output-side patient-PII redaction in HallucinationLeakageGuard.

These cover the leak documented in issue 7bd58642 — patient DOB rendered as
numeric `M/D/YYYY` and member IDs (`PAT-########`) reaching the final
synthesized Call Analysis Report because:

  * `PII_PATTERNS["dob"]` only matched verbose month-name dates, and
  * `HallucinationLeakageGuard.wrap_model_call` only scanned `INTERNAL_TERMS`
    and silently skipped list-shaped `AIMessage.content`.
"""

from __future__ import annotations

import json
import os
import tempfile
from unittest import mock

from langchain_core.messages import AIMessage

from agent import middleware as mw


def _run_guard_with_response(response: AIMessage) -> AIMessage:
    """Invoke HallucinationLeakageGuard.wrap_model_call with a stub handler."""
    guard = mw.HallucinationLeakageGuard()
    return guard.wrap_model_call(request=object(), handler=lambda _req: response)


def test_dob_numeric_pattern_matches_slash_and_dash_formats():
    text = "DOB: 3/15/1958, also 03-15-1958 and 12/31/2024."
    redacted, findings = mw._redact_pii(text)
    types = {f["type"] for f in findings}
    assert "dob_numeric" in types
    assert "3/15/1958" not in redacted
    assert "03-15-1958" not in redacted
    assert "12/31/2024" not in redacted
    assert "[REDACTED-DOB_NUMERIC]" in redacted


def test_dob_verbose_pattern_still_matches():
    text = "Patient born March 15, 1958."
    redacted, findings = mw._redact_pii(text)
    types = {f["type"] for f in findings}
    assert "dob_verbose" in types
    assert "March 15, 1958" not in redacted


def test_guard_redacts_pii_in_string_content(tmp_path):
    audit_path = tmp_path / "audit_log.json"
    with mock.patch.object(mw, "AUDIT_LOG_PATH", str(audit_path)):
        response = AIMessage(content="Final report — DOB: 3/15/1958, ID: PAT-20241087")
        result = _run_guard_with_response(response)

    assert "3/15/1958" not in result.content
    assert "PAT-20241087" not in result.content
    assert "[REDACTED-DOB_NUMERIC]" in result.content
    assert "[REDACTED-MEMBER_ID]" in result.content

    log = json.loads(audit_path.read_text())
    assert any(e["guardrail"] == "hallucination_leakage_guard" for e in log)


def test_guard_redacts_pii_in_list_content_blocks(tmp_path):
    """The regression case: AIMessage.content is a list of content blocks."""
    audit_path = tmp_path / "audit_log.json"
    with mock.patch.object(mw, "AUDIT_LOG_PATH", str(audit_path)):
        response = AIMessage(
            content=[
                {"type": "text", "text": "DOB: 3/15/1958, ID: PAT-20241087"},
                {"type": "tool_use", "id": "x", "name": "noop", "input": {}},
            ]
        )
        result = _run_guard_with_response(response)

    text_block = next(b for b in result.content if b.get("type") == "text")
    assert "3/15/1958" not in text_block["text"]
    assert "PAT-20241087" not in text_block["text"]
    assert "[REDACTED-DOB_NUMERIC]" in text_block["text"]
    assert "[REDACTED-MEMBER_ID]" in text_block["text"]

    log = json.loads(audit_path.read_text())
    assert any(
        e["guardrail"] == "hallucination_leakage_guard"
        and e["action"] == "content_redacted_list"
        for e in log
    )


def test_guard_still_redacts_internal_terms(tmp_path):
    audit_path = tmp_path / "audit_log.json"
    with mock.patch.object(mw, "AUDIT_LOG_PATH", str(audit_path)):
        response = AIMessage(content="See Project Titan for context.")
        result = _run_guard_with_response(response)

    assert "Project Titan" not in result.content
    assert "[REDACTED-INTERNAL]" in result.content
