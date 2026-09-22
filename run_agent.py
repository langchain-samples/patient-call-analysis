"""
CLI entry point for the patient call analysis agent.

Usage:
    python run_agent.py
    python run_agent.py --audio path/to/call.mp3
    python run_agent.py --implementation strands
    python run_agent.py --model claude-sonnet-4-5-20250929
"""

import argparse
import os
import sys
import uuid

from dotenv import load_dotenv

load_dotenv(override=True)


def main():
    parser = argparse.ArgumentParser(description="Patient Call Analysis Agent")
    parser.add_argument("--audio", type=str, default="", help="Path to call audio file")
    parser.add_argument("--model", type=str, default="claude-sonnet-4-5-20250929", help="Model to use")
    parser.add_argument(
        "--implementation",
        choices=["deepagents", "strands"],
        default="deepagents",
        help="Agent framework to use",
    )
    args = parser.parse_args()

    if not os.environ.get("LANGSMITH_API_KEY"):
        print("Error: LANGSMITH_API_KEY environment variable is required.")
        print("Copy .env.example to .env and add your LangSmith API key.")
        sys.exit(1)

    os.environ.setdefault("LANGSMITH_GATEWAY", "true")

    if args.audio:
        user_message = f"Analyze the patient call from this audio file: {args.audio}"
    else:
        user_message = "Analyze the patient call."

    print("Starting patient call analysis...\n")

    if args.implementation == "strands":
        from agent.strands import create_orchestrator

        agent = create_orchestrator(model=args.model)
        final_message = str(agent(user_message)).strip()
    else:
        deepagents_dir = os.path.join(os.path.dirname(__file__), "agent", "deepagents")
        sys.path.insert(0, deepagents_dir)
        from deep_agent import create_orchestrator

        agent, _ = create_orchestrator(model=args.model)
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}
        result = agent.invoke(
            {"messages": [{"role": "user", "content": user_message}]},
            config=config,
        )
        final_message = result["messages"][-1].content

    print(final_message)


if __name__ == "__main__":
    main()
