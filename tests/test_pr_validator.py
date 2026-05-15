from pathlib import Path

import pytest
from typer.testing import CliRunner

from policyflow.cli import app
from policyflow.exceptions import WorkflowValidationError
from policyflow.validator import validate_pull_request


FIXTURES_DIR = Path(__file__).parent / "fixtures"
runner = CliRunner()


def fixture_path(name: str) -> Path:
    return FIXTURES_DIR / name


def test_valid_pull_request_passes() -> None:
    result = validate_pull_request(
        fixture_path("valid-medium.yml"), fixture_path("valid-pr-body.md")
    )

    assert result.context.workflow_file == "workflows/examples/valid-medium.yml"
    assert result.context.risk_level == "MEDIUM"


def test_pull_request_without_linked_issue_fails() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_pull_request(
            fixture_path("valid-medium.yml"),
            fixture_path("pr-missing-linked-issue.md"),
        )

    assert "PR body must include a non-empty Linked Issue section." in exc_info.value.errors


def test_pull_request_with_mismatched_workflow_file_fails() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_pull_request(
            fixture_path("valid-medium.yml"),
            fixture_path("pr-mismatched-workflow-file.md"),
        )

    assert (
        "PR body Workflow File must match context.workflow_file: "
        "workflows/examples/valid-medium.yml"
    ) in exc_info.value.errors


def test_pull_request_with_mismatched_risk_level_fails() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_pull_request(
            fixture_path("valid-medium.yml"),
            fixture_path("pr-mismatched-risk-level.md"),
        )

    assert (
        "PR body Declared risk level must match context.risk_level: MEDIUM"
        in exc_info.value.errors
    )


def test_pull_request_without_workflow_confirmation_fails() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_pull_request(
            fixture_path("valid-medium.yml"),
            fixture_path("pr-unchecked-workflow-confirmation.md"),
        )

    assert (
        "PR body must confirm that the linked workflow file governed this change."
        in exc_info.value.errors
    )


def test_validate_pr_command_succeeds() -> None:
    result = runner.invoke(
        app,
        [
            "validate-pr",
            str(fixture_path("valid-medium.yml")),
            str(fixture_path("valid-pr-body.md")),
        ],
    )

    assert result.exit_code == 0
    assert "[SUCCESS] Pull request validation passed." in result.stdout
