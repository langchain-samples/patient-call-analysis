import asyncio
import json
from types import SimpleNamespace
from unittest.mock import patch

from langchain.agents.middleware.types import ModelResponse
from langchain_core.messages import AIMessage

from agent.middleware import HallucinationLeakageGuard, PIIDetectionMiddleware
from agent.mock_data import MOCK_TRANSCRIPT

IDENTIFIERS = (
    "Margaret Chen",
    "March 15, 1958",
    "3/15/1958",
    "PAT-20241087",
    "555-867-5309",
)


def _request():
    return SimpleNamespace(tool_call={"name": "transcribe_call", "id": "call-1"})


def _model_response(content):
    return ModelResponse([AIMessage(content=content)])


def test_internal_qa_report_redacts_all_patient_identifiers(tmp_path):
    report = (
        "Internal QA audit report for Margaret Chen: DOB 3/15/1958, "
        "member PAT-20241087, phone 555-867-5309. " + MOCK_TRANSCRIPT
    )
    middleware = PIIDetectionMiddleware(patient_name="Margaret Chen")

    with patch("agent.middleware.AUDIT_LOG_PATH", str(tmp_path / "audit.json")):
        response = middleware.wrap_model_call(
            _request(), lambda request: _model_response(report)
        )
        redacted = response.result[0].content
        audit_entries = json.loads((tmp_path / "audit.json").read_text())

    assert all(identifier not in redacted for identifier in IDENTIFIERS)
    assert "[REDACTED-NAME]" in redacted
    assert "[REDACTED-DOB]" in redacted
    assert "[REDACTED-MEMBER_ID]" in redacted
    assert "[REDACTED-PHONE]" in redacted
    assert any(entry["action"] == "model_output_redacted" for entry in audit_entries)


def test_model_output_redacts_typed_content_blocks_and_preserves_metadata(tmp_path):
    content = [
        {"type": "text", "text": "Margaret Chen, PAT-20241087, 3/15/1958"},
        {"type": "image", "source": {"type": "base64", "data": "abc"}},
    ]
    middleware = PIIDetectionMiddleware(patient_name="Margaret Chen")

    with patch("agent.middleware.AUDIT_LOG_PATH", str(tmp_path / "audit.json")):
        response = middleware.wrap_model_call(
            _request(),
            lambda request: ModelResponse(
                [AIMessage(content=content, response_metadata={"source": "test"})]
            ),
        )

    message = response.result[0]
    assert message.response_metadata == {"source": "test"}
    assert message.content[0]["text"] == (
        "[REDACTED-NAME], [REDACTED-MEMBER_ID], [REDACTED-DOB]"
    )
    assert message.content[1] == content[1]


def test_async_model_output_hook_redacts_content(tmp_path):
    middleware = PIIDetectionMiddleware(patient_name="Margaret Chen")

    async def run():
        with patch("agent.middleware.AUDIT_LOG_PATH", str(tmp_path / "audit.json")):

            async def handler(request):
                return _model_response(
                    "Margaret Chen, 3/15/1958, PAT-20241087, 555-867-5309"
                )

            return await middleware.awrap_model_call(
                _request(),
                handler,
            )

    response = asyncio.run(run())
    assert "Margaret Chen" not in response.result[0].content
    assert "[REDACTED-DOB]" in response.result[0].content


def test_hallucination_guard_processes_typed_content_blocks(tmp_path):
    guard = HallucinationLeakageGuard()
    content = [
        {"type": "text", "text": "Project Titan"},
        {"type": "image", "source": {"type": "base64", "data": "abc"}},
    ]

    with patch("agent.middleware.AUDIT_LOG_PATH", str(tmp_path / "audit.json")):
        response = guard.wrap_model_call(
            _request(), lambda request: _model_response(content)
        )

    assert response.result[0].content[0]["text"] == "[REDACTED-INTERNAL]"
    assert response.result[0].content[1] == content[1]
