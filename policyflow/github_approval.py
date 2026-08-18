from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from policyflow.exceptions import WorkflowValidationError
from policyflow.models import (
    EvidenceV2,
    V2EvidenceStatus,
    V2EvidenceType,
    WorkflowDocumentV2,
)
from policyflow.validator import (
    HIGH_RISK_APPROVAL_EVIDENCE_ERROR,
    inspect_workflow_v2_file,
    validate_pull_request,
)


@dataclass(frozen=True)
class ApprovalValidationResult:
    workflow: Any
    status: str
    pending_logins: list[str]
    errors: list[str]

    def __getattr__(self, name: str) -> Any:
        return getattr(self.workflow, name)


def validate_github_pr_approvals(
    workflow_path: str | Path,
    pr_body_path: str | Path,
    reviews_path: str | Path,
    *,
    allow_pending: bool = False,
) -> ApprovalValidationResult:
    if _is_v2_workflow(Path(workflow_path)):
        return _validate_github_pr_approvals_v2(
            workflow_path,
            pr_body_path,
            reviews_path,
            allow_pending=allow_pending,
        )

    workflow = validate_pull_request(workflow_path, pr_body_path)
    reviews = _load_reviews_json(Path(reviews_path))
    approved_logins = _approved_review_logins(reviews)
    required_logins = _required_approval_logins(workflow)

    errors: list[str] = []
    pending_logins: list[str] = []
    for login in required_logins:
        if login not in approved_logins:
            pending_logins.append(login)

    if pending_logins and not allow_pending:
        for login in pending_logins:
            errors.append(
                f"GitHub PR approvals must include an APPROVED review from login: {login}"
            )

    if errors:
        raise WorkflowValidationError(errors)

    return ApprovalValidationResult(
        workflow=workflow,
        status="pending" if pending_logins else "approved",
        pending_logins=sorted(pending_logins),
        errors=[],
    )


def _validate_github_pr_approvals_v2(
    workflow_path: str | Path,
    pr_body_path: str | Path,
    reviews_path: str | Path,
    *,
    allow_pending: bool,
) -> ApprovalValidationResult:
    _require_pr_body_file(Path(pr_body_path))
    validation_result = inspect_workflow_v2_file(
        workflow_path, allow_pending_human_approval=allow_pending
    )
    if validation_result.decision == "BLOCK":
        raise WorkflowValidationError(
            [finding.message for finding in validation_result.errors]
        )

    workflow = validation_result.workflow
    reviews = _load_reviews_json(Path(reviews_path))
    latest_review_by_login = _latest_review_by_login(reviews)
    required_approvals = _required_v2_github_approval_evidence(workflow)

    errors: list[str] = []
    pending_logins: list[str] = []
    for evidence in required_approvals:
        login = _github_review_login_from_source(evidence.source)
        if login is None:
            errors.append(
                "V2 GitHub approval evidence must use source "
                f"'github-review:<login>': {evidence.id}"
            )
            continue

        if evidence.status == V2EvidenceStatus.PENDING:
            pending_logins.append(login)
            continue

        review = latest_review_by_login.get(login)
        if review is None or str(review.get("state", "")).upper() != "APPROVED":
            errors.append(
                f"GitHub PR approvals must include an APPROVED review from login: {login}"
            )
            continue

        if evidence.ref not in _github_review_refs(review):
            errors.append(
                f"V2 GitHub approval evidence '{evidence.id}' ref must match "
                f"the latest APPROVED review for login: {login}"
            )

    if pending_logins and not allow_pending:
        for login in sorted(set(pending_logins)):
            errors.append(
                f"GitHub PR approvals must include an APPROVED review from login: {login}"
            )

    if errors:
        raise WorkflowValidationError(errors)

    return ApprovalValidationResult(
        workflow=workflow,
        status="pending" if pending_logins else "approved",
        pending_logins=sorted(set(pending_logins)),
        errors=[],
    )


def _load_reviews_json(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise WorkflowValidationError([f"GitHub review file not found: {path}"])

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise WorkflowValidationError([f"Invalid GitHub review JSON: {exc}"]) from exc

    if not isinstance(data, list):
        raise WorkflowValidationError(
            ["GitHub review file must contain a top-level JSON array"]
        )

    return [item for item in data if isinstance(item, dict)]


def _approved_review_logins(reviews: list[dict[str, Any]]) -> set[str]:
    latest_state_by_login = {
        login: str(review.get("state", "")).upper()
        for login, review in _latest_review_by_login(reviews).items()
    }

    return {
        login
        for login, state in latest_state_by_login.items()
        if state == "APPROVED"
    }


def _latest_review_by_login(reviews: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    latest_review_by_login: dict[str, dict[str, Any]] = {}

    for review in reviews:
        user = review.get("user")
        if not isinstance(user, dict):
            continue
        login = user.get("login")
        state = review.get("state")
        if not isinstance(login, str) or not login:
            continue
        if not isinstance(state, str) or not state:
            continue
        latest_review_by_login[login] = review

    return latest_review_by_login


def _required_approval_logins(workflow) -> set[str]:
    required_logins: set[str] = set()

    if workflow.governance.human_approval_required:
        approval_evidence = workflow.evidence.approval if workflow.evidence else None
        if approval_evidence is None or not approval_evidence.approved_by:
            raise WorkflowValidationError([HIGH_RISK_APPROVAL_EVIDENCE_ERROR])
        required_logins.add(approval_evidence.approved_by)

    for override in workflow.overrides or []:
        if override.approved_by:
            required_logins.add(override.approved_by)

    return required_logins


def _required_v2_github_approval_evidence(
    workflow: WorkflowDocumentV2,
) -> list[EvidenceV2]:
    if not workflow.governance.human_approval_required:
        return []

    return [
        evidence
        for evidence in workflow.evidence
        if evidence.type == V2EvidenceType.APPROVAL
        and evidence.status in {V2EvidenceStatus.PASSED, V2EvidenceStatus.PENDING}
    ]


def _github_review_login_from_source(source: str) -> str | None:
    prefix = "github-review:"
    if not source.startswith(prefix):
        return None
    login = source.removeprefix(prefix).strip()
    return login or None


def _github_review_refs(review: dict[str, Any]) -> set[str]:
    refs: set[str] = set()
    for key in ("id", "node_id", "url", "html_url", "pull_request_url"):
        value = review.get(key)
        if value not in (None, ""):
            refs.add(str(value))
    return refs


def _require_pr_body_file(path: Path) -> None:
    if not path.exists():
        raise WorkflowValidationError([f"PR body file not found: {path}"])


def _is_v2_workflow(path: Path) -> bool:
    if not path.exists():
        raise WorkflowValidationError([f"Workflow file not found: {path}"])

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise WorkflowValidationError([f"Invalid YAML: {exc}"]) from exc

    if not isinstance(data, dict):
        raise WorkflowValidationError(
            ["Workflow file must contain a top-level YAML mapping"]
        )

    return data.get("version") == 2
