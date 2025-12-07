"""Hyper-Spec CLI: Integrated Spec-Driven Development Environment."""

import json
import os
import shlex
import subprocess
from pathlib import Path
from typing import Optional

import typer
from jinja2 import Environment, PackageLoader, FileSystemLoader
from pydantic import BaseModel
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from hyper_spec_core.adapter import GovernanceAdapter

# Initialize Typer and Rich Console
app = typer.Typer(help="Hyper-Spec: Integrated Spec-Driven Development")
console = Console()

# Constants
SPECS_DIR = Path("specs")
TEMPLATES_DIR = SPECS_DIR / ".templates"
VSCODE_DIR = Path(".vscode")
DEFAULT_VALIDATOR_CMD = "codex validate --stack --ast"


def resolve_gov_path(cli_path: Optional[Path]) -> Path:
    """Resolve governance path with priority: CLI > Env > Local .codex.

    Args:
        cli_path: Path provided via CLI flag, or None.

    Returns:
        Resolved path to the .codex governance directory.

    Raises:
        ValueError: If no governance path can be resolved.
    """
    if cli_path is not None:
        return cli_path

    env_path = os.getenv("HYPER_GOVERNANCE_PATH")
    if env_path:
        return Path(env_path)

    # Try .codex/ in current directory as sensible default
    local_codex = Path(".codex")
    if local_codex.exists():
        return local_codex

    raise ValueError(
        "Governance path not found. Either:\n"
        "  - Run 'codex weave' to generate .codex/ locally\n"
        "  - Set HYPER_GOVERNANCE_PATH environment variable\n"
        "  - Use --governance-path CLI flag"
    )


def get_template_env() -> Environment:
    """Get Jinja2 Environment with template loader.

    Priority: local specs/.templates/ > bundled package templates.

    Returns:
        Configured Jinja2 Environment.
    """
    # Priority: local .templates/ for customization (only if it contains template files)
    if TEMPLATES_DIR.exists() and any(TEMPLATES_DIR.glob("*.md")):
        return Environment(loader=FileSystemLoader(TEMPLATES_DIR))

    # Fall back to bundled templates from package
    return Environment(loader=PackageLoader("hyper_spec_core", "templates"))


class FeatureSpec(BaseModel):
    """Pydantic model for feature specifications."""

    feature_name: str
    author: str
    complexity: str
    intent: str
    user_stories: list[str]
    functional_requirements: list[str]
    anti_requirements: list[str]
    success_criteria: list[str]


class ImplementationPlan(BaseModel):
    """Pydantic model for implementation plans."""

    summary: str
    file_changes: list[dict]
    logic_steps: list[str]
    verification_strategy: list[str]


@app.command()
def init(
    force: bool = typer.Option(False, "--force", "-f", help="Force re-initialization"),
) -> None:
    """Bootstrap the .vscode and specs directories. Checks for uv."""
    console.print(Panel("[bold blue]Hyper-Spec Initialization[/bold blue]"))

    # Check for uv using subprocess (governance-compliant)
    result = subprocess.run(
        ["uv", "--version"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        console.print(
            "[bold red]Error:[/bold red] 'uv' is not installed. Please install it first."
        )
        raise typer.Exit(code=1)
    console.print("[green]✓[/green] 'uv' detected.")

    # Create directories
    dirs = [SPECS_DIR, TEMPLATES_DIR, VSCODE_DIR]
    for d in dirs:
        if not d.exists():
            d.mkdir(parents=True)
            console.print(f"[green]✓[/green] Created {d}")
        else:
            console.print(f"[yellow]![/yellow] {d} already exists.")

    console.print("[bold green]Initialization Complete![/bold green]")


@app.command()
def new(
    name: str = typer.Option(..., "--name", "-n", help="Name of the feature"),
    interactive: bool = typer.Option(
        True, "--interactive/--no-interactive", help="Run interactive steering interview"
    ),
) -> None:
    """Create a new feature branch and spec file. Runs the steering interview."""
    console.print(Panel(f"[bold blue]Creating New Feature Spec: {name}[/bold blue]"))

    feature_dir = SPECS_DIR / name
    if feature_dir.exists():
        console.print(f"[bold red]Error:[/bold red] Feature '{name}' already exists.")
        raise typer.Exit(code=1)

    feature_dir.mkdir()

    context: dict[str, str] = {}
    if interactive:
        console.print("[bold]Steering Interview[/bold]")
        context["feature_name"] = name
        context["author"] = Prompt.ask(
            "Who is the owner of this feature?", default=os.getenv("USER", "developer")
        )
        context["complexity"] = Prompt.ask(
            "Estimated Complexity Score (1-10)?",
            choices=[str(i) for i in range(1, 11)],
            default="3",
        )

    # Load Template
    env = get_template_env()
    try:
        template = env.get_template("spec_template.md")
        content = template.render(**context)
    except Exception as e:
        console.print(f"[bold red]Error loading template:[/bold red] {e}")
        # Fallback if template doesn't exist yet (during bootstrapping)
        content = f"# Feature Specification: {name}\n\nTODO: Fill this out."

    spec_file = feature_dir / "spec.md"
    spec_file.write_text(content)
    console.print(f"[green]✓[/green] Created {spec_file}")

    # Create context.json for checksums (placeholder)
    context_file = feature_dir / "context.json"
    context_file.write_text(json.dumps({"spec_checksum": "TODO"}, indent=2))

    console.print(f"[bold green]Feature '{name}' initialized![/bold green]")
    console.print(f"Open {spec_file} to define your requirements.")


@app.command()
def plan(
    spec_file: Path = typer.Option(..., "--spec", "-s", help="Path to the spec file"),
    model: str = typer.Option("gpt-4-turbo", "--model", "-m", help="LLM model to use"),
    governance_path: Optional[Path] = typer.Option(
        None,
        "--governance-path",
        "-g",
        help="Path to .codex governance artifacts",
    ),
) -> None:
    """Read the Spec + Governance artifacts, generate a technical Plan."""
    console.print(
        Panel(f"[bold blue]Generating Implementation Plan for {spec_file}[/bold blue]")
    )

    if not spec_file.exists():
        console.print(f"[bold red]Error:[/bold red] File {spec_file} not found.")
        raise typer.Exit(code=1)

    # Read Spec
    spec_content = spec_file.read_text()

    # Load Governance Context (The Artifact Handshake)
    try:
        gov_path = resolve_gov_path(governance_path)
        console.print(f"[cyan]Loading governance context from {gov_path}...[/cyan]")
        adapter = GovernanceAdapter(gov_path)
        gov_context = adapter.load_context()
        governance_prompt = gov_context.to_system_prompt()
        console.print("[green]✓[/green] Governance context loaded.")
    except ValueError as e:
        console.print(f"[bold yellow]Warning:[/bold yellow] {e}")
        console.print("[yellow]Proceeding without governance constraints.[/yellow]")
        governance_prompt = "No governance constraints available."
    except FileNotFoundError as e:
        console.print(f"[bold yellow]Warning:[/bold yellow] {e}")
        console.print("[yellow]Proceeding without governance constraints.[/yellow]")
        governance_prompt = "No governance constraints available."

    # Prepare Prompt with Governance Context
    _system_prompt = f"""
You are a Senior Architect. You must adhere to the following Live Governance Rules.
Any plan that violates these rules will be rejected.

{governance_prompt}

Based on the following Feature Specification, generate an Implementation Plan.
"""

    _user_prompt = f"Feature Spec:\n{spec_content}"

    console.print("[yellow]Thinking... (Simulating LLM call)[/yellow]")

    # In a real scenario, we would call OpenAI here.
    # client = instructor.patch(openai.OpenAI())
    # plan = client.chat.completions.create(...)

    # For this implementation, render the plan template with placeholders
    feature_name = spec_file.parent.name

    context = {
        "feature_name": feature_name,
        "confidence_score": "95",
        "summary": f"Implementation plan for {feature_name} based on the provided spec.",
    }

    env = get_template_env()
    try:
        template = env.get_template("plan_template.md")
        plan_content = template.render(**context)
    except Exception as e:
        console.print(f"[bold red]Error loading template:[/bold red] {e}")
        plan_content = "# Implementation Plan\n\nError generating plan."

    plan_file = spec_file.parent / "plan.md"
    plan_file.write_text(plan_content)

    console.print(f"[green]✓[/green] Generated {plan_file}")
    console.print("[bold green]Plan Generation Complete![/bold green]")


@app.command()
def implement(
    plan_file: Path = typer.Option(..., "--plan", "-p", help="Path to the plan file"),
    auto_approve: bool = typer.Option(False, "--auto-approve", help="Skip confirmation"),
    skip_validation: bool = typer.Option(
        False, "--skip-validation", help="Skip governance validation"
    ),
) -> None:
    """Execute the Plan, generate code and run governance validation."""
    console.print(
        Panel(f"[bold blue]Executing Implementation Plan: {plan_file}[/bold blue]")
    )

    if not plan_file.exists():
        console.print(f"[bold red]Error:[/bold red] File {plan_file} not found.")
        raise typer.Exit(code=1)

    _plan_content = plan_file.read_text()  # noqa: F841

    # Parse Plan (Simple parsing for this demo)
    # In reality, we'd use the structured output from the 'plan' step or parse the markdown.

    console.print("[bold]Proposed Actions:[/bold]")
    console.print("1. Create src/domain/models/user.py (Simulated)")
    console.print("2. Modify src/api/routes.py (Simulated)")

    if not auto_approve:
        if not Confirm.ask("Do you want to proceed with these changes?"):
            console.print("[yellow]Aborted.[/yellow]")
            raise typer.Exit()

    console.print("[green]Executing changes...[/green]")
    # Here we would actually write the files.
    # For the demo, we'll just simulate success.

    # Run Governance Validation (The Artifact Handshake - Enforcement)
    if not skip_validation:
        _run_governance_validation()

    console.print("[bold green]Implementation Complete![/bold green]")


def _run_governance_validation() -> bool:
    """Run the governance validator and report results.

    Returns:
        True if validation passed, False otherwise.
    """
    cmd_str = os.getenv("HYPER_VALIDATOR_CMD", DEFAULT_VALIDATOR_CMD)
    cmd_args = shlex.split(cmd_str)

    console.print(f"[cyan]Running Governance Validation: {cmd_str}[/cyan]")

    try:
        result = subprocess.run(
            cmd_args,
            cwd=os.getcwd(),
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            console.print("[bold red]Governance Violation Detected:[/bold red]")
            if result.stdout:
                console.print(result.stdout)
            if result.stderr:
                console.print(result.stderr, style="dim")
            return False
        else:
            console.print("[bold green]✓ Governance Verified[/bold green]")
            return True

    except FileNotFoundError:
        console.print(
            "[bold yellow]Warning:[/bold yellow] Validator command not found. "
            "Set HYPER_VALIDATOR_CMD or ensure 'codex' is on PATH."
        )
        return False


if __name__ == "__main__":
    app()
