from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
import yaml
from rich.console import Console

from policyflow.bootstrap import bootstrap_consumer_repo
from policyflow.doctor import doctor_consumer_repo
from policyflow.exceptions import WorkflowValidationError
from policyflow.github_approval import validate_github_pr_approvals
from policyflow.validator import (
    inspect_workflow_file,
    inspect_workflow_v2_file,
    validate_pull_request,
)


app = typer.Typer(help="PolicyFlow governance validator.")
console = Console()


@app.callback()
def main() -> None:
    """PolicyFlow governance validator commands."""


@app.command()
def validate(
    workflow_path: Path,
    json_output: bool = typer.Option(False, "--json"),
    allow_pending: bool = typer.Option(
        False,
        "--allow-pending",
        help="Return WARN instead of BLOCK for pending V2 human approval evidence.",
    ),
) -> None:
    """Validate governance policy and evidence for a change."""

    try:
        if _is_v2_workflow(workflow_path):
            result = inspect_workflow_v2_file(
                workflow_path, allow_pending_human_approval=allow_pending
            )
            if json_output:
                typer.echo(json.dumps(result.to_json_dict(), indent=2))
            else:
                _print_v2_validation_result(result.to_json_dict())
            if result.decision == "BLOCK":
                raise typer.Exit(code=1)
            return

        workflow, warnings = inspect_workflow_file(workflow_path)
    except WorkflowValidationError as exc:
        _print_errors("Workflow validation failed.", exc.errors, json_output=json_output)
        raise typer.Exit(code=1) from exc

    if json_output:
        typer.echo(
            json.dumps(
                {
                    "schema_version": "policyflow.validation.v1",
                    "decision": "WARN" if warnings else "PASS",
                    "merge_ready": not warnings,
                    "workflow_id": workflow.workflow.id,
                    "warnings": warnings,
                    "errors": [],
                },
                indent=2,
            )
        )
        return

    for warning in warnings:
        console.print(f"[yellow][WARN][/yellow] {warning}")
    console.print("[green][SUCCESS][/green] Workflow validation passed.")


@app.command("init")
def init(
    target: Path = typer.Argument(Path(".")),
    dry_run: bool = typer.Option(False, "--dry-run"),
    force: bool = typer.Option(False, "--force"),
    github: bool = typer.Option(
        True,
        "--github/--no-github",
        help="Include read-only GitHub PR template and governance workflow assets.",
    ),
) -> None:
    """Bootstrap PolicyFlow governance assets into a repository."""

    result = bootstrap_consumer_repo(target, dry_run=dry_run, force=force, github=github)

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
    """Check whether a repository is ready to run PolicyFlow governance."""

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
def validate_pr(
    workflow_path: Path,
    pr_body_path: Path,
    github_reviews: Path | None = typer.Option(
        None,
        "--github-reviews",
        help="Read-only GitHub PR reviews JSON used to validate declared approvers.",
    ),
    allow_pending: bool = typer.Option(
        False,
        "--allow-pending",
        help="Treat missing matching GitHub approvals as pending instead of failed.",
    ),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Validate PR governance claims against workflow policy and evidence."""

    try:
        if github_reviews is None:
            workflow = validate_pull_request(workflow_path, pr_body_path)
            payload: dict[str, Any] = {
                "schema_version": "policyflow.pr_validation.v1",
                "decision": "PASS",
                "workflow_id": workflow.workflow.id,
                "github_approval_status": "not_checked",
                "pending_logins": [],
                "errors": [],
            }
        else:
            result = validate_github_pr_approvals(
                workflow_path,
                pr_body_path,
                github_reviews,
                allow_pending=allow_pending,
            )
            payload = {
                "schema_version": "policyflow.pr_validation.v1",
                "decision": "WARN" if result.status == "pending" else "PASS",
                "workflow_id": result.workflow.workflow.id,
                "github_approval_status": result.status,
                "pending_logins": result.pending_logins,
                "errors": [],
            }
    except WorkflowValidationError as exc:
        _print_errors("Pull request validation failed.", exc.errors, json_output=json_output)
        raise typer.Exit(code=1) from exc

    if json_output:
        typer.echo(json.dumps(payload, indent=2))
        return

    if payload["github_approval_status"] == "pending":
        console.print("[yellow][PENDING][/yellow] GitHub approval pending.")
        for login in payload["pending_logins"]:
            console.print(f"  - awaiting APPROVED review from login: {login}")
        return

    console.print("[green][SUCCESS][/green] Pull request validation passed.")


def _is_v2_workflow(path: Path) -> bool:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise WorkflowValidationError([f"Invalid YAML: {exc}"]) from exc

    if not isinstance(data, dict):
        raise WorkflowValidationError(["Workflow file must contain a top-level YAML mapping"])

    return data.get("version") == 2


def _print_v2_validation_result(payload: dict[str, Any]) -> None:
    decision = payload["decision"]
    if decision == "PASS":
        console.print("[green][SUCCESS][/green] Workflow validation passed.")
    elif decision == "WARN":
        console.print("[yellow][WARN][/yellow] Workflow validation has warnings.")
    else:
        console.print("[red][ERROR][/red] Workflow validation blocked.")

    for warning in payload["warnings"]:
        console.print(f"  - {warning['message']}")
    for error in payload["errors"]:
        console.print(f"  - {error['message']}")


def _print_errors(title: str, errors: list[str], *, json_output: bool) -> None:
    if json_output:
        typer.echo(
            json.dumps(
                {
                    "decision": "BLOCK",
                    "merge_ready": False,
                    "errors": errors,
                    "warnings": [],
                },
                indent=2,
            )
        )
        return

    console.print(f"[red][ERROR][/red] {title}")
    for error in errors:
        console.print(f"  - {error}")


if __name__ == "__main__":
    app()
