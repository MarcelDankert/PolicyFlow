"""Stable public Python API for PolicyFlow governance consumers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from policyflow.exceptions import WorkflowValidationError
from policyflow.github_approval import ApprovalValidationResult, validate_github_pr_approvals
from policyflow.models import ValidationResultV2, WorkflowDocument, WorkflowDocumentV2
from policyflow.validator import (
    inspect_workflow_file,
    inspect_workflow_v2_data,
    inspect_workflow_v2_file,
    validate_pull_request,
    validate_workflow_data as _validate_workflow_data,
    validate_workflow_file,
    validate_workflow_v2_data as _validate_workflow_v2_data,
    validate_workflow_v2_file,
)

__all__ = [
    "ApprovalValidationResult",
    "ValidationResultV2",
    "WorkflowDocument",
    "WorkflowDocumentV2",
    "WorkflowValidationError",
    "inspect_workflow",
    "inspect_workflow_v2",
    "inspect_workflow_v2_data",
    "validate_github_approvals",
    "validate_pr_body",
    "validate_workflow",
    "validate_workflow_data",
    "validate_workflow_v2",
    "validate_workflow_v2_data",
]


def inspect_workflow(path: str | Path) -> tuple[WorkflowDocument, list[str]]:
    """Validate a V1 workflow file and return the normalized document plus warnings."""

    return inspect_workflow_file(path)


def validate_workflow(path: str | Path) -> WorkflowDocument:
    """Validate a V1 workflow file and return its normalized governance document."""

    return validate_workflow_file(path)


def validate_workflow_data(raw_data: dict[str, Any]) -> WorkflowDocument:
    """Validate an in-memory V1 workflow mapping."""

    return _validate_workflow_data(raw_data)


def validate_workflow_v2(path: str | Path) -> WorkflowDocumentV2:
    """Validate a V2 governance file and return the normalized document."""

    return validate_workflow_v2_file(path)


def validate_workflow_v2_data(raw_data: dict[str, Any]) -> WorkflowDocumentV2:
    """Validate an in-memory V2 governance mapping."""

    return _validate_workflow_v2_data(raw_data)


def inspect_workflow_v2(
    path: str | Path, *, allow_pending_human_approval: bool = False
) -> ValidationResultV2:
    """Return the V2 PASS/WARN/BLOCK governance validation result."""

    return inspect_workflow_v2_file(
        path, allow_pending_human_approval=allow_pending_human_approval
    )


def validate_pr_body(
    workflow_path: str | Path, pr_body_path: str | Path
) -> WorkflowDocument:
    """Validate PR body governance claims against a workflow file."""

    return validate_pull_request(workflow_path, pr_body_path)


def validate_github_approvals(
    workflow_path: str | Path,
    pr_body_path: str | Path,
    reviews_path: str | Path,
    *,
    allow_pending: bool = False,
) -> ApprovalValidationResult:
    """Validate declared human approvers against read-only GitHub review JSON."""

    return validate_github_pr_approvals(
        workflow_path,
        pr_body_path,
        reviews_path,
        allow_pending=allow_pending,
    )
