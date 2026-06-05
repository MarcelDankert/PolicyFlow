from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console

from policyflow.agent_execution import run_phase_with_runner
from policyflow.bootstrap import bootstrap_consumer_repo
from policyflow.consumer_config import load_consumer_config
from policyflow.doctor import doctor_consumer_repo
from policyflow.exceptions import WorkflowValidationError
from policyflow.github_approval import validate_github_pr_approvals
from policyflow.runtime import (
    block_phase as block_workflow_phase,
    complete_phase as complete_workflow_phase,
    handoff_status_summary,
    next_step_summary,
    record_handoff as record_workflow_handoff,
    start_phase as start_workflow_phase,
)
from policyflow.reporting import audit_directory, audit_lines, status_lines, workflow_status
from policyflow.validator import (
    inspect_workflow_file,
    validate_pull_request,
)


app = typer.Typer(help="PolicyFlow governance validator.")
console = Console()


@app.callback()
def main() -> None:
    """PolicyFlow governance validator commands."""


@app.command()
def validate(workflow_path: Path) -> None:
    """Validate a workflow file against lightweight governance rules."""

    try:
        _workflow, warnings = inspect_workflow_file(workflow_path)
    except WorkflowValidationError as exc:
        console.print("[red][ERROR][/red] Workflow validation failed.")
        for error in exc.errors:
            console.print(f"  - {error}")
        raise typer.Exit(code=1) from exc

    for warning in warnings:
        console.print(f"[yellow][WARN][/yellow] {warning}")
    console.print("[green][SUCCESS][/green] Workflow validation passed.")


@app.command("config-check")
def config_check(config_path: Path = typer.Argument(Path("policyflow.yml"))) -> None:
    """Validate a Consumer-Repo PolicyFlow config file."""

    try:
        load_consumer_config(config_path)
    except WorkflowValidationError as exc:
        console.print("[red][ERROR][/red] Consumer config validation failed.")
        for error in exc.errors:
            console.print(f"  - {error}")
        raise typer.Exit(code=1) from exc

    console.print("[green][SUCCESS][/green] Consumer config validation passed.")


@app.command("init")
def init(
    target: Path = typer.Argument(Path(".")),
    dry_run: bool = typer.Option(False, "--dry-run"),
    force: bool = typer.Option(False, "--force"),
) -> None:
    """Bootstrap PolicyFlow assets into a Consumer-Repo."""

    result = bootstrap_consumer_repo(target, dry_run=dry_run, force=force)

    for path in result.created:
        console.print(f"created {path}", markup=False)
    for path in result.overwritten:
        console.print(f"overwrote {path}", markup=False)
    for path in result.skipped:
        console.print(f"skipped {path}", markup=False)
    for path in result.would_create:
        console.print(f"would create {path}", markup=False)
    for path in result.would_skip:
        console.print(f"would skip {path}", markup=False)

    console.print("[green][SUCCESS][/green] PolicyFlow bootstrap completed.")


@app.command("doctor")
def doctor(
    target: Path = typer.Argument(Path(".")),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Check whether a Consumer-Repo is ready to run PolicyFlow."""

    report = doctor_consumer_repo(target)

    if json_output:
        typer.echo(json.dumps(report, indent=2))
    else:
        for check in report["checks"]:
            label = {
                "pass": "[PASS]",
                "warning": "[WARN]",
                "failure": "[FAIL]",
            }[check["status"]]
            console.print(f"{label} {check['check']}: {check['message']}", markup=False)
            if check["remediation"]:
                console.print(f"  remediation: {check['remediation']}", markup=False)

    if report["failures"]:
        raise typer.Exit(code=1)


@app.command("validate-pr")
def validate_pr(workflow_path: Path, pr_body_path: Path) -> None:
    """Validate a PR body markdown file against a workflow file."""

    try:
        validate_pull_request(workflow_path, pr_body_path)
    except WorkflowValidationError as exc:
        console.print("[red][ERROR][/red] Pull request validation failed.")
        for error in exc.errors:
            console.print(f"  - {error}")
        raise typer.Exit(code=1) from exc

    console.print("[green][SUCCESS][/green] Pull request validation passed.")


@app.command("validate-github-approvals")
def validate_github_approvals(
    workflow_path: Path, pr_body_path: Path, reviews_path: Path
) -> None:
    """Validate PR approval logins against GitHub review metadata."""

    try:
        validate_github_pr_approvals(workflow_path, pr_body_path, reviews_path)
    except WorkflowValidationError as exc:
        console.print("[red][ERROR][/red] GitHub approval validation failed.")
        for error in exc.errors:
            console.print(f"  - {error}")
        raise typer.Exit(code=1) from exc

    console.print("[green][SUCCESS][/green] GitHub approval validation passed.")


@app.command("status")
def status(workflow_path: Path, json_output: bool = typer.Option(False, "--json")) -> None:
    """Show a detailed workflow status and merge-readiness view."""

    try:
        payload = workflow_status(workflow_path)
    except WorkflowValidationError as exc:
        console.print("[red][ERROR][/red] Workflow status query failed.")
        for error in exc.errors:
            console.print(f"  - {error}")
        raise typer.Exit(code=1) from exc

    if json_output:
        typer.echo(json.dumps(payload, indent=2))
        return

    for line in status_lines(payload):
        console.print(line, markup=False)


@app.command("audit")
def audit(directory: Path, json_output: bool = typer.Option(False, "--json")) -> None:
    """Show an audit overview for workflow files in a directory tree."""

    payload = audit_directory(directory)

    if json_output:
        typer.echo(json.dumps(payload, indent=2))
        return

    for line in audit_lines(payload):
        console.print(line, markup=False)


@app.command("run-phase")
def run_phase(
    workflow_path: Path,
    phase: str,
    runner_config: Path = typer.Option(Path("policyflow.runners.yml"), "--runner-config"),
) -> None:
    """Run one agent-owned workflow phase through the configured external runner."""

    try:
        run_phase_with_runner(workflow_path, phase, runner_config)
    except WorkflowValidationError as exc:
        console.print("[red][ERROR][/red] Agent phase execution failed.")
        for error in exc.errors:
            console.print(f"  - {error}")
        raise typer.Exit(code=1) from exc

    console.print(f"[green][SUCCESS][/green] Executed phase {phase}.")


@app.command("next-step")
def next_step(workflow_path: Path) -> None:
    """Show the next actionable orchestration step for a workflow."""

    try:
        summary = next_step_summary(workflow_path)
    except WorkflowValidationError as exc:
        console.print("[red][ERROR][/red] Workflow orchestration query failed.")
        for error in exc.errors:
            console.print(f"  - {error}")
        raise typer.Exit(code=1) from exc

    console.print(summary)


@app.command("handoff-status")
def handoff_status(workflow_path: Path) -> None:
    """Show recorded workflow handoffs."""

    try:
        lines = handoff_status_summary(workflow_path)
    except WorkflowValidationError as exc:
        console.print("[red][ERROR][/red] Workflow handoff query failed.")
        for error in exc.errors:
            console.print(f"  - {error}")
        raise typer.Exit(code=1) from exc

    for line in lines:
        console.print(line, markup=False)


@app.command("start-phase")
def start_phase(workflow_path: Path, phase: str) -> None:
    """Start a declared workflow phase and persist the runtime state."""

    try:
        start_workflow_phase(workflow_path, phase)
    except WorkflowValidationError as exc:
        console.print("[red][ERROR][/red] Could not start phase.")
        for error in exc.errors:
            console.print(f"  - {error}")
        raise typer.Exit(code=1) from exc

    console.print(f"[green][SUCCESS][/green] Started phase {phase}.")


@app.command("complete-phase")
def complete_phase(workflow_path: Path, phase: str) -> None:
    """Complete an in-progress workflow phase and persist the runtime state."""

    try:
        complete_workflow_phase(workflow_path, phase)
    except WorkflowValidationError as exc:
        console.print("[red][ERROR][/red] Could not complete phase.")
        for error in exc.errors:
            console.print(f"  - {error}")
        raise typer.Exit(code=1) from exc

    console.print(f"[green][SUCCESS][/green] Completed phase {phase}.")


@app.command("block-phase")
def block_phase(workflow_path: Path, phase: str, reason: str = typer.Option(..., "--reason")) -> None:
    """Block a workflow phase with an explicit reason and persist the runtime state."""

    try:
        block_workflow_phase(workflow_path, phase, reason)
    except WorkflowValidationError as exc:
        console.print("[red][ERROR][/red] Could not block phase.")
        for error in exc.errors:
            console.print(f"  - {error}")
        raise typer.Exit(code=1) from exc

    console.print(f"[green][SUCCESS][/green] Blocked phase {phase}.")


@app.command("record-handoff")
def record_handoff(
    workflow_path: Path,
    from_phase: str = typer.Option(..., "--from-phase"),
    to_phase: str = typer.Option(..., "--to-phase"),
    required_input: list[str] = typer.Option([], "--required-input"),
    produced_output: list[str] = typer.Option([], "--produced-output"),
    blocker: list[str] = typer.Option([], "--blocker"),
    override_ref: list[str] = typer.Option([], "--override-ref"),
) -> None:
    """Record a workflow handoff with concrete input and output artifacts."""

    try:
        record_workflow_handoff(
            workflow_path,
            from_phase,
            to_phase,
            required_input,
            produced_output,
            blocker,
            override_ref,
        )
    except WorkflowValidationError as exc:
        console.print("[red][ERROR][/red] Could not record handoff.")
        for error in exc.errors:
            console.print(f"  - {error}")
        raise typer.Exit(code=1) from exc

    console.print(
        f"[green][SUCCESS][/green] Recorded handoff {from_phase} -> {to_phase}."
    )


if __name__ == "__main__":
    app()
