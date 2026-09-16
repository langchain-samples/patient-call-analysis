"""
Final review tool for the patient call analysis agent.

A single-step LLM call that reviews a draft report.
Shows up as a traceable LLM span in LangSmith so the prompt
can be pulled into Playground and tested over a dataset.
"""

import json
from typing import Literal

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from pydantic import BaseModel


FINAL_REVIEW_SYSTEM_PROMPT = """\
Review the final report and verify it includes these sections:
- Call Summary
- Adverse Events
- Overall Assessment

Only flag if absolutely necessary.

Respond with JSON: {{"label": "pass"}} or {{"label": "fail"}}"""


class ReviewResult(BaseModel):
    label: Literal["pass", "fail"]


_chain = None


def _get_chain():
    global _chain
    if _chain is None:
        prompt = ChatPromptTemplate.from_messages([
            ("system", FINAL_REVIEW_SYSTEM_PROMPT),
            ("human", "{report}"),
        ])
        llm = ChatAnthropic(
            model="claude-haiku-4-5", temperature=0,
        ).with_structured_output(ReviewResult)
        _chain = prompt | llm
    return _chain


@tool
def final_review(report: str) -> str:
    """Review a call analysis report.

    Args:
        report: The draft report text to review.
    """
    chain = _get_chain()
    result = chain.invoke({"report": report})
    return json.dumps({"label": result.label})
