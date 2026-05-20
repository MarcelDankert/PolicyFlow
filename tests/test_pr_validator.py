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


def test_pull_request_without_override_reference_fails() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_pull_request(
            fixture_path("valid-medium.yml"),
            fixture_path("pr-missing-override-reference.md"),
        )

    assert (
        "PR body must reference workflow override: phase-bypass-1"
        in exc_info.value.errors
    )


def test_pull_request_with_mismatched_override_type_fails() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_pull_request(
            fixture_path("valid-medium.yml"),
            fixture_path("pr-mismatched-override-type.md"),
        )

    assert (
        "PR body Override phase-bypass-1 must declare type phase_bypass"
        in exc_info.value.errors
    )


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


def test_pull_request_without_workflow_first_confirmation_fails() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_pull_request(
            fixture_path("valid-medium.yml"),
            fixture_path("pr-unchecked-workflow-first-confirmation.md"),
        )

    assert (
        "PR body must confirm that the workflow file existed before implementation "
        "and governed the work from the start."
        in exc_info.value.errors
    )


def test_pull_request_without_workflow_lock_confirmation_fails() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_pull_request(
            fixture_path("valid-medium.yml"),
            fixture_path("pr-unchecked-workflow-lock-confirmation.md"),
        )

    assert (
        "PR body must confirm that scope, non-goals, and risk were fixed in the "
        "workflow before implementation started."
        in exc_info.value.errors
    )


def test_pull_request_without_workflow_phase_confirmation_fails() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_pull_request(
            fixture_path("valid-medium.yml"),
            fixture_path("pr-unchecked-workflow-phase-confirmation.md"),
        )

    assert (
        "PR body must confirm that required workflow phases were executed as "
        "visible working steps, not only documented after the fact."
        in exc_info.value.errors
    )


def test_pull_request_without_planning_evidence_reference_fails() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_pull_request(
            fixture_path("valid-medium.yml"),
            fixture_path("pr-missing-planning-evidence-reference.md"),
        )

    assert (
        "PR body must reference workflow evidence block: evidence.planning"
        in exc_info.value.errors
    )


def test_pull_request_with_mismatched_architecture_evidence_reference_fails() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_pull_request(
            fixture_path("valid-medium.yml"),
            fixture_path("pr-mismatched-architecture-evidence-reference.md"),
        )

    assert (
        "PR body Architecture evidence must reference workflow evidence.architecture-check"
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
