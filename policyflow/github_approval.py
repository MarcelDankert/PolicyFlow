from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from policyflow.exceptions import WorkflowValidationError
from policyflow.validator import HIGH_RISK_APPROVAL_EVIDENCE_ERROR, validate_pull_request


def validate_github_pr_approvals(
    workflow_path: str | Path, pr_body_path: str | Path, reviews_path: str | Path
):
    workflow = validate_pull_request(workflow_path, pr_body_path)
    reviews = _load_reviews_json(Path(reviews_path))
    approved_logins = _approved_review_logins(reviews)
    required_logins = _required_approval_logins(workflow)

    errors: list[str] = []
    for login in required_logins:
        if login not in approved_logins:
            errors.append(
                f"GitHub PR approvals must include an APPROVED review from login: {login}"
            )

    if errors:
        raise WorkflowValidationError(errors)

    return workflow


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
    latest_state_by_login: dict[str, str] = {}

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
        latest_state_by_login[login] = state.upper()

    return {
        login
        for login, state in latest_state_by_login.items()
        if state == "APPROVED"
    }


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
