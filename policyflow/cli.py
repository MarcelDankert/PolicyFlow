from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from policyflow.exceptions import WorkflowValidationError
from policyflow.validator import validate_workflow_file


app = typer.Typer(help="PolicyFlow governance validator.")
console = Console()


@app.callback()
def main() -> None:
    """PolicyFlow governance validator commands."""


@app.command()
def validate(workflow_path: Path) -> None:
    """Validate a workflow file against lightweight governance rules."""

    try:
        validate_workflow_file(workflow_path)
    except WorkflowValidationError as exc:
        console.print("[red][ERROR][/red] Workflow validation failed.")
        for error in exc.errors:
            console.print(f"  - {error}")
        raise typer.Exit(code=1) from exc

    console.print("[green][SUCCESS][/green] Workflow validation passed.")


if __name__ == "__main__":
    app()
