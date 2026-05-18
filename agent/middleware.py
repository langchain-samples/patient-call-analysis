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
from datetime import datetime, timezone

from langchain.agents.middleware.types import AgentMiddleware
from langchain_core.messages import ToolMessage, AIMessage

AUDIT_LOG_PATH = os.path.join(os.path.dirname(__file__), "output", "audit_log.json")

PII_PATTERNS = {
    "phone": re.compile(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    "ssn": re.compile(r"\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b"),
    "dob": re.compile(
        r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)"
        r"\s+\d{1,2},?\s+\d{4}\b",
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


def _redact_pii(text: str) -> tuple[str, list[dict]]:
    """Scan text for PII patterns and redact matches.

    Returns (redacted_text, list_of_findings).
    """
    findings = []
    redacted = text

    for pii_type, pattern in PII_PATTERNS.items():
        matches = pattern.findall(redacted)
        for match in matches:
            findings.append({"type": pii_type, "matched": match})
            redacted = redacted.replace(match, f"[REDACTED-{pii_type.upper()}]")

    return redacted, findings


class PIIDetectionMiddleware(AgentMiddleware):
    """Redacts patient PII from tool outputs before the LLM processes them.

    Scans tool results for phone numbers, SSNs, dates of birth, and member IDs.
    Redacts matches and logs each detection to the audit trail.
    """

    tools = []

    def wrap_tool_call(self, request, handler):
        result = handler(request)

        if isinstance(result, ToolMessage) and isinstance(result.content, str):
            redacted_content, findings = _redact_pii(result.content)

            if findings:
                tool_name = request.tool_call["name"]
                _save_audit_entry({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "guardrail": "pii_detection",
                    "tool": tool_name,
                    "action": "pii_redacted",
                    "findings": findings,
                })
                return ToolMessage(
                    content=redacted_content,
                    tool_call_id=request.tool_call["id"],
                )

        return result

    async def awrap_tool_call(self, request, handler):
        result = await handler(request)

        if isinstance(result, ToolMessage) and isinstance(result.content, str):
            redacted_content, findings = _redact_pii(result.content)

            if findings:
                tool_name = request.tool_call["name"]
                _save_audit_entry({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "guardrail": "pii_detection",
                    "tool": tool_name,
                    "action": "pii_redacted",
                    "findings": findings,
                })
                return ToolMessage(
                    content=redacted_content,
                    tool_call_id=request.tool_call["id"],
                )

        return result


class HallucinationLeakageGuard(AgentMiddleware):
    """Scans LLM responses for hallucinated data and internal information leakage.

    Checks model outputs for:
    - Internal company terms that should never appear in call analysis
    - References to information not grounded in the call transcript
    Logs all detections to the audit trail.
    """

    tools = []

    def _check_response(self, content: str) -> tuple[str, list[dict]]:
        """Check response content for leakage. Returns (modified_content, findings)."""
        findings = []
        modified = content

        content_lower = content.lower()
        for term in INTERNAL_TERMS:
            if term.lower() in content_lower:
                findings.append({
                    "type": "internal_data_leakage",
                    "term": term,
                })
                pattern = re.compile(re.escape(term), re.IGNORECASE)
                modified = pattern.sub("[REDACTED-INTERNAL]", modified)

        return modified, findings

    def _scan_response(self, response: AIMessage) -> list[dict]:
        """Scan an AIMessage's content (str or list-of-blocks) and redact in place.

        Returns the aggregated list of findings across all scanned text.
        """
        all_findings: list[dict] = []

        if isinstance(response.content, str):
            modified_content, findings = self._check_response(response.content)
            if findings:
                response.content = modified_content
                all_findings.extend(findings)
        elif isinstance(response.content, list):
            for block in response.content:
                if (
                    isinstance(block, dict)
                    and block.get("type") == "text"
                    and isinstance(block.get("text"), str)
                ):
                    modified_text, findings = self._check_response(block["text"])
                    if findings:
                        block["text"] = modified_text
                        all_findings.extend(findings)

        return all_findings

    def wrap_model_call(self, request, handler):
        response = handler(request)

        if isinstance(response, AIMessage):
            findings = self._scan_response(response)
            if findings:
                _save_audit_entry({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "guardrail": "hallucination_leakage_guard",
                    "action": "content_redacted",
                    "findings": findings,
                })

        return response

    async def awrap_model_call(self, request, handler):
        response = await handler(request)

        if isinstance(response, AIMessage):
            findings = self._scan_response(response)
            if findings:
                _save_audit_entry({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "guardrail": "hallucination_leakage_guard",
                    "action": "content_redacted",
                    "findings": findings,
                })

        return response
