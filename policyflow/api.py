"""Stable public Python API for PolicyFlow consumers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from policyflow.exceptions import WorkflowValidationError
from policyflow.github_approval import validate_github_pr_approvals
from policyflow.models import WorkflowDocument
from policyflow.reporting import audit_directory, workflow_status
from policyflow.runtime import (
    block_phase,
    complete_phase,
    record_handoff,
    start_phase,
)
from policyflow.validator import (
    inspect_workflow_file,
    validate_pull_request,
    validate_workflow_data as _validate_workflow_data,
    validate_workflow_file,
)

__all__ = [
    "WorkflowDocument",
    "WorkflowValidationError",
    "audit_workflows",
    "block_workflow_phase",
    "complete_workflow_phase",
    "get_workflow_status",
    "inspect_workflow",
    "record_workflow_handoff",
    "start_workflow_phase",
    "validate_github_approvals",
    "validate_pr_body",
    "validate_workflow",
    "validate_workflow_data",
]


def inspect_workflow(path: str | Path) -> tuple[WorkflowDocument, list[str]]:
    """Validate a workflow file and return the normalized document plus warnings."""

    return inspect_workflow_file(path)


def validate_workflow(path: str | Path) -> WorkflowDocument:
    """Validate a workflow file and return its normalized workflow document."""

    return validate_workflow_file(path)


def validate_workflow_data(raw_data: dict[str, Any]) -> WorkflowDocument:
    """Validate an in-memory workflow mapping."""

    return _validate_workflow_data(raw_data)


def validate_pr_body(
    workflow_path: str | Path, pr_body_path: str | Path
) -> WorkflowDocument:
    """Validate a PR body markdown file against a workflow file."""

    return validate_pull_request(workflow_path, pr_body_path)


def validate_github_approvals(
    workflow_path: str | Path, pr_body_path: str | Path, reviews_path: str | Path
) -> WorkflowDocument:
    """Validate GitHub review metadata against workflow approval requirements."""

    return validate_github_pr_approvals(
        workflow_path, pr_body_path, reviews_path
    ).workflow


def get_workflow_status(path: str | Path) -> dict[str, Any]:
    """Return workflow status and merge-readiness data."""

    return workflow_status(Path(path))


def audit_workflows(directory: str | Path) -> dict[str, Any]:
    """Return an audit payload for all workflow files under a directory."""

    return audit_directory(Path(directory))


def start_workflow_phase(path: str | Path, phase: str) -> None:
    """Start a pending workflow phase and persist runtime state."""

    start_phase(Path(path), phase)


def complete_workflow_phase(path: str | Path, phase: str) -> None:
    """Complete an in-progress workflow phase and persist runtime state."""

    complete_phase(Path(path), phase)


def block_workflow_phase(path: str | Path, phase: str, reason: str) -> None:
    """Block a workflow phase with a reason and persist runtime state."""

    block_phase(Path(path), phase, reason)


def record_workflow_handoff(
    path: str | Path,
    from_phase: str,
    to_phase: str,
    required_inputs: list[str],
    produced_outputs: list[str],
    blockers: list[str] | None = None,
    override_refs: list[str] | None = None,
) -> None:
    """Record a workflow phase handoff with concrete artifacts."""

    record_handoff(
        Path(path),
        from_phase,
        to_phase,
        required_inputs,
        produced_outputs,
        blockers,
        override_refs,
    )
