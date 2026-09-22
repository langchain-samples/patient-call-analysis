"""LangSmith telemetry setup for the Strands implementation."""

from langsmith.integrations.strands_agents import setup_langsmith_telemetry

_telemetry_configured = False


def setup_telemetry() -> None:
    """Configure the LangSmith Strands exporter once per process."""
    global _telemetry_configured
    if _telemetry_configured:
        return

    setup_langsmith_telemetry()
    _telemetry_configured = True
