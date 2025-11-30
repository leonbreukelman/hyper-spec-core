# Hyper-Spec

Integrated Spec-Driven Development Environment for VS Code.

## Features
- **Constitutional Steering**: Enforce architectural rules via AI.
- **Interactive CLI**: Structured interviews for feature specs.
- **VS Code Integration**: Native tasks and settings.
- **uv-Powered**: Fast, reliable Python environment.

## Usage
1. Initialize: `uv run hyper_spec.py init`
2. New Feature: `uv run hyper_spec.py new --name my-feature`
3. Plan: `uv run hyper_spec.py plan --spec specs/my-feature/spec.md`
4. Implement: `uv run hyper_spec.py implement --plan specs/my-feature/plan.md`
