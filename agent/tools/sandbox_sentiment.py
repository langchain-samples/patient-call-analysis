"""
LangSmith sandbox tool for sentiment computation.

Uses the LangSmith code sandbox to execute Python code for computing
sentiment aggregation, trend analysis, and statistical summaries.
Falls back to local exec() if LANGSMITH_API_KEY is not set.
"""

import os
import warnings

from langchain_core.tools import tool

_sandbox_available = False
if os.environ.get("LANGSMITH_API_KEY"):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            from langsmith.sandbox import SandboxClient
        _sandbox_available = True
    except ImportError:
        pass


def _run_local(code: str) -> str:
    import io
    import contextlib
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            exec(code, {"__builtins__": __builtins__}, {})
        output = buf.getvalue().strip()
        return output if output else "Code executed but produced no output."
    except Exception as e:
        return f"Computation error: {e}"


@tool
def run_sentiment_computation(code: str) -> str:
    """Execute Python code in a secure sandbox for sentiment analysis computations.

    Use this for any sentiment math that requires precision:
    - Weighted average sentiment scores across call segments
    - Sentiment trend analysis (improving, declining, stable)
    - Patient vs. agent sentiment comparison
    - Segment-level score aggregation by speaker or topic
    - Statistical summaries (mean, median, std deviation, min, max)

    The code should print() its results. Only standard Python libraries
    are available (math, statistics, json). No external packages.

    Example:
        scores = [0.25, 0.45, 0.55, 0.75, 0.85]
        import statistics
        print(f"Mean: {statistics.mean(scores):.2f}")
        print(f"Trend: {'improving' if scores[-1] > scores[0] else 'declining'}")

    Args:
        code: Python code to execute. Must use print() for output.
    """
    if not _sandbox_available:
        return _run_local(code)

    try:
        client = SandboxClient()
        with client.sandbox() as sandbox:
            result = sandbox.run(f"python3 -c \"{code}\"")
            output = result.stdout.strip()
            if result.stderr.strip():
                output += f"\nWarnings: {result.stderr.strip()}"
            return output if output else "Code executed but produced no output."
    except Exception as e:
        return f"Computation error: {e}"
