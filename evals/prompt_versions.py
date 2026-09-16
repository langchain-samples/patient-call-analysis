"""
System prompt versions for evaluation.

Pulls prompt versions from LangSmith Prompt Hub by tag.
Each tag corresponds to a different prompting strategy.
"""

from langsmith import Client

PROMPT_NAME = "call-analysis-orchestrator"

PROMPT_TAGS = {
    "v1_detailed": "v1_detailed",
    "v2_safety_focused": "v2_safety_focused",
    "v3_structured": "v3_structured",
    "v4_minimal": "v4_minimal",
}


def _pull_system_prompt(tag: str) -> str:
    """Pull a prompt from LangSmith Prompt Hub by tag and extract the system message."""
    client = Client()
    prompt = client.pull_prompt(f"{PROMPT_NAME}:{tag}")
    messages = prompt.invoke({"messages": []}).to_messages()
    for msg in messages:
        if msg.type == "system":
            return msg.content
    return str(messages[0].content)


def get_prompt_versions() -> dict[str, str]:
    """Pull all tagged prompt versions from the hub."""
    versions = {}
    for version_name, tag in PROMPT_TAGS.items():
        versions[version_name] = _pull_system_prompt(tag)
    return versions
