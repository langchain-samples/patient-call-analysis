"""Final report review tool for the Strands implementation."""

import json
from typing import Literal

from pydantic import BaseModel
from strands import Agent, tool

from .model import DEFAULT_SPECIALIST_MODEL, create_gateway_model

FINAL_REVIEW_SYSTEM_PROMPT = """\
Review the final report and verify it includes these sections:
- Call Summary
- Adverse Events
- Overall Assessment

Only flag if absolutely necessary.

Respond with JSON: {"label": "pass"} or {"label": "fail"}"""


class ReviewResult(BaseModel):
    label: Literal["pass", "fail"]


def create_final_review_tool(model_id: str = DEFAULT_SPECIALIST_MODEL):
    """Create a stateless final-review tool backed by a Strands agent."""

    @tool(name="final_review", description="Review a call analysis report.")
    def final_review(report: str) -> str:
        """Review a call analysis report for its required sections."""
        reviewer = Agent(
            model=create_gateway_model(model_id, temperature=0),
            system_prompt=FINAL_REVIEW_SYSTEM_PROMPT,
            structured_output_model=ReviewResult,
            callback_handler=None,
        )
        result = reviewer(report)
        review = result.structured_output
        if not isinstance(review, ReviewResult):
            raise ValueError("Final review did not return a structured result.")
        return json.dumps({"label": review.label})

    return final_review
