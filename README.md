# Patient Call Analysis Agent

A patient support call analysis agent implemented with both LangChain Deep Agents and Strands Agents. Both implementations use the same three specialists and route Claude calls through the LangSmith LLM Gateway.

## Architecture

<img width="1926" height="1444" alt="image" src="https://github.com/user-attachments/assets/9c1385ec-10f7-4462-9e2a-f207d5c257b1" />


```
Orchestrator (Sonnet) ─── transcribe_call ──→ transcript
    │
    ├── sentiment_analysis (Haiku) ──→ JSON sentiment scores & trends
    ├── topic_and_ae_detection (Haiku) ──→ JSON topics, adverse events, technical complaints
    └── agent_performance (Haiku) ──→ JSON compliance scores against SOPs
```

**Guardrails:**
- **Hallucination & Internal Data Leakage Guard** (`middleware.py`) — scans LLM responses for internal company terms, redacts them, and writes an audit entry under the selected implementation's `output/` directory
- **Final Review** (`pii_review.py`, `final_review` tool) — a single-step LLM call that checks the draft report for required sections

**Skills** (loaded by agent_performance subagent):
- `sop-compliance-checklist` — 6-section call handling checklist with scoring guidelines
- `adverse-event-reporting-guidelines` — AE/TC identification, severity classification, compliance requirements

The Deep Agents implementation retains its existing audio attachment and LangSmith evaluation support. The Strands implementation exports its agent, event-loop, model, and tool spans to LangSmith through OpenTelemetry.

## Setup

```bash
# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# Add your LANGSMITH_API_KEY to .env
```

### Required environment variables

| Variable | Description |
|----------|-------------|
| `LANGSMITH_API_KEY` | Workspace-scoped key with LLM Gateway access |
| `LANGSMITH_GATEWAY` | Routes supported LangChain models through the Gateway |
| `LANGSMITH_GATEWAY_URL` | Direct Anthropic Gateway endpoint used by Strands |
| `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` | LangSmith OpenTelemetry ingestion endpoint |
| `OTEL_EXPORTER_OTLP_HEADERS` | LangSmith API key and destination project for Strands traces |

The LangSmith workspace must have an Anthropic provider secret configured and the API key must have Gateway invoke access.

Strands telemetry includes prompts, completions, and tool inputs and outputs. The configured `Langsmith-Project` receives application-level spans; Gateway model-call traces may also appear in the Gateway-managed tracing project.

### System dependencies (macOS)

```bash
brew install sox lame  # For audio generation
```

## Usage

### Run the agent

```bash
uv run python3 run_agent.py
uv run python3 run_agent.py --implementation strands
uv run python3 run_agent.py --audio path/to/call.mp3
```

### Run in LangGraph Studio

Open the Deep Agents implementation in LangGraph Studio — `langgraph.json` points to `agent/deepagents/graph.py`.

### Run evaluations

The current evaluation runner targets the Deep Agents implementation. Strands application tracing is enabled, but Strands evaluation support is not yet wired into this runner.

```bash
# Run all 4 prompt versions
uv run python3 evals/run_evals.py

# Run a specific prompt version
uv run python3 evals/run_evals.py --prompt-version v1_detailed

# Use a different model
uv run python3 evals/run_evals.py --model claude-sonnet-4-5-20250929
```

### Evals walkthrough notebook

`evals/evals_walkthrough.ipynb` is a step-by-step teaching version of the eval suite. It
breaks an eval into its pieces — dataset, target, evaluators, `evaluate()` — and builds each
of the 5 evaluators one at a time against a fast toy target, then compares the 4 Prompt Hub
prompt versions with a lightweight prompt-driven agent. Every experiment logs to LangSmith.

```bash
uv run jupyter notebook evals/evals_walkthrough.ipynb
```

Requires `LANGSMITH_API_KEY` and `ANTHROPIC_API_KEY` in `.env`. If you use a personal
access token, also set `LANGSMITH_WORKSPACE_ID` so the dataset and experiments land in the
right workspace.

## Evaluation Suite

Tests 4 system prompt versions (`v1_detailed`, `v2_minimal`, `v3_safety_focused`, `v4_structured`) with 5 evaluators:

| Evaluator | Type | What it checks |
|-----------|------|----------------|
| Trajectory | Code | Correct subagent delegation order |
| PII Leakage | Code | No patient PII in final report |
| Internal Leakage | Code | No internal company terms in report |
| Report Completeness | Code | All required sections present |
| Report Correctness | LLM-as-Judge | Content accuracy vs reference summary |

Results are tracked in LangSmith with experiment metadata for prompt version comparison.

## Project Structure

```
├── agent/
│   ├── deepagents/            # Deep Agents implementation and Studio graph
│   │   ├── subagents/
│   │   ├── tools/
│   │   └── skills/
│   └── strands/               # Strands Agents implementation
│       ├── strands_agent.py   # Orchestrator configuration
│       ├── model.py           # LangSmith Gateway model configuration
│       ├── subagents/
│       ├── tools/
│       └── skills/
├── evals/
│   ├── run_evals.py           # Evaluation runner
│   ├── evals_walkthrough.ipynb # Step-by-step evals teaching notebook
│   ├── evaluators.py          # 5 evaluators
│   ├── dataset.py             # LangSmith dataset with expected outputs
│   └── prompt_versions.py     # 4 prompt variants + Prompt Hub scaffolding
├── run_agent.py               # CLI entry point
├── langgraph.json             # LangGraph Studio config
└── pyproject.toml             # Dependencies
```
