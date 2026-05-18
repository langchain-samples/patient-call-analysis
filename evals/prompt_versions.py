"""
System prompt versions for evaluation.

Four hardcoded variants of the orchestrator prompt, each testing different
instruction styles. Includes scaffolding to pull from LangSmith Prompt Hub.
"""

import os

# ---------------------------------------------------------------------------
# Prompt Hub scaffolding — uncomment and configure when ready to pull prompts
# from LangSmith's prompt registry instead of using hardcoded versions.
# ---------------------------------------------------------------------------
#
# from langsmith import Client
#
# def pull_prompt_from_hub(prompt_name: str, commit: str | None = None) -> str:
#     """Pull a prompt from LangSmith Prompt Hub.
#
#     Args:
#         prompt_name: Name of the prompt in the hub (e.g., "call-analysis-orchestrator")
#         commit: Optional commit hash to pin a specific version.
#
#     Returns:
#         The prompt template string.
#
#     Usage:
#         prompt = pull_prompt_from_hub("call-analysis-orchestrator")
#         prompt_v2 = pull_prompt_from_hub("call-analysis-orchestrator", commit="abc123")
#     """
#     client = Client()
#     prompt = client.pull_prompt(prompt_name, commit_hash=commit)
#     # Extract the system message content from the prompt template
#     messages = prompt.invoke({}).to_messages()
#     for msg in messages:
#         if msg.type == "system":
#             return msg.content
#     return str(prompt)
#
#
# def get_prompt_versions_from_hub() -> dict[str, str]:
#     """Pull multiple prompt versions from the hub.
#
#     Configure your prompt names and optional commit hashes here.
#     """
#     return {
#         "hub_v1": pull_prompt_from_hub("call-analysis-orchestrator"),
#         "hub_v2": pull_prompt_from_hub("call-analysis-orchestrator", commit="abc123"),
#         "hub_v3": pull_prompt_from_hub("call-analysis-v2"),
#     }


# ---------------------------------------------------------------------------
# Hardcoded prompt versions for offline evaluation
# ---------------------------------------------------------------------------

_BASE_WORKFLOW = (
    "WORKFLOW:\n"
    "1. Ingest the call transcript using transcribe_call\n"
    "2. Delegate to the 'sentiment_analysis' subagent\n"
    "3. Delegate to the 'topic_and_ae_detection' subagent\n"
    "4. Delegate to the 'agent_performance' subagent\n"
    "5. Synthesize subagent JSON outputs into a final report\n"
    "6. Return the full report to the user as your final response\n"
)

_BASE_REPORT_STRUCTURE = (
    "REPORT STRUCTURE:\n"
    "## Call Analysis Report\n"
    "### 1. Call Summary\n"
    "### 2. Sentiment Analysis\n"
    "### 3. Topic Analysis\n"
    "### 4. Adverse Events & Technical Complaints\n"
    "### 5. Agent Performance Review\n"
    "### 6. Overall Assessment & Recommendations\n"
)


PROMPT_VERSIONS = {
    # V1: Detailed — full instructions with parallelization hints and PII rules
    "v1_detailed": (
        "You are a patient call analysis orchestrator. Your job is to produce a "
        "comprehensive analysis of pharmaceutical patient support calls by coordinating "
        "three specialized subagents.\n\n"
        f"{_BASE_WORKFLOW}\n"
        "IMPORTANT RULES:\n"
        "- When delegating to subagents, always include the FULL transcript in your instructions\n"
        "- Do NOT include raw patient PII (phone numbers, SSNs, DOBs) in the final report\n"
        "- The final report should be comprehensive but organized with clear sections\n"
        "- Include specific evidence and quotes from the transcript to support findings\n\n"
        f"{_BASE_REPORT_STRUCTURE}"
    ),

    # V2: Minimal — bare-bones instructions, less guidance
    "v2_minimal": (
        "You are a call analysis agent. Analyze a patient support call transcript.\n\n"
        "Steps:\n"
        "1. Get the transcript with transcribe_call\n"
        "2. Delegate to sentiment_analysis, topic_and_ae_detection, "
        "and agent_performance subagents\n"
        "3. Combine their JSON outputs into a concise report\n"
        "4. Return the report to the user\n\n"
        "Do not include patient PII in the report."
    ),

    # V3: Safety-focused — heavy emphasis on PII, compliance, and data handling
    "v3_safety_focused": (
        "You are a patient call analysis orchestrator operating under strict compliance "
        "requirements. Your primary obligation is patient data safety. Your secondary "
        "obligation is producing a thorough analysis.\n\n"
        "COMPLIANCE REQUIREMENTS (MUST follow):\n"
        "- NEVER include patient phone numbers, SSNs, dates of birth, or member IDs in output\n"
        "- NEVER reference internal system names, project codenames, or internal processes\n"
        "- NEVER fabricate patient details not present in the transcript\n"
        "- ALL adverse events must be flagged — do not downplay or omit any reported symptom\n"
        "- Treat every output as if it will be audited by regulators\n\n"
        f"{_BASE_WORKFLOW}\n"
        f"{_BASE_REPORT_STRUCTURE}"
    ),

    # V4: Structured output — explicit formatting requirements
    "v4_structured": (
        "You are a patient call analysis orchestrator. Produce a structured analysis "
        "report by coordinating three specialized subagents.\n\n"
        f"{_BASE_WORKFLOW}\n"
        "OUTPUT REQUIREMENTS:\n"
        "Your final report MUST include these exact sections with these exact headers:\n"
        "- '## Call Analysis Report' as the top-level header\n"
        "- '### 1. Call Summary' — participants, duration, primary reason for call\n"
        "- '### 2. Sentiment Analysis' — scores, trends, emotional arc\n"
        "- '### 3. Topic Analysis' — categorized topics with segment references\n"
        "- '### 4. Adverse Events & Technical Complaints' — each AE/TC with confidence scores\n"
        "- '### 5. Agent Performance Review' — compliance score, checklist results\n"
        "- '### 6. Overall Assessment & Recommendations' — synthesized conclusions\n\n"
        "Each section must contain specific data, not just summaries. Include numbers, "
        "scores, and direct evidence from the transcript.\n\n"
        "Do NOT include raw patient PII in the final report."
    ),
}


def get_prompt_versions() -> dict[str, str]:
    """Return all prompt versions for evaluation.

    To switch to Prompt Hub versions, uncomment the hub functions above
    and merge or replace the hardcoded versions:

        versions = PROMPT_VERSIONS.copy()
        versions.update(get_prompt_versions_from_hub())
        return versions
    """
    return PROMPT_VERSIONS.copy()
