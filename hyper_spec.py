import os
import sys
import typer
import yaml
import json
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from jinja2 import Environment, FileSystemLoader
import openai
import instructor
from pydantic import BaseModel, Field

# Initialize Typer and Rich Console
app = typer.Typer(help="Hyper-Spec: Integrated Spec-Driven Development")
console = Console()

# Constants
SPECS_DIR = Path("specs")
TEMPLATES_DIR = SPECS_DIR / ".templates"
CONSTITUTION_DIR = SPECS_DIR / ".constitution"
VSCODE_DIR = Path(".vscode")

class FeatureSpec(BaseModel):
    feature_name: str
    author: str
    complexity: str
    intent: str
    user_stories: List[str]
    functional_requirements: List[str]
    anti_requirements: List[str]
    success_criteria: List[str]

class ImplementationPlan(BaseModel):
    summary: str
    file_changes: List[dict]
    logic_steps: List[str]
    verification_strategy: List[str]

@app.command()
def init(force: bool = typer.Option(False, "--force", "-f", help="Force re-initialization")):
    """
    Bootstraps the .vscode and specs directories. Checks for uv.
    """
    console.print(Panel("[bold blue]Hyper-Spec Initialization[/bold blue]"))

    # Check for uv
    if os.system("uv --version") != 0:
        console.print("[bold red]Error:[/bold red] 'uv' is not installed. Please install it first.")
        raise typer.Exit(code=1)
    console.print("[green]✓[/green] 'uv' detected.")

    # Create directories
    dirs = [SPECS_DIR, TEMPLATES_DIR, CONSTITUTION_DIR, VSCODE_DIR]
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
    interactive: bool = typer.Option(True, "--interactive/--no-interactive", help="Run interactive steering interview")
):
    """
    Creates a new feature branch and spec file. Runs the steering interview.
    """
    console.print(Panel(f"[bold blue]Creating New Feature Spec: {name}[/bold blue]"))

    feature_dir = SPECS_DIR / name
    if feature_dir.exists():
        console.print(f"[bold red]Error:[/bold red] Feature '{name}' already exists.")
        raise typer.Exit(code=1)

    feature_dir.mkdir()
    
    context = {}
    if interactive:
        console.print("[bold]Steering Interview[/bold]")
        context['feature_name'] = name
        context['author'] = Prompt.ask("Who is the owner of this feature?", default=os.getenv("USER", "developer"))
        context['complexity'] = Prompt.ask("Estimated Complexity Score (1-10)?", choices=[str(i) for i in range(1, 11)], default="3")
        
        # In a real implementation, we would ask more questions here to populate the spec
        # For now, we'll use the template
        
    # Load Template
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
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
    model: str = typer.Option("gpt-4-turbo", "--model", "-m", help="LLM model to use")
):
    """
    Reads the Spec + Constitution, generates a technical Plan.
    """
    console.print(Panel(f"[bold blue]Generating Implementation Plan for {spec_file}[/bold blue]"))

    if not spec_file.exists():
        console.print(f"[bold red]Error:[/bold red] File {spec_file} not found.")
        raise typer.Exit(code=1)

    # Read Spec
    spec_content = spec_file.read_text()

    # Read Constitution
    constitution = ""
    for rule_file in CONSTITUTION_DIR.glob("*.md"):
        constitution += f"\n--- {rule_file.name} ---\n" + rule_file.read_text()

    # Prepare Prompt (Simulation)
    system_prompt = f"""
    You are a Senior Architect. You must follow these Constitutional Rules:
    {constitution}
    
    Based on the following Feature Specification, generate an Implementation Plan.
    """
    
    user_prompt = f"Feature Spec:\n{spec_content}"

    console.print("[yellow]Thinking... (Simulating LLM call)[/yellow]")
    
    # In a real scenario, we would call OpenAI here.
    # client = instructor.patch(openai.OpenAI())
    # plan = client.chat.completions.create(...)
    
    # For this implementation, we will render the plan template with placeholders
    # or "mock" the AI response by parsing the spec slightly or just using defaults.
    
    feature_name = spec_file.parent.name
    
    context = {
        "feature_name": feature_name,
        "confidence_score": "95",
        "summary": f"Implementation plan for {feature_name} based on the provided spec.",
    }

    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
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
    auto_approve: bool = typer.Option(False, "--auto-approve", help="Skip confirmation")
):
    """
    Executes the Plan, generating code and running verification tasks.
    """
    console.print(Panel(f"[bold blue]Executing Implementation Plan: {plan_file}[/bold blue]"))

    if not plan_file.exists():
        console.print(f"[bold red]Error:[/bold red] File {plan_file} not found.")
        raise typer.Exit(code=1)

    plan_content = plan_file.read_text()
    
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
    
    console.print("[green]Running Verification...[/green]")
    # os.system("uv run pytest")
    
    console.print("[bold green]Implementation Complete![/bold green]")

if __name__ == "__main__":
    app()
