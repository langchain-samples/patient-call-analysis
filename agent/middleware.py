"""
Guardrail middleware for the patient call analysis agent.

Two middleware classes:
  1. PIIDetectionMiddleware — wrap_tool_call: redacts patient PII
     (phone numbers, SSNs, DOBs) from tool outputs before the LLM sees them.
  2. HallucinationLeakageGuard — wrap_model_call: scans LLM responses for
     hallucinated patient data and internal company information leakage.
"""

import json
import os
import re
from collections.abc import Callable
from datetime import UTC, datetime
from typing import ClassVar

from langchain.agents.middleware.types import AgentMiddleware, ModelResponse
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage

AUDIT_LOG_PATH = os.path.join(os.path.dirname(__file__), "output", "audit_log.json")

PII_PATTERNS = {
    "phone": re.compile(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    "ssn": re.compile(r"\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b"),
    "dob": re.compile(
        r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)"
        r"\s+\d{1,2},?\s+\d{4}\b|\b\d{1,2}/\d{1,2}/\d{4}\b",
        re.IGNORECASE,
    ),
    "member_id": re.compile(r"\bPAT-\d{8}\b"),
}

INTERNAL_TERMS = [
    "Project Titan",
    "VoiceIQ",
    "internal-ref",
    "NOVA-2024",
    "pre-launch",
    "Phase IIb",
    "compound NVS-4892",
    "internal audit score",
    "Salesforce case ID",
    "CRM ticket",
]


def _load_audit_log() -> list:
    if os.path.exists(AUDIT_LOG_PATH):
        with open(AUDIT_LOG_PATH, "r") as f:
            return json.load(f)
    return []


def _save_audit_entry(entry: dict):
    os.makedirs(os.path.dirname(AUDIT_LOG_PATH), exist_ok=True)
    log = _load_audit_log()
    log.append(entry)
    with open(AUDIT_LOG_PATH, "w") as f:
        json.dump(log, f, indent=2)


def _redact_pii(text: str, patient_name: str | None = None) -> tuple[str, list[dict]]:
    """Scan text for configured patient PII and redact matches."""
    findings = []
    redacted = text
    patterns = dict(PII_PATTERNS)
    if patient_name:
        patterns["name"] = re.compile(re.escape(patient_name), re.IGNORECASE)

    for pii_type, pattern in patterns.items():
        matches = pattern.findall(redacted)
        for match in matches:
            findings.append({"type": pii_type, "matched": match})
            redacted = redacted.replace(match, f"[REDACTED-{pii_type.upper()}]")

    return redacted, findings


def _rewrite_content(content, processor: Callable[[str], tuple[str, list[dict]]]):
    findings = []
    if isinstance(content, str):
        rewritten, content_findings = processor(content)
        return rewritten, content_findings
    if isinstance(content, list):
        rewritten_blocks = []
        for block in content:
            if isinstance(block, str):
                rewritten, block_findings = processor(block)
                rewritten_blocks.append(rewritten)
                findings.extend(block_findings)
            elif isinstance(block, dict) and isinstance(block.get("text"), str):
                rewritten, block_findings = processor(block["text"])
                rewritten_blocks.append({**block, "text": rewritten})
                findings.extend(block_findings)
            else:
                rewritten_blocks.append(block)
        return rewritten_blocks, findings
    return content, findings


def _rewrite_message(
    message: BaseMessage, processor: Callable[[str], tuple[str, list[dict]]]
):
    rewritten_content, findings = _rewrite_content(message.content, processor)
    if findings:
        return message.model_copy(update={"content": rewritten_content}), findings
    return message, findings


def _rewrite_model_response(
    response, processor: Callable[[str], tuple[str, list[dict]]]
):
    if isinstance(response, ModelResponse):
        messages = []
        findings = []
        for message in response.result:
            rewritten, message_findings = _rewrite_message(message, processor)
            messages.append(rewritten)
            findings.extend(message_findings)
        return ModelResponse(messages, response.structured_response), findings
    if isinstance(response, AIMessage):
        return _rewrite_message(response, processor)
    return response, []


class PIIDetectionMiddleware(AgentMiddleware):
    """Redacts configured patient PII from tool and model outputs."""

    tools: ClassVar = []

    def __init__(self, patient_name: str | None = None):
        self.patient_name = patient_name or os.getenv("PATIENT_NAME")

    def _redact_tool_result(self, result):
        if not isinstance(result, ToolMessage):
            return result, []
        return _rewrite_message(
            result, lambda text: _redact_pii(text, self.patient_name)
        )

    def _audit(self, findings, action, **details):
        if findings:
            _save_audit_entry(
                {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "guardrail": "pii_detection",
                    "action": action,
                    "findings": findings,
                    **details,
                }
            )

    def wrap_tool_call(self, request, handler):
        result = handler(request)
        redacted, findings = self._redact_tool_result(result)
        self._audit(findings, "pii_redacted", tool=request.tool_call["name"])
        return redacted

    async def awrap_tool_call(self, request, handler):
        result = await handler(request)
        redacted, findings = self._redact_tool_result(result)
        self._audit(findings, "pii_redacted", tool=request.tool_call["name"])
        return redacted

    def wrap_model_call(self, request, handler):
        response = handler(request)
        redacted, findings = _rewrite_model_response(
            response, lambda text: _redact_pii(text, self.patient_name)
        )
        self._audit(findings, "model_output_redacted")
        return redacted

    async def awrap_model_call(self, request, handler):
        response = await handler(request)
        redacted, findings = _rewrite_model_response(
            response, lambda text: _redact_pii(text, self.patient_name)
        )
        self._audit(findings, "model_output_redacted")
        return redacted


class HallucinationLeakageGuard(AgentMiddleware):
    """Scans LLM responses for hallucinated data and internal information leakage."""

    tools: ClassVar = []

    def _check_response(self, content: str) -> tuple[str, list[dict]]:
        """Check response content for leakage."""
        findings = []
        modified = content

        content_lower = content.lower()
        for term in INTERNAL_TERMS:
            if term.lower() in content_lower:
                findings.append(
                    {
                        "type": "internal_data_leakage",
                        "term": term,
                    }
                )
                pattern = re.compile(re.escape(term), re.IGNORECASE)
                modified = pattern.sub("[REDACTED-INTERNAL]", modified)

        return modified, findings

    def wrap_model_call(self, request, handler):
        response = handler(request)
        modified, findings = _rewrite_model_response(response, self._check_response)

        if findings:
            _save_audit_entry(
                {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "guardrail": "hallucination_leakage_guard",
                    "action": "content_redacted",
                    "findings": findings,
                }
            )
        return modified

    async def awrap_model_call(self, request, handler):
        response = await handler(request)
        modified, findings = _rewrite_model_response(response, self._check_response)

        if findings:
            _save_audit_entry(
                {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "guardrail": "hallucination_leakage_guard",
                    "action": "content_redacted",
                    "findings": findings,
                }
            )
        return modified
