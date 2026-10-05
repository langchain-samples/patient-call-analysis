"""
Reasoning + to-do-list agent — a LangSmith tracing demo.

A small Deep Agent that:
  1. plans with the built-in `write_todos` to-do list, and
  2. runs on a Claude model with extended *thinking* (reasoning) enabled,

so both the to-do list and the model's reasoning show up natively in the LangSmith trace.

Usage:
    python reasoning_agent.py
    python reasoning_agent.py --model claude-sonnet-4-5-20250929 --thinking-budget 1500

Then open the 'reasoning-agent-demo' project in LangSmith:
  - each model call shows a "reasoning" block (the model's thinking)
  - the `write_todos` tool calls show the plan and its pending -> in_progress -> completed status
"""

import argparse
import os
import sys
import uuid

from dotenv import load_dotenv

load_dotenv(override=True)


TRIAGE_TASK = (
    "Triage this patient call. First make a to-do list, then work through it:\n"
    "  1. List the adverse events the patient reported.\n"
    "  2. Flag any billing issue.\n"
    "  3. Write a one-line recommended follow-up action.\n\n"
    "CALL TRANSCRIPT:\n{transcript}"
)


def main():
    parser = argparse.ArgumentParser(description="Reasoning + to-do-list tracing demo")
    parser.add_argument("--model", default="claude-sonnet-4-5-20250929", help="Claude model to use")
    parser.add_argument(
        "--thinking-budget",
        type=int,
        default=1500,
        help="Extended-thinking token budget (the reasoning allowance).",
    )
    parser.add_argument(
        "--project",
        default="reasoning-agent-demo",
        help="LangSmith project to trace into (overrides LANGSMITH_PROJECT from .env).",
    )
    args = parser.parse_args()

    for var in ("LANGSMITH_API_KEY", "ANTHROPIC_API_KEY"):
        if not os.environ.get(var):
            print(f"Error: {var} is required. Copy .env.example to .env and fill it in.")
            sys.exit(1)

    # Trace natively to LangSmith under an easy-to-find project (overrides .env's LANGSMITH_PROJECT).
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_PROJECT"] = args.project

    # Reuse the demo transcript from the deepagents implementation.
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agent", "deepagents"))
    from mock_data import MOCK_TRANSCRIPT

    from langchain_anthropic import ChatAnthropic
    from deepagents import create_deep_agent

    # Enable extended thinking so reasoning blocks appear in the trace.
    # max_tokens must exceed the thinking budget, so size it off the budget.
    model = ChatAnthropic(
        model=args.model,
        max_tokens=args.thinking_budget + 2500,
        thinking={"type": "enabled", "budget_tokens": args.thinking_budget},
    )

    # create_deep_agent includes the built-in `write_todos` to-do-list middleware.
    agent = create_deep_agent(
        model=model,
        system_prompt=(
            "You are a patient-call triage assistant. For any task, FIRST call write_todos "
            "to plan the steps, then work through them, marking each completed as you go."
        ),
    )

    print("Running reasoning + to-do-list agent (tracing to LangSmith)...\n")
    result = agent.invoke(
        {"messages": [{"role": "user", "content": TRIAGE_TASK.format(transcript=MOCK_TRANSCRIPT)}]},
        config={"configurable": {"thread_id": str(uuid.uuid4())}},
    )

    # --- The plan: the to-do list the agent built (from agent state) ---
    print("TO-DO LIST (agent state):")
    for todo in result.get("todos", []):
        print(f"  [{todo.get('status')}] {todo.get('content')}")

    # --- The reasoning: model thinking captured as `reasoning` content blocks ---
    print("\nREASONING (model thinking blocks):")
    found = False
    for message in result["messages"]:
        for block in getattr(message, "content_blocks", None) or []:
            if isinstance(block, dict) and block.get("type") == "reasoning":
                text = (block.get("reasoning") or "").strip()
                if text:
                    found = True
                    print(f"  • {text[:300]}{'...' if len(text) > 300 else ''}")
    if not found:
        print("  (none captured this run)")

    # --- Final answer ---
    final = result["messages"][-1].content
    print("\nFINAL TRIAGE:\n" + (final if isinstance(final, str) else str(final)))

    project = os.environ["LANGSMITH_PROJECT"]
    print(
        f"\nTrace logged to LangSmith project '{project}'. Open it to see the reasoning blocks "
        "and the write_todos plan inline in the trace."
    )


if __name__ == "__main__":
    main()
