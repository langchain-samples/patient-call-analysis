# Patient Call Analysis Agent

A LangChain Deep Agent that analyzes pharmaceutical patient support calls using three specialized subagents, with LangSmith tracing, audio file attachments, and an offline evaluation suite.

## Architecture

<img width="1926" height="1444" alt="image" src="https://github.com/user-attachments/assets/9c1385ec-10f7-4462-9e2a-f207d5c257b1" />


```
Orchestrator (Sonnet) ─── transcribe_call ──→ audio attachment + transcript
    │
    ├── sentiment_analysis (Haiku) ──→ JSON sentiment scores & trends
    ├── topic_and_ae_detection (Haiku) ──→ JSON topics, adverse events, technical complaints
    └── agent_performance (Haiku) ──→ JSON compliance scores against SOPs
```

**Guardrails:**
- **Hallucination & Internal Data Leakage Guard** (`middleware.py`, `wrap_model_call`) — scans LLM responses for hallucinated patient data and internal company terms, redacts them, and writes an entry to `agent/output/audit_log.json`
- **Final Review** (`pii_review.py`, `final_review` tool) — a single-step traced LLM call that checks the draft report for required sections; runs as its own LangSmith span so the prompt can be iterated in Playground

**Skills** (loaded by agent_performance subagent):
- `sop-compliance-checklist` — 6-section call handling checklist with scoring guidelines
- `adverse-event-reporting-guidelines` — AE/TC identification, severity classification, compliance requirements

**Audio:** Generates a multi-voice MP3 recording from the transcript using macOS TTS (`say` + `sox` + `lame`), attached to the LangSmith trace via `@traceable` with `Attachment`.

## Setup

```bash
# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# Add your ANTHROPIC_API_KEY and LANGSMITH_API_KEY to .env
```

### Required environment variables

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude models |
| `LANGSMITH_API_KEY` | LangSmith API key for tracing and evals |

### System dependencies (macOS)

```bash
brew install sox lame  # For audio generation
```

## Usage

### Run the agent

```bash
uv run python3 run_agent.py
uv run python3 run_agent.py --audio path/to/call.mp3
```

### Run in LangGraph Studio

Open the project in LangGraph Studio — it reads `langgraph.json` which points to `agent/graph.py`.

### Run evaluations

```bash
# Run all 4 prompt versions
uv run python3 evals/run_evals.py

# Run a specific prompt version
uv run python3 evals/run_evals.py --prompt-version v1_detailed

# Use a different model
uv run python3 evals/run_evals.py --model claude-sonnet-4-5-20250929
```

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
│   ├── graph.py              # LangGraph Studio entry point
│   ├── deep_agent.py         # Orchestrator configuration
│   ├── prompts.py            # System prompt
│   ├── mock_data.py          # Mock transcript and analysis data
│   ├── middleware.py          # Hallucination + internal leakage guard
│   ├── pii_review.py          # final_review tool (traced report review)
│   ├── subagents/
│   │   ├── sentiment.py       # Sentiment analysis subagent
│   │   ├── topic_and_ae.py    # Topic + AE/TC detection subagent
│   │   └── agent_performance.py  # SOP compliance review subagent
│   ├── tools/
│   │   ├── transcript_tools.py   # Audio generation + LangSmith attachment
│   │   ├── analysis_tools.py     # Mock analysis tools
│   │   └── sandbox_sentiment.py  # LangSmith sandbox tool
│   └── skills/
│       ├── sop-compliance-checklist/SKILL.md
│       └── adverse-event-reporting-guidelines/SKILL.md
├── evals/
│   ├── run_evals.py           # Evaluation runner
│   ├── evaluators.py          # 5 evaluators
│   ├── dataset.py             # LangSmith dataset with expected outputs
│   └── prompt_versions.py     # 4 prompt variants + Prompt Hub scaffolding
├── run_agent.py               # CLI entry point
├── langgraph.json             # LangGraph Studio config
└── pyproject.toml             # Dependencies
```
