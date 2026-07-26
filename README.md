# LabOS Operations Copilot

AI-assisted laboratory operations workflow that identifies experiments requiring attention, explains why, and recommends next actions using typed data services, deterministic rules, MCP tools, and an evidence-grounded LLM agent.

Uses simulated data only. No real laboratory systems or actions are connected.

## Features

- Typed experiment, inventory, instrument, and deadline models
- Validated JSON fixtures and read-only Python SDK
- Deterministic blocker detection
- MCP-compatible tools
- Evidence-grounded operations brief
- Approval-gated mock actions
- Structured traces, evaluations, and Streamlit UI

## Architecture

Streamlit UI → Application Service → LLM Agent → MCP Tools
     → Typed LabOS SDK → Experiments / Inventory / Instruments / Deadlines
     → Deterministic Blocker Engine → Findings / Approval / Mock Actions

The LLM handles intent, tool selection, and summarization. Python rules handle blocker detection, severity, validation, and policy.

### Blocker Rules

- Stage duration exceeds its expected limit
- Required material is unavailable or below minimum quantity
- Required instrument is unavailable
- Customer deadline is at risk
- Multiple blockers affect the same experiment

## Tech Stack

Python 3.12, Pydantic, Pytest, Ruff, MyPy, MCP Python SDK/FastMCP, Streamlit, Docker.

## Installation

```bash 
git clone <REPOSITORY_URL>
cd labos-operations-copilot
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

## Usage

```bash
from pathlib import Path
from labos_copilot.sdk import LabOSClient

client = LabOSClient.from_fixture_directory(Path("fixtures"))

for experiment in client.experiments.list_active():
    print(experiment.id, experiment.current_stage)

streamlit run app.py
python -m labos_copilot.mcp.server
``` 

## Testing

```bash 

python -m ruff format --check .
python -m ruff check .
python -m mypy src tests
python -m pytest

```

## Safety

Read-only operations may run automatically. Mock side effects require explicit approval. The prototype does not submit experiments, control instruments, trigger procurement, send customer communications, or modify production data.