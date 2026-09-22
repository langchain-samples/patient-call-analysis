"""Agent performance review subagent configuration."""

from pathlib import Path

from strands import Agent, AgentSkills
from strands.models import Model

AGENT_PERFORMANCE_PROMPT = (
    "You are a QA specialist evaluating a pharmaceutical patient support agent.\n\n"
    "WORKFLOW:\n"
    "1. Call skills with skill_name sop-compliance-checklist\n"
    "2. Call skills with skill_name adverse-event-reporting-guidelines\n"
    "3. Score the agent against both, then return a JSON summary.\n\n"
    "Return this exact structure:\n"
    "```json\n"
    "{\n"
    '  "overall_score": <int 0-100>,\n'
    '  "rating": "<Excellent|Satisfactory|Needs Improvement|Unsatisfactory>",\n'
    '  "sections": [\n'
    '    {"name": "...", "score": "<Completed|Partially|Not Completed>", "evidence": "..."}\n'
    "  ],\n"
    '  "ae_compliance": {"compliant": <bool>, "notes": "..."},\n'
    '  "strengths": ["..."],\n'
    '  "improvements": ["..."]\n'
    "}\n"
    "```\n\n"
    "Two skill calls, then respond with ONLY the JSON. No prose."
)

_SKILLS_DIR = Path(__file__).resolve().parents[1] / "skills"


def create_agent_performance_subagent(model: Model) -> Agent:
    """Create the SOP and reporting compliance specialist."""
    return Agent(
        name="agent_performance",
        description=(
            "Review the call agent's performance against SOPs and reporting guidelines. "
            "Returns a structured JSON summary with compliance scores."
        ),
        system_prompt=AGENT_PERFORMANCE_PROMPT,
        model=model,
        plugins=[AgentSkills(skills=_SKILLS_DIR)],
        callback_handler=None,
    )
