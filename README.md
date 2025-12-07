# Hyper-Spec

Integrated Spec-Driven Development Environment for VS Code.

## Features

- **Governance Integration**: AI agents are steered by live governance artifacts from `hyper-governance-core`.
- **Interactive CLI**: Structured interviews for feature specs.
- **VS Code Integration**: Native tasks and settings.
- **uv-Powered**: Fast, reliable Python environment.

## Prerequisites

1. **uv** - Install from [astral.sh/uv](https://astral.sh/uv)
2. **hyper-governance-core** - Install and run `codex weave` to generate governance artifacts

## Installation

### Via uv (recommended)

```bash
uv add hyper-spec-core
```

### Via pip

```bash
pip install hyper-spec-core
```

### Development Installation

```bash
git clone https://github.com/your-org/hyper-spec-core.git
cd hyper-spec-core
uv sync
```

## Usage

### Initialize Project

```bash
hyper-spec init
```

### Create New Feature

```bash
hyper-spec new --name my-feature
```

### Generate Implementation Plan

```bash
# Uses local .codex/ if available (run 'codex weave' first)
hyper-spec plan --spec specs/my-feature/spec.md

# Or specify a custom governance path
hyper-spec plan --spec specs/my-feature/spec.md \
    --governance-path /path/to/.codex
```

### Implement Feature

```bash
hyper-spec implement --plan specs/my-feature/plan.md
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `HYPER_GOVERNANCE_PATH` | Path to `.codex` governance artifacts | Local `.codex/` if exists |
| `HYPER_VALIDATOR_CMD` | Command to run governance validation | `codex validate --stack --ast` |

## Governance Path Resolution

The `--governance-path` is resolved in this priority order:

1. CLI flag `--governance-path` (highest priority)
2. `HYPER_GOVERNANCE_PATH` environment variable
3. Local `.codex/` directory in current working directory
4. Error if none found (explicit path required)

## Template Customization

To customize templates, create a `specs/.templates/` directory in your project with:

- `spec_template.md` - Feature specification template
- `plan_template.md` - Implementation plan template

These will override the bundled templates.
