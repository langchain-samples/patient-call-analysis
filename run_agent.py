"""
CLI entry point for the patient call analysis agent.

Usage:
    python run_agent.py
    python run_agent.py --audio path/to/call.mp3
    python run_agent.py --model claude-sonnet-4-5-20250929
"""

import argparse
import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agent"))

from dotenv import load_dotenv
load_dotenv(override=True)

from deep_agent import create_orchestrator
from middleware import build_trace_metadata


def main():
    parser = argparse.ArgumentParser(description="Patient Call Analysis Agent")
    parser.add_argument("--audio", type=str, default="", help="Path to call audio file")
    parser.add_argument("--model", type=str, default="claude-sonnet-4-5-20250929", help="Model to use")
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable is required.")
        print("Copy .env.example to .env and add your API key.")
        sys.exit(1)

    agent, store = create_orchestrator(model=args.model)

    if args.audio:
        user_message = f"Analyze the patient call from this audio file: {args.audio}"
    else:
        user_message = "Analyze the patient call. Use the demo transcript."

    thread_id = f"call-analysis-{uuid.uuid4()}"
    config = {
        "configurable": {"thread_id": thread_id},
        "metadata": build_trace_metadata(user_message, thread_id),
    }

    print("Starting patient call analysis...\n")

    result = agent.invoke(
        {"messages": [{"role": "user", "content": user_message}]},
        config=config,
    )

    final_message = result["messages"][-1].content
    print(final_message)


if __name__ == "__main__":
    main()
