"""Guardrail hook for the Strands patient call analysis agent."""

import json
import os
import re
import threading
from datetime import datetime, timezone

from strands.hooks import AfterModelCallEvent, HookRegistry

AUDIT_LOG_PATH = os.path.join(os.path.dirname(__file__), "output", "audit_log.json")
_AUDIT_LOG_LOCK = threading.Lock()

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
    with _AUDIT_LOG_LOCK:
        os.makedirs(os.path.dirname(AUDIT_LOG_PATH), exist_ok=True)
        log = _load_audit_log()
        log.append(entry)
        with open(AUDIT_LOG_PATH, "w") as f:
            json.dump(log, f, indent=2)


class HallucinationLeakageGuard:
    """Redact the same fixed internal terms as the Deep Agents middleware."""

    def register_hooks(self, registry: HookRegistry) -> None:
        registry.add_callback(AfterModelCallEvent, self._after_model_call)

    def _check_response(self, content: str) -> tuple[str, list[dict]]:
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

    def _after_model_call(self, event: AfterModelCallEvent) -> None:
        if event.stop_response is None:
            return

        findings = []
        for block in event.stop_response.message.get("content", []):
            content = block.get("text")
            if not isinstance(content, str):
                continue
            modified_content, block_findings = self._check_response(content)
            block["text"] = modified_content
            findings.extend(block_findings)

        if findings:
            _save_audit_entry({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "guardrail": "hallucination_leakage_guard",
                "action": "content_redacted",
                "findings": findings,
            })
