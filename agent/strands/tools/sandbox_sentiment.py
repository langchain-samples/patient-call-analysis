"""LangSmith sandbox tool for sentiment computation.

This mirrors the Deep Agents helper and remains unused by the configured
sentiment subagent.
"""

import os
import warnings

from strands import tool

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
    import contextlib
    import io

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
    """Execute Python code for sentiment analysis computations."""
    if not _sandbox_available:
        return _run_local(code)

    try:
        client = SandboxClient()
        with client.sandbox() as sandbox:
            result = sandbox.run(f'python3 -c "{code}"')
            output = result.stdout.strip()
            if result.stderr.strip():
                output += f"\nWarnings: {result.stderr.strip()}"
            return output if output else "Code executed but produced no output."
    except Exception as e:
        return f"Computation error: {e}"
