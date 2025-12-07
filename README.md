# Hyper-Spec

Integrated Spec-Driven Development Environment for VS Code.

## Features

- **Governance Integration**: AI agents are steered by live governance artifacts from `hyper-governance-core`.
- **Interactive CLI**: Structured interviews for feature specs.
- **VS Code Integration**: Native tasks and settings.
- **uv-Powered**: Fast, reliable Python environment.

## Prerequisites

1. **uv** - Install from [astral.sh/uv](https://astral.sh/uv)
2. **hyper-governance-core** - Clone and run `codex weave` to generate governance artifacts

## Installation

```bash
git clone https://github.com/your-org/hyper-spec-core.git
cd hyper-spec-core
uv sync
```

## Usage

### Initialize Project

```bash
uv run hyper_spec.py init
```

### Create New Feature

```bash
uv run hyper_spec.py new --name my-feature
```

### Generate Implementation Plan

```bash
# Uses default governance path: ../hyper-governance-core/.codex
uv run hyper_spec.py plan --spec specs/my-feature/spec.md

# Or specify a custom governance path
uv run hyper_spec.py plan --spec specs/my-feature/spec.md \
    --governance-path /path/to/.codex
```

### Implement Feature

```bash
uv run hyper_spec.py implement --plan specs/my-feature/plan.md
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `HYPER_GOVERNANCE_PATH` | Path to `.codex` governance artifacts | `../hyper-governance-core/.codex` |
| `HYPER_VALIDATOR_CMD` | Command to run governance validation | `codex validate --stack --ast` |

## Configuration Priority

For `--governance-path`:
1. CLI flag (highest)
2. `HYPER_GOVERNANCE_PATH` environment variable
3. Default path (lowest)
