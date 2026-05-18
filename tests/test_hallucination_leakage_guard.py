"""Regression tests for HallucinationLeakageGuard.

Covers the bug where INTERNAL_TERMS leaked through tool-using turns because
``AIMessage.content`` was a list of content blocks rather than a string, and
the guard's ``isinstance(content, str)`` gate skipped redaction.
"""

import os
import sys

import pytest
from langchain_core.messages import AIMessage

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agent"))

from middleware import HallucinationLeakageGuard, INTERNAL_TERMS  # noqa: E402


def _run(guard: HallucinationLeakageGuard, message: AIMessage) -> AIMessage:
    """Drive ``wrap_model_call`` with a handler that returns ``message``."""
    return guard.wrap_model_call(request=object(), handler=lambda _req: message)


def test_redacts_internal_terms_in_string_content():
    guard = HallucinationLeakageGuard()
    msg = AIMessage(content="The compound is NVS-4892 in Phase IIb under Project Titan.")
    out = _run(guard, msg)
    assert isinstance(out.content, str)
    for term in ("NVS-4892", "Phase IIb", "Project Titan"):
        assert term not in out.content
    assert "[REDACTED-INTERNAL]" in out.content


def test_redacts_internal_terms_in_list_content_with_tool_use_blocks():
    """Regression: list-shaped content (text + tool_use blocks) must also be scanned."""
    guard = HallucinationLeakageGuard()
    msg = AIMessage(
        content=[
            {
                "type": "text",
                "text": "Logged in VoiceIQ as Project Titan ticket NOVA-2024 (Phase IIb).",
            },
            {
                "type": "tool_use",
                "id": "tool_1",
                "name": "transcribe_call",
                "input": {},
            },
        ]
    )
    out = _run(guard, msg)
    assert isinstance(out.content, list)
    text_block = out.content[0]
    for term in ("VoiceIQ", "Project Titan", "NOVA-2024", "Phase IIb"):
        assert term not in text_block["text"]
    assert "[REDACTED-INTERNAL]" in text_block["text"]
    # Non-text blocks must be left untouched.
    assert out.content[1]["type"] == "tool_use"
    assert out.content[1]["name"] == "transcribe_call"


def test_list_content_without_internal_terms_is_unchanged():
    guard = HallucinationLeakageGuard()
    original_text = "The patient reported mild headaches; no further action."
    msg = AIMessage(
        content=[
            {"type": "text", "text": original_text},
            {"type": "tool_use", "id": "t", "name": "x", "input": {}},
        ]
    )
    out = _run(guard, msg)
    assert out.content[0]["text"] == original_text


@pytest.mark.parametrize("term", INTERNAL_TERMS)
def test_every_internal_term_is_redacted_in_list_content(term):
    guard = HallucinationLeakageGuard()
    msg = AIMessage(
        content=[{"type": "text", "text": f"Reference: {term} appears here."}]
    )
    out = _run(guard, msg)
    assert term.lower() not in out.content[0]["text"].lower()


@pytest.mark.asyncio
async def test_awrap_model_call_redacts_list_content():
    guard = HallucinationLeakageGuard()
    msg = AIMessage(
        content=[
            {"type": "text", "text": "Filed Salesforce case ID under CRM ticket."},
            {"type": "tool_use", "id": "t", "name": "x", "input": {}},
        ]
    )

    async def handler(_req):
        return msg

    out = await guard.awrap_model_call(request=object(), handler=handler)
    text = out.content[0]["text"]
    assert "Salesforce case ID" not in text
    assert "CRM ticket" not in text
    assert "[REDACTED-INTERNAL]" in text
