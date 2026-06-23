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


def test_pull_request_without_workflow_file_section_reports_body_diagnostics(
    tmp_path: Path,
) -> None:
    pr_body_path = tmp_path / "pr-missing-workflow-file-section.md"
    pr_body_path.write_text(
        """## Summary

Bounded parser validation update.

## Linked Issue

#97

## Governance
- Declared risk level: MEDIUM
- Confidence summary: bounded change with direct tests

## Confirmation
- [x] The linked workflow file governed this change
- [x] The workflow file existed before implementation and governed the work from the start
- [x] Scope, non-goals, and risk were fixed in the workflow before implementation started
- [x] Required workflow phases were executed as visible working steps, not only documented after the fact
""",
        encoding="utf-8",
    )

    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_pull_request(fixture_path("valid-medium.yml"), pr_body_path)

    assert (
        "PR body must include a Workflow File section. "
        "PR body length: 524 characters. Markdown headings found: "
        "Summary, Linked Issue, Governance, Confirmation."
    ) in exc_info.value.errors


def test_pull_request_with_empty_workflow_file_section_reports_body_diagnostics(
    tmp_path: Path,
) -> None:
    pr_body_path = tmp_path / "pr-empty-workflow-file-section.md"
    pr_body_path.write_text(
        """## Summary

Bounded parser validation update.

## Linked Issue

#97

## Workflow File

## Governance
- Declared risk level: MEDIUM
- Confidence summary: bounded change with direct tests

## Confirmation
- [x] The linked workflow file governed this change
- [x] The workflow file existed before implementation and governed the work from the start
- [x] Scope, non-goals, and risk were fixed in the workflow before implementation started
- [x] Required workflow phases were executed as visible working steps, not only documented after the fact
""",
        encoding="utf-8",
    )

    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_pull_request(fixture_path("valid-medium.yml"), pr_body_path)

    assert (
        "PR body Workflow File section is empty. "
        "PR body length: 542 characters. Markdown headings found: "
        "Summary, Linked Issue, Workflow File, Governance, Confirmation."
    ) in exc_info.value.errors


def test_pull_request_accepts_bulleted_backticked_workflow_file(
    tmp_path: Path,
) -> None:
    pr_body = fixture_path("valid-pr-body.md").read_text(encoding="utf-8")
    pr_body_path = tmp_path / "pr-bulleted-backticked-workflow-file.md"
    pr_body_path.write_text(
        pr_body.replace(
            "- workflows/examples/valid-medium.yml",
            "- `workflows/examples/valid-medium.yml`",
        ),
        encoding="utf-8",
    )

    result = validate_pull_request(fixture_path("valid-medium.yml"), pr_body_path)

    assert result.context.workflow_file == "workflows/examples/valid-medium.yml"


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


def test_pull_request_without_confidence_summary_fails() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_pull_request(
            fixture_path("valid-medium.yml"),
            fixture_path("pr-missing-confidence-summary.md"),
        )

    assert (
        "PR body must include Confidence summary in the Governance section."
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


def test_high_risk_pull_request_requires_human_approval_login() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_pull_request(
            fixture_path("valid-high.yml"),
            fixture_path("pr-missing-human-approval-login.md"),
        )

    assert (
        "PR body must declare Human approval login if required: arch-board"
        in exc_info.value.errors
    )


def test_pull_request_with_mismatched_override_approval_login_fails() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_pull_request(
            fixture_path("valid-medium.yml"),
            fixture_path("pr-mismatched-override-approval-login.md"),
        )

    assert (
        "PR body Override phase-bypass-1 must declare approved_by login architecture-agent"
        in exc_info.value.errors
    )


def test_high_risk_pull_request_with_approval_login_passes() -> None:
    result = validate_pull_request(
        fixture_path("valid-high.yml"), fixture_path("valid-high-pr-body.md")
    )

    assert result.context.risk_level == "HIGH"


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
