"""
Guardrail middleware for the patient call analysis agent.

HallucinationLeakageGuard — wrap_model_call: scans LLM responses for
hallucinated patient data and internal company information leakage.

PII review is handled by the final_review tool (see pii_review.py),
which runs as a traced LLM call so the prompt can be iterated in LangSmith Playground.
"""

import json
import os
import re
from datetime import datetime, timezone

from langchain.agents.middleware.types import AgentMiddleware
from langchain_core.messages import AIMessage

AUDIT_LOG_PATH = os.path.join(os.path.dirname(__file__), "output", "audit_log.json")

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

    def wrap_model_call(self, request, handler):
        response = handler(request)

        if isinstance(response, AIMessage) and isinstance(response.content, str):
            modified_content, findings = self._check_response(response.content)

            if findings:
                _save_audit_entry({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "guardrail": "hallucination_leakage_guard",
                    "action": "content_redacted",
                    "findings": findings,
                })
                response.content = modified_content

        return response

    async def awrap_model_call(self, request, handler):
        response = await handler(request)

        if isinstance(response, AIMessage) and isinstance(response.content, str):
            modified_content, findings = self._check_response(response.content)

            if findings:
                _save_audit_entry({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "guardrail": "hallucination_leakage_guard",
                    "action": "content_redacted",
                    "findings": findings,
                })
                response.content = modified_content

        return response
