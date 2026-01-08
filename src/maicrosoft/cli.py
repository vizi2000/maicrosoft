"""Maicrosoft CLI - Command line interface for primitives-first AI coding."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
import yaml

from maicrosoft.core.models import Plan, PlanMetadata, PlanSettings
from maicrosoft.registry.registry import PrimitiveRegistry
from maicrosoft.validation.validator import PlanValidator
from maicrosoft.compiler import N8NCompiler

app = typer.Typer(
    name="maicrosoft",
    help="Framework for Hallucination-Free AI Coding",
    add_completion=False,
)

console = Console()


def get_registry() -> PrimitiveRegistry:
    """Get the primitive registry."""
    return PrimitiveRegistry()


@app.command()
def init(
    name: str = typer.Argument(..., help="Project name"),
    path: Optional[Path] = typer.Option(None, help="Project path"),
) -> None:
    """Initialize a new Maicrosoft project."""
    project_path = path or Path.cwd() / name

    if project_path.exists():
        console.print(f"[red]Error:[/red] Directory already exists: {project_path}")
        raise typer.Exit(1)

    project_path.mkdir(parents=True)
    (project_path / "primitives").mkdir()
    (project_path / "plans").mkdir()
    (project_path / "compiled").mkdir()

    config = {
        "project": {
            "name": name,
            "version": "1.0.0",
        },
        "settings": {
            "allow_fallback": False,
            "default_target": "n8n",
        },
    }

    with open(project_path / "maicrosoft.yaml", "w") as f:
        yaml.dump(config, f, default_flow_style=False)

    console.print(f"[green]Created project:[/green] {project_path}")
    console.print("\nNext steps:")
    console.print(f"  cd {name}")
    console.print("  maicrosoft particles list")
    console.print('  maicrosoft compose "your workflow description"')


@app.command()
def validate(
    plan_file: Path = typer.Argument(..., help="Path to plan YAML file"),
) -> None:
    """Validate a plan against the primitives registry."""
    if not plan_file.exists():
        console.print(f"[red]Error:[/red] File not found: {plan_file}")
        raise typer.Exit(1)

    with open(plan_file) as f:
        plan_data = yaml.safe_load(f)

    try:
        plan = Plan(**plan_data)
    except Exception as e:
        console.print(f"[red]Error parsing plan:[/red] {e}")
        raise typer.Exit(1)

    validator = PlanValidator()
    result = validator.validate(plan)

    if result.valid:
        console.print(Panel("[green]Plan is valid[/green]", title="Validation Result"))
    else:
        console.print(Panel("[red]Plan has errors[/red]", title="Validation Result"))

    if result.violations:
        table = Table(title="Violations")
        table.add_column("Level", style="red")
        table.add_column("Code")
        table.add_column("Message")
        table.add_column("Node")

        for v in result.violations:
            table.add_row(v.level, v.code, v.message, v.node_id or "-")

        console.print(table)

    if result.warnings:
        table = Table(title="Warnings")
        table.add_column("Level", style="yellow")
        table.add_column("Code")
        table.add_column("Message")

        for w in result.warnings:
            table.add_row(w.level, w.code, w.message)

        console.print(table)

    if not result.valid:
        raise typer.Exit(1)


@app.command("particles")
def list_particles(
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show details"),
) -> None:
    """List available particles."""
    registry = get_registry()
    particles = registry.list(primitive_type="particle", category=category)

    table = Table(title="Available Particles")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Category")
    table.add_column("Description")

    for p in particles:
        table.add_row(
            p["id"],
            p["name"],
            p.get("category", "-"),
            p.get("description", "-")[:50] + "..." if len(p.get("description", "")) > 50 else p.get("description", "-"),
        )

    console.print(table)
    console.print(f"\n[dim]Total: {len(particles)} particles[/dim]")


@app.command("particle")
def show_particle(
    primitive_id: str = typer.Argument(..., help="Particle ID (e.g., P001)"),
) -> None:
    """Show details of a specific particle."""
    registry = get_registry()

    try:
        primitive = registry.get(primitive_id)
    except FileNotFoundError:
        console.print(f"[red]Error:[/red] Particle not found: {primitive_id}")
        raise typer.Exit(1)

    console.print(Panel(
        f"[bold]{primitive.metadata.name}[/bold]\n\n{primitive.metadata.description}",
        title=f"Particle {primitive_id}",
    ))

    if primitive.interface.inputs:
        table = Table(title="Inputs")
        table.add_column("Name", style="cyan")
        table.add_column("Type")
        table.add_column("Required")
        table.add_column("Description")

        for inp in primitive.interface.inputs:
            table.add_row(
                inp.name,
                inp.type.value,
                "Yes" if inp.required else "No",
                inp.description or "-",
            )

        console.print(table)

    if primitive.interface.outputs:
        table = Table(title="Outputs")
        table.add_column("Name", style="green")
        table.add_column("Type")
        table.add_column("Description")

        for out in primitive.interface.outputs:
            table.add_row(out.name, out.type.value, out.description or "-")

        console.print(table)


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
) -> None:
    """Search for particles by name or description."""
    registry = get_registry()
    results = registry.search_by_name(query)

    if not results:
        console.print(f"[yellow]No particles found matching:[/yellow] {query}")
        return

    table = Table(title=f"Search Results for '{query}'")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Description")

    for r in results:
        table.add_row(r["id"], r["name"], r.get("description", "-")[:60])

    console.print(table)


@app.command()
def compile(
    plan_file: Path = typer.Argument(..., help="Path to plan YAML file"),
    target: str = typer.Option("n8n", "--target", "-t", help="Compilation target"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
) -> None:
    """Compile a plan to a target format (n8n, python, temporal)."""
    if not plan_file.exists():
        console.print(f"[red]Error:[/red] File not found: {plan_file}")
        raise typer.Exit(1)

    with open(plan_file) as f:
        plan_data = yaml.safe_load(f)

    try:
        plan = Plan(**plan_data)
    except Exception as e:
        console.print(f"[red]Error parsing plan:[/red] {e}")
        raise typer.Exit(1)

    validator = PlanValidator()
    result = validator.validate(plan)

    if not result.valid:
        console.print("[red]Error:[/red] Plan validation failed. Run 'maicrosoft validate' for details.")
        raise typer.Exit(1)

    # Compile to target
    import json

    if target == "n8n":
        registry = get_registry()
        compiler = N8NCompiler(registry)
        workflow = compiler.compile(plan)

        output_path = output or plan_file.with_suffix(".n8n.json")
        with open(output_path, "w") as f:
            json.dump(workflow, f, indent=2)

        console.print(f"[green]Compiled to:[/green] {output_path}")
    else:
        console.print(f"[yellow]Note:[/yellow] Compilation to '{target}' not yet implemented.")
        console.print("Supported targets: n8n")


@app.command()
def gaps() -> None:
    """Show primitives that have been requested but don't exist."""
    console.print("[yellow]Note:[/yellow] Gap tracking not yet implemented.")
    console.print("This feature will track missing primitives from failed validations.")


@app.command()
def serve(
    port: int = typer.Option(8080, "--port", "-p", help="Server port"),
    primitives: Path = typer.Option(Path("primitives"), "--primitives", help="Primitives directory"),
) -> None:
    """Start the MCP server for AI agent integration."""
    import asyncio

    try:
        from maicrosoft.mcp import create_server
    except ImportError:
        console.print("[red]Error:[/red] MCP dependencies not installed.")
        console.print("Install with: pip install maicrosoft[mcp]")
        raise typer.Exit(1)

    console.print(f"[green]Starting MCP server...[/green]")
    console.print(f"  Primitives: {primitives}")
    console.print(f"  Port: {port}")
    console.print("\n[dim]Press Ctrl+C to stop[/dim]\n")

    server = create_server(str(primitives))
    asyncio.run(server.run())


@app.command()
def compose(
    description: str = typer.Argument(..., help="Natural language description of the workflow"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file for the plan"),
    model: str = typer.Option("claude-sonnet-4-20250514", "--model", "-m", help="LLM model to use"),
) -> None:
    """Compose a plan from natural language description using AI."""
    from maicrosoft.llm import LLMOrchestrator

    console.print(f"[cyan]Composing plan for:[/cyan] {description}\n")

    orchestrator = LLMOrchestrator(model=model)

    with console.status("[bold green]Generating plan..."):
        result = orchestrator.compose_sync(description)

    if result.success and result.plan:
        console.print(Panel("[green]Plan composed successfully[/green]", title="Result"))

        if result.gaps:
            console.print("\n[yellow]Detected gaps (missing primitives):[/yellow]")
            for gap in result.gaps:
                console.print(f"  - {gap}")

        # Save plan
        if result.plan_yaml:
            output_path = output or Path(f"plan-{result.plan.metadata.id}.yaml")
            with open(output_path, "w") as f:
                f.write(result.plan_yaml)
            console.print(f"\n[green]Plan saved to:[/green] {output_path}")

        # Show plan summary
        console.print(f"\n[bold]Plan:[/bold] {result.plan.metadata.name}")
        console.print(f"[dim]Nodes: {len(result.plan.nodes)}[/dim]")

    else:
        console.print(Panel("[red]Plan composition failed[/red]", title="Result"))

        if result.validation_errors:
            console.print("\n[red]Validation errors:[/red]")
            for error in result.validation_errors:
                console.print(f"  - {error}")

        if result.suggestions:
            console.print("\n[yellow]Suggestions:[/yellow]")
            for suggestion in result.suggestions:
                console.print(f"  - {suggestion}")

        raise typer.Exit(1)


@app.command()
def suggest(
    description: str = typer.Argument(..., help="Description of what you want to do"),
) -> None:
    """Suggest primitives for a given task description."""
    from maicrosoft.llm import LLMOrchestrator

    orchestrator = LLMOrchestrator()
    results = orchestrator.suggest_primitives(description)

    if not results:
        console.print(f"[yellow]No primitives found for:[/yellow] {description}")
        return

    table = Table(title=f"Suggested Primitives for '{description}'")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Score", justify="right")
    table.add_column("Description")

    for r in results:
        table.add_row(
            r["id"],
            r["name"],
            str(r["score"]),
            r["description"][:50] + "..." if len(r["description"]) > 50 else r["description"],
        )

    console.print(table)


@app.command()
def version() -> None:
    """Show version information."""
    from maicrosoft import __version__

    console.print(f"Maicrosoft v{__version__}")
    console.print("Framework for Hallucination-Free AI Coding")
    console.print("Created by The Collective BORG.tools")


def main() -> None:
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
