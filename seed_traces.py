"""
Seed LangSmith with multiple agent traces for demo purposes.

Runs the agent N times concurrently with unique thread IDs,
creating independent traces in LangSmith.

Usage:
    python seed_traces.py             # Default 50 traces, 5 concurrent
    python seed_traces.py --count 20  # 20 traces
    python seed_traces.py --count 50 --concurrency 10
"""

import argparse
import os
import sys
import uuid
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agent"))

from dotenv import load_dotenv
load_dotenv(override=True)

from deep_agent import create_orchestrator

MESSAGES = [
    "Analyze the patient call. Use the demo transcript.",
    "Please analyze the demo patient call recording.",
    "Run a full analysis on the patient support call transcript.",
    "Analyze this call for adverse events, sentiment, and agent performance.",
    "Process the patient call and generate a comprehensive report.",
]


def run_single_trace(trace_num: int, total: int) -> tuple[int, bool, str]:
    """Run a single agent invocation. Returns (trace_num, success, detail)."""
    try:
        agent, _ = create_orchestrator()
        thread_id = f"seed-{uuid.uuid4()}"
        config = {"configurable": {"thread_id": thread_id}}
        message = MESSAGES[trace_num % len(MESSAGES)]

        start = time.time()
        result = agent.invoke(
            {"messages": [{"role": "user", "content": message}]},
            config=config,
        )
        elapsed = time.time() - start

        output = result["messages"][-1].content
        has_report = "Call Analysis Report" in output
        return (trace_num, True, f"done in {elapsed:.1f}s (report={'yes' if has_report else 'no'})")
    except Exception as e:
        return (trace_num, False, str(e)[:100])


def main():
    parser = argparse.ArgumentParser(description="Seed LangSmith with agent traces")
    parser.add_argument("--count", type=int, default=50, help="Number of traces to create")
    parser.add_argument("--concurrency", type=int, default=5, help="Max concurrent invocations")
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY required. Set it in .env")
        sys.exit(1)

    print(f"Seeding {args.count} traces with concurrency={args.concurrency}...\n")

    succeeded = 0
    failed = 0
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = {
            executor.submit(run_single_trace, i, args.count): i
            for i in range(args.count)
        }

        for future in as_completed(futures):
            trace_num, success, detail = future.result()
            status = "OK" if success else "FAIL"
            print(f"  [{trace_num + 1}/{args.count}] {status}: {detail}")
            if success:
                succeeded += 1
            else:
                failed += 1

    total_time = time.time() - start_time
    print(f"\nDone: {succeeded} succeeded, {failed} failed in {total_time:.0f}s")


if __name__ == "__main__":
    main()
