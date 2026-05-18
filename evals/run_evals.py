"""
Evaluation runner for the patient call analysis agent.

Runs the agent against a LangSmith dataset across 4 system prompt versions,
evaluating trajectory, PII leakage, internal data leakage, report
completeness, and report correctness (LLM-as-judge).

Usage:
    python evals/run_evals.py
    python evals/run_evals.py --prompt-version v1_detailed
    python evals/run_evals.py --model claude-sonnet-4-5-20250929
"""

import argparse
import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agent"))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"), override=True)

from langsmith import evaluate

from dataset import create_dataset
from prompt_versions import get_prompt_versions
from evaluators import ALL_EVALUATORS


DATASET_NAME = "Patient Call Analysis Eval"


def make_run_fn(system_prompt: str, model: str):
    """Create a run function that uses the given system prompt.

    Returns a function compatible with langsmith.evaluate() that:
    1. Creates a fresh orchestrator with the given prompt
    2. Invokes the agent on the input
    3. Captures the trajectory (subagent tool calls) and final output
    """

    def run_agent(inputs: dict) -> dict:
        from deepagents import create_deep_agent
        from deepagents.backends import FilesystemBackend
        from langgraph.checkpoint.memory import MemorySaver

        agent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "agent"))
        sys.path.insert(0, agent_dir)

        from subagents.sentiment import sentiment_subagent
        from subagents.topic_and_ae import topic_and_ae_subagent
        from subagents.agent_performance import agent_performance_subagent
        from tools.transcript_tools import transcribe_call
        from middleware import PIIDetectionMiddleware, HallucinationLeakageGuard

        agent = create_deep_agent(
            name="call-analysis-orchestrator",
            model=model,
            system_prompt=system_prompt,
            tools=[transcribe_call],
            subagents=[
                sentiment_subagent,
                topic_and_ae_subagent,
                agent_performance_subagent,
            ],
            backend=FilesystemBackend(root_dir=agent_dir, virtual_mode=True),
            skills=[os.path.join(agent_dir, "skills") + "/"],
            checkpointer=MemorySaver(),
            middleware=[PIIDetectionMiddleware(), HallucinationLeakageGuard()],
        )

        thread_id = f"eval-{uuid.uuid4()}"
        config = {"configurable": {"thread_id": thread_id}}

        message = inputs.get("message", "Analyze the patient call. Use the demo transcript.")

        trajectory = []
        final_output = ""

        for chunk in agent.stream(
            {"messages": [{"role": "user", "content": message}]},
            config=config,
            stream_mode="debug",
            subgraphs=True,
        ):
            if isinstance(chunk, dict):
                event_type = chunk.get("type", "")
                payload = chunk.get("payload", {})

                if event_type == "task_result" and "name" in payload:
                    tool_name = payload["name"]
                    if tool_name == "task":
                        agent_name = payload.get("result", {})
                        if isinstance(agent_name, dict):
                            agent_name = agent_name.get("agent", "")
                        trajectory.append(str(agent_name))
                    else:
                        trajectory.append(tool_name)

            elif isinstance(chunk, tuple) and len(chunk) == 2:
                namespace, event = chunk
                if isinstance(event, dict):
                    event_type = event.get("type", "")
                    payload = event.get("payload", {})

                    if event_type == "task_result" and "name" in payload:
                        tool_name = payload["name"]
                        if tool_name == "task":
                            args = payload.get("args", {})
                            if isinstance(args, dict):
                                trajectory.append(args.get("agent", tool_name))
                        else:
                            trajectory.append(tool_name)

        state = agent.get_state(config)
        messages = state.values.get("messages", [])
        if messages:
            final_output = messages[-1].content if hasattr(messages[-1], "content") else str(messages[-1])

        return {
            "output": final_output,
            "trajectory": trajectory,
        }

    return run_agent


def run_evaluation(
    prompt_version: str | None = None,
    model: str = "claude-sonnet-4-5-20250929",
):
    """Run evaluations across prompt versions.

    Args:
        prompt_version: If specified, only run this version. Otherwise run all.
        model: Model to use for the agent.
    """
    print("Creating/updating evaluation dataset...")
    create_dataset(DATASET_NAME)

    versions = get_prompt_versions()

    if prompt_version:
        if prompt_version not in versions:
            print(f"Error: Unknown prompt version '{prompt_version}'.")
            print(f"Available: {', '.join(versions.keys())}")
            sys.exit(1)
        versions = {prompt_version: versions[prompt_version]}

    print(f"\nRunning evaluations across {len(versions)} prompt version(s)...\n")

    results = {}

    for version_name, system_prompt in versions.items():
        print(f"{'='*60}")
        print(f"Evaluating prompt version: {version_name}")
        print(f"{'='*60}")

        run_fn = make_run_fn(system_prompt, model)
        experiment_prefix = f"call-analysis-{version_name}"

        experiment_metadata = {
            "models": [model],
            "prompts": [f"patient-call-analysis:{version_name}"],
            "tools": [
                {
                    "name": "transcribe_call",
                    "description": "Transcribe patient call audio and return transcript",
                },
                {
                    "name": "analyze_sentiment",
                    "description": "Analyze sentiment across call transcript segments",
                },
                {
                    "name": "extract_topics",
                    "description": "Extract and categorize topics from transcript",
                },
                {
                    "name": "detect_adverse_events",
                    "description": "Detect adverse events with confidence scores",
                },
                {
                    "name": "detect_technical_complaints",
                    "description": "Detect technical complaints with confidence scores",
                },
            ],
            "prompt_version": version_name,
        }

        experiment_results = evaluate(
            run_fn,
            data=DATASET_NAME,
            evaluators=ALL_EVALUATORS,
            experiment_prefix=experiment_prefix,
            description=f"Testing prompt version '{version_name}' for patient call analysis.",
            max_concurrency=1,
            metadata=experiment_metadata,
        )

        results[version_name] = experiment_results
        print(f"\nCompleted: {version_name}\n")

    print(f"\n{'='*60}")
    print("All evaluations complete!")
    print(f"{'='*60}")
    print(f"\nView results in LangSmith under the '{DATASET_NAME}' dataset.")
    print(f"Experiment prefixes: {', '.join(f'call-analysis-{v}' for v in versions)}")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run patient call analysis evaluations")
    parser.add_argument(
        "--prompt-version",
        type=str,
        default=None,
        help="Run only this prompt version (e.g., v1_detailed). Runs all if omitted.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="claude-sonnet-4-5-20250929",
        help="Model to use for the agent.",
    )
    args = parser.parse_args()

    run_evaluation(
        prompt_version=args.prompt_version,
        model=args.model,
    )
