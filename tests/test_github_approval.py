from pathlib import Path

import pytest
from typer.testing import CliRunner

from policyflow.cli import app
from policyflow.exceptions import WorkflowValidationError
from policyflow.github_approval import validate_github_pr_approvals


FIXTURES_DIR = Path(__file__).parent / "fixtures"
runner = CliRunner()


def fixture_path(name: str) -> Path:
    return FIXTURES_DIR / name


def test_github_pr_approvals_pass_for_matching_human_approval_login() -> None:
    workflow = fixture_path("valid-high.yml")
    pr_body = fixture_path("valid-high-pr-body.md")
    reviews = fixture_path("github-reviews-valid-high.json")

    result = validate_github_pr_approvals(workflow, pr_body, reviews)

    assert result.context.risk_level == "HIGH"


def test_github_pr_approvals_fail_when_human_approval_login_lacks_approved_review() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_github_pr_approvals(
            fixture_path("valid-high.yml"),
            fixture_path("valid-high-pr-body.md"),
            fixture_path("github-reviews-missing-human-approval.json"),
        )

    assert (
        "GitHub PR approvals must include an APPROVED review from login: arch-board"
        in exc_info.value.errors
    )


def test_github_pr_approvals_fail_when_override_approver_lacks_approved_review() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_github_pr_approvals(
            fixture_path("valid-medium.yml"),
            fixture_path("valid-pr-body.md"),
            fixture_path("github-reviews-missing-override-approver.json"),
        )

    assert (
        "GitHub PR approvals must include an APPROVED review from login: architecture-agent"
        in exc_info.value.errors
    )


def test_github_pr_approvals_fail_when_high_risk_approval_evidence_is_incomplete() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_github_pr_approvals(
            fixture_path("high-missing-evidence-approval.yml"),
            fixture_path("valid-high-pr-body.md"),
            fixture_path("github-reviews-valid-high.json"),
        )

    assert (
        "HIGH risk workflows with human approval required must declare evidence.approval.approved_by, evidence.approval.reference, and evidence.approval.scope_confirmed; governance.approval_evidence alone is not sufficient for PR approval validation."
        in exc_info.value.errors
    )


def test_validate_github_approvals_command_succeeds() -> None:
    result = runner.invoke(
        app,
        [
            "validate-github-approvals",
            str(fixture_path("valid-high.yml")),
            str(fixture_path("valid-high-pr-body.md")),
            str(fixture_path("github-reviews-valid-high.json")),
        ],
    )

    assert result.exit_code == 0
    assert "[SUCCESS] GitHub approval validation passed." in result.stdout
