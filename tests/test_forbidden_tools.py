"""Regression tests for the orchestrator forbidden-tool guard.

Two layers of defense are validated here:

1. The compiled orchestrator graph must not expose deepagents' built-in
   filesystem tools (`write_todos`, `write_file`, `read_file`, `edit_file`,
   `ls`) — they are disabled by passing `backend=None` to `create_deep_agent`.

2. If a future refactor re-exposes any of those tools, the
   ``ForbiddenToolGuard`` middleware short-circuits the call with a
   ``ToolMessage`` error rather than executing it.

The first test uses the standard demo transcript flow (no audio file) but
only inspects the compiled graph's nodes/tools — it does not require an
Anthropic API key — so it runs deterministically in CI.
"""

import os
import sys

import pytest
from langchain_core.messages import ToolMessage

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agent"))


FORBIDDEN = {"write_todos", "write_file", "read_file", "edit_file", "ls"}


def _collect_tool_names(graph) -> set[str]:
    """Best-effort enumeration of tool names reachable from a compiled graph."""
    names: set[str] = set()

    # Compiled graphs expose `.nodes` mapping; tool nodes hold a `.tools_by_name`.
    nodes = getattr(graph, "nodes", {}) or {}
    for node in nodes.values():
        runnable = getattr(node, "runnable", node)
        tools_by_name = getattr(runnable, "tools_by_name", None)
        if isinstance(tools_by_name, dict):
            names.update(tools_by_name.keys())
        tools = getattr(runnable, "tools", None)
        if tools:
            for t in tools:
                tool_name = getattr(t, "name", None)
                if tool_name:
                    names.add(tool_name)

    return names


def test_orchestrator_does_not_expose_builtin_fs_tools():
    """The compiled orchestrator graph must not advertise forbidden fs tools."""
    pytest.importorskip("deepagents", reason="deepagents not installed")
    from deep_agent import create_orchestrator

    agent, _ = create_orchestrator()
    tool_names = _collect_tool_names(agent)
    leaked = FORBIDDEN & tool_names
    assert not leaked, (
        f"Orchestrator should not expose deepagents built-in fs tools, "
        f"but found: {sorted(leaked)}"
    )


@pytest.mark.parametrize("tool_name", sorted(FORBIDDEN))
def test_forbidden_tool_guard_blocks_each_tool(tool_name):
    """ForbiddenToolGuard returns an error ToolMessage instead of invoking the handler."""
    from middleware import ForbiddenToolGuard

    guard = ForbiddenToolGuard()

    class _Req:
        tool_call = {"name": tool_name, "id": "call-123", "args": {}}

    def _handler(_request):  # pragma: no cover - must not be called
        raise AssertionError(f"handler should not run for forbidden tool {tool_name}")

    result = guard.wrap_tool_call(_Req(), _handler)
    assert isinstance(result, ToolMessage)
    assert result.tool_call_id == "call-123"
    assert tool_name in result.content
    assert "not allowed" in result.content


def test_forbidden_tool_guard_passes_through_allowed_tools():
    """Allowed tool calls (e.g. `transcribe_call`) must reach the handler unchanged."""
    from middleware import ForbiddenToolGuard

    guard = ForbiddenToolGuard()

    class _Req:
        tool_call = {"name": "transcribe_call", "id": "call-xyz", "args": {}}

    sentinel = ToolMessage(content="ok", tool_call_id="call-xyz")
    result = guard.wrap_tool_call(_Req(), lambda _r: sentinel)
    assert result is sentinel
