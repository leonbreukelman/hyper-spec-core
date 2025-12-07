# Hyper-Spec

> Integrated Spec-Driven Development Environment with AI Governance Integration

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

Hyper-Spec is an AI-powered development tool that enforces organizational governance policies during the software development lifecycle. It integrates with [hyper-governance-core](https://github.com/leonbreukelman/hyper-governance-core) to ensure AI agents are "steered" by live governance artifacts rather than static rules.

### The Artifact Handshake

Hyper-Spec implements a **Producer-Consumer** pattern:

1. **Producer** (`hyper-governance-core`): Compiles policy fragments into machine-readable artifacts via `codex weave`
2. **Consumer** (`hyper-spec-core`): Reads artifacts to build AI context and validates generated code

```
┌─────────────────────┐         ┌─────────────────────┐
│  Governance Core    │         │    Spec Core        │
│  ─────────────────  │         │  ─────────────────  │
│  codex weave        │──────▶  │  plan --spec        │
│  .codex/ artifacts  │         │  implement --plan   │
└─────────────────────┘         └─────────────────────┘
```

## Features

- **Live Governance Integration**: AI agents receive allowed/banned libraries, security controls, and architectural constraints
- **Governance Validation**: Code is validated against governance rules before completion
- **Interactive CLI**: Structured interviews for feature specification
- **Configurable**: Supports CLI flags, environment variables, and defaults
- **VS Code Integration**: Native tasks and settings (coming soon)

## Prerequisites

1. **uv** - Modern Python package manager
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **hyper-governance-core** - Clone as sibling directory and generate artifacts
   ```bash
   git clone https://github.com/leonbreukelman/hyper-governance-core.git
   cd hyper-governance-core
   uv sync && uv run codex weave
   ```

## Installation

```bash
git clone https://github.com/leonbreukelman/hyper-spec-core.git
cd hyper-spec-core
uv sync
```

For development:
```bash
uv sync --group dev
```

## Quick Start

```bash
# 1. Initialize project structure
uv run python hyper_spec.py init

# 2. Create a new feature spec
uv run python hyper_spec.py new --name my-feature

# 3. Generate governance-aware implementation plan
uv run python hyper_spec.py plan --spec specs/my-feature/spec.md

# 4. Implement with governance validation
uv run python hyper_spec.py implement --plan specs/my-feature/plan.md
```

## CLI Reference

### `init`
Bootstrap project directories (specs, templates, .vscode).

### `new --name <feature>`
Create a new feature spec via interactive interview.

### `plan --spec <path> [--governance-path <path>]`
Generate an implementation plan with governance context injected into the AI prompt.

### `implement --plan <path> [--skip-validation]`
Execute the plan and validate generated code against governance rules.

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `HYPER_GOVERNANCE_PATH` | Path to `.codex` governance artifacts | `../hyper-governance-core/.codex` |
| `HYPER_VALIDATOR_CMD` | Governance validation command | `codex validate --stack --ast` |

### Configuration Priority

1. CLI flag `--governance-path` (highest)
2. Environment variable `HYPER_GOVERNANCE_PATH`
3. Default path `../hyper-governance-core/.codex` (lowest)

## Development

```bash
# Run tests
uv run pytest tests/ -v

# Code quality
uv run ruff check .
uv run mypy adapter.py hyper_spec.py

# Governance validation
codex validate
```

## Project Status

**Current Version**: 2.0.0 (Prototype)

- ✅ Governance adapter with YAML and Markdown parsing
- ✅ CLI integration with `--governance-path` flag
- ✅ Subprocess validation via `codex validate`
- ✅ Graceful degradation for missing artifacts
- ⏳ Full LLM integration (currently simulated)
- ⏳ VS Code task integration

## License

MIT
