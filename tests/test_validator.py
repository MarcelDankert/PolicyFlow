from pathlib import Path

import pytest

import policyflow.validator as validator_module
from policyflow.exceptions import WorkflowValidationError
from policyflow.validator import validate_workflow_file


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def fixture_path(name: str) -> Path:
    return FIXTURES_DIR / name


def test_valid_low_workflow_passes() -> None:
    result = validate_workflow_file(fixture_path("valid-low.yml"))

    assert result.context.workflow_file == "workflows/examples/valid-low.yml"
    assert result.context.risk_level == "LOW"
    assert result.context.confidence.planning
    assert result.context.confidence.residual_uncertainty
    assert result.governance.required_reviews == ["review-agent"]
    assert result.governance.human_approval_required is False
    assert result.execution.mode == "strict"
    assert [phase.phase for phase in result.execution.phases] == [
        "planning",
        "implementation",
        "review",
    ]
    assert result.contracts.planning.owner_agent == "planning-agent"


def test_valid_medium_workflow_passes() -> None:
    result = validate_workflow_file(fixture_path("valid-medium.yml"))

    assert result.context.risk_level == "MEDIUM"
    assert result.context.confidence.implementation
    assert result.governance.required_reviews == [
        "architecture-agent",
        "review-agent",
        "qa-agent",
    ]
    assert [phase.phase for phase in result.execution.phases] == [
        "planning",
        "architecture-check",
        "implementation",
        "review",
        "qa",
    ]
    assert result.contracts.architecture_check.owner_agent == "architecture-agent"
    assert result.overrides[0].type == "phase_bypass"
    assert result.runtime.status == "handoff_pending"
    assert result.handoffs[0].to_phase == "implementation"


def test_valid_high_workflow_passes() -> None:
    result = validate_workflow_file(fixture_path("valid-high.yml"))

    assert result.context.risk_level == "HIGH"
    assert result.context.confidence.tests
    assert result.governance.human_approval_required is True
    assert result.governance.escalation_required is True
    assert result.governance.protected_areas_touched == ["database schema"]
    assert result.governance.approval_evidence == [
        "approved in architecture review"
    ]
    assert [phase.phase for phase in result.execution.phases] == [
        "planning",
        "architecture-check",
        "implementation",
        "review",
        "qa",
        "approval",
    ]
    assert result.evidence.approval.approved_by == "arch-board"
    assert result.contracts.planning.owner_agent == "planning-agent"


def test_root_level_fallback_fields_are_accepted() -> None:
    result = validate_workflow_file(fixture_path("valid-root-fallback.yml"))

    assert result.context.workflow_file == "workflows/examples/root-fallback.yml"
    assert result.context.risk_level == "LOW"
    assert result.context.confidence.planning == "Root fallback planning confidence is documented."
    assert result.governance.required_reviews == ["review-agent"]


def test_root_level_fallback_support_is_explicitly_covered_by_fixture() -> None:
    data = fixture_path("valid-root-fallback.yml").read_text(encoding="utf-8")

    for field in (
        "workflow_file:",
        "risk_level:",
        "confidence:",
        "required_reviews:",
        "human_approval_required:",
    ):
        assert field in data

    validate_workflow_file(fixture_path("valid-root-fallback.yml"))


def test_valid_complete_evidence_workflow_passes() -> None:
    result = validate_workflow_file(fixture_path("valid-complete-evidence.yml"))

    assert result.evidence.review.outcome == "approved"
    assert result.evidence.qa.outcome == "passed"
    assert result.contracts.implementation.owner_agent == "senior-dev-agent"
    assert result.contracts.review.owner_agent == "review-agent"
    assert result.contracts.qa.owner_agent == "qa-agent"


def test_release_readiness_evidence_fixture_passes() -> None:
    result = validate_workflow_file(fixture_path("valid-release-readiness.yml"))
    data = fixture_path("valid-release-readiness.yml").read_text(encoding="utf-8")

    assert result.context.risk_level == "MEDIUM"
    for expected in (
        "release_readiness:",
        "state: preparatory",
        "state: blocked",
        "ready_for_release",
        "release_blockers:",
        "blocked_issues:",
        "issue_ordering:",
        "external_credentials_required:",
        "non_executable_checks:",
        "draft_prs:",
    ):
        assert expected in data


def test_evaluation_schema_fixture_passes() -> None:
    result = validate_workflow_file(fixture_path("valid-evaluation-schema.yml"))
    data = fixture_path("valid-evaluation-schema.yml").read_text(encoding="utf-8")

    assert result.context.risk_level == "MEDIUM"
    for expected in (
        "evaluation:",
        "categories:",
        "required_metrics:",
        "thresholds:",
        "evidence_refs:",
        "compliance_status:",
        "tests",
        "coverage",
        "security",
    ):
        assert expected in data


def test_missing_risk_level_fails() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_workflow_file(fixture_path("missing-risk-level.yml"))

    assert "context.risk_level is required" in exc_info.value.errors


def test_missing_confidence_fails() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_workflow_file(fixture_path("missing-confidence.yml"))

    assert "context.confidence is required" in exc_info.value.errors


def test_malformed_confidence_fails() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_workflow_file(fixture_path("malformed-confidence.yml"))

    assert "context.confidence.implementation is required" in exc_info.value.errors
    assert "context.confidence.residual_uncertainty is required" in exc_info.value.errors


def test_missing_execution_fails() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_workflow_file(fixture_path("missing-execution.yml"))

    assert "execution.mode is required" in exc_info.value.errors


def test_invalid_execution_state_fails() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_workflow_file(fixture_path("invalid-execution-state.yml"))

    assert "execution.phases.0.state: Input should be 'pending', 'in_progress', 'completed' or 'blocked'" in exc_info.value.errors


def test_medium_risk_requires_architecture_check_phase() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_workflow_file(fixture_path("medium-missing-architecture-phase.yml"))

    assert (
        "MEDIUM risk workflows must declare execution phases: architecture-check"
        in exc_info.value.errors
    )


def test_high_risk_requires_approval_phase() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_workflow_file(fixture_path("high-missing-approval-phase.yml"))

    assert (
        "HIGH risk workflows must declare execution phases: approval"
        in exc_info.value.errors
    )


def test_invalid_review_evidence_fails() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_workflow_file(fixture_path("invalid-review-evidence.yml"))

    assert (
        "evidence.review.residual_risk: Field required" in exc_info.value.errors
    )


def test_invalid_approval_evidence_fails() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_workflow_file(fixture_path("invalid-approval-evidence.yml"))

    assert (
        "evidence.approval.scope_confirmed: Field required" in exc_info.value.errors
    )


def test_implementation_cannot_start_before_planning_completes() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_workflow_file(fixture_path("implementation-before-planning.yml"))

    assert (
        "implementation cannot start until planning is completed."
        in exc_info.value.errors
    )


def test_medium_implementation_requires_completed_architecture_check() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_workflow_file(
            fixture_path("medium-implementation-before-architecture-complete.yml")
        )

    assert (
        "MEDIUM risk implementation cannot start until architecture-check is completed."
        in exc_info.value.errors
    )


def test_review_cannot_complete_before_implementation_completes() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_workflow_file(
            fixture_path("review-before-implementation-complete.yml")
        )

    assert (
        "review cannot start until implementation is completed."
        in exc_info.value.errors
    )


def test_qa_cannot_complete_before_review_completes() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_workflow_file(fixture_path("qa-before-review-complete.yml"))

    assert (
        "qa cannot start until review is completed." in exc_info.value.errors
    )


def test_completed_planning_requires_planning_evidence() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_workflow_file(fixture_path("completed-planning-without-evidence.yml"))

    assert (
        "Completed phase 'planning' requires matching evidence block: planning"
        in exc_info.value.errors
    )


def test_completed_planning_requires_planning_contract() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_workflow_file(fixture_path("completed-planning-without-contract.yml"))

    assert (
        "Completed phase 'planning' requires matching contract block: planning"
        in exc_info.value.errors
    )


def test_planning_contract_requires_planning_agent() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_workflow_file(fixture_path("planning-contract-wrong-agent.yml"))

    assert (
        "contracts.planning.owner_agent: Input should be 'planning-agent'"
        in exc_info.value.errors
    )


def test_completed_implementation_requires_implementation_contract() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_workflow_file(
            fixture_path("completed-implementation-without-contract.yml")
        )

    assert (
        "Completed phase 'implementation' requires matching contract block: implementation"
        in exc_info.value.errors
    )


def test_completed_approval_requires_approval_evidence() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_workflow_file(fixture_path("completed-approval-without-evidence.yml"))

    assert (
        "Completed phase 'approval' requires matching evidence block: approval"
        in exc_info.value.errors
    )


def test_risk_exception_requires_approval_metadata() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_workflow_file(fixture_path("risk-exception-without-approval.yml"))

    assert (
        "Override 'risk-exception-1' of type 'risk_exception' requires approved_by and approval_reference."
        in exc_info.value.errors
    )


def test_override_requires_review_or_expiry() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_workflow_file(fixture_path("override-without-review-or-expiry.yml"))

    assert (
        "Override 'phase-bypass-1' must declare exactly one of review_by or expires_on."
        in exc_info.value.errors
    )


def test_runtime_handoff_pending_requires_matching_handoff() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_workflow_file(
            fixture_path("runtime-handoff-pending-without-handoff.yml")
        )

    assert (
        "runtime.status handoff_pending requires an open pending handoff from the current phase."
        in exc_info.value.errors
    )


def test_handoff_requires_concrete_output_artifacts() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_workflow_file(fixture_path("handoff-without-produced-outputs.yml"))

    assert (
        "handoffs.0.produced_outputs must be a non-empty list"
        in exc_info.value.errors
    )


def test_expired_override_requires_revalidation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        validator_module, "_current_date", lambda: validator_module.date(2026, 5, 21)
    )

    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_workflow_file(fixture_path("expired-override.yml"))

    assert (
        "Override 'phase-bypass-1' requires revalidation because review_by has passed."
        in exc_info.value.errors
    )


def test_handoff_cannot_reference_override_requiring_revalidation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        validator_module, "_current_date", lambda: validator_module.date(2026, 5, 21)
    )

    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_workflow_file(fixture_path("handoff-with-expired-override.yml"))

    assert (
        "handoff override reference requires revalidation and cannot remain active: phase-bypass-1"
        in exc_info.value.errors
    )


def test_invalid_risk_level_fails() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_workflow_file(fixture_path("invalid-risk-level.yml"))

    assert "risk_level must be one of: LOW, MEDIUM, HIGH" in exc_info.value.errors


def test_high_risk_without_human_approval_fails() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_workflow_file(fixture_path("high-without-approval.yml"))

    assert "HIGH risk workflows require human approval." in exc_info.value.errors


def test_empty_required_reviews_fails() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_workflow_file(fixture_path("empty-required-reviews.yml"))

    assert "governance.required_reviews must be a non-empty list" in exc_info.value.errors


def test_low_risk_without_review_agent_fails() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_workflow_file(fixture_path("low-missing-review-agent.yml"))

    assert (
        "LOW risk workflows must include required reviews: review-agent"
        in exc_info.value.errors
    )


def test_medium_risk_with_weaker_reviews_fails() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_workflow_file(fixture_path("medium-weaker-reviews.yml"))

    assert (
        "MEDIUM risk workflows must include required reviews: "
        "architecture-agent, qa-agent"
        in exc_info.value.errors
    )


def test_high_risk_with_weaker_reviews_fails() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_workflow_file(fixture_path("high-weaker-reviews.yml"))

    assert (
        "HIGH risk workflows must include required reviews: "
        "architecture-agent, qa-agent"
        in exc_info.value.errors
    )


def test_high_risk_without_approval_evidence_fails() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_workflow_file(fixture_path("high-missing-approval-evidence.yml"))

    assert (
        "HIGH risk workflows must include non-empty approval evidence."
        in exc_info.value.errors
    )


def test_high_risk_with_empty_approval_evidence_fails() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_workflow_file(fixture_path("high-empty-approval-evidence.yml"))

    assert (
        "HIGH risk workflows must include non-empty approval evidence."
        in exc_info.value.errors
    )


def test_high_risk_without_evidence_approval_fails_with_pr_approval_guidance() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_workflow_file(fixture_path("high-missing-evidence-approval.yml"))

    assert (
        "HIGH risk workflows with human approval required must declare evidence.approval.approved_by, evidence.approval.reference, and evidence.approval.scope_confirmed; governance.approval_evidence alone is not sufficient for PR approval validation."
        in exc_info.value.errors
    )


@pytest.mark.parametrize(
    "fixture_name",
    ["high-empty-approved-by.yml", "high-null-approved-by.yml"],
)
def test_high_risk_with_empty_approved_by_fails_with_field_guidance(
    fixture_name: str,
) -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_workflow_file(fixture_path(fixture_name))

    assert (
        "HIGH risk workflows with human approval required must declare evidence.approval.approved_by, evidence.approval.reference, and evidence.approval.scope_confirmed; governance.approval_evidence alone is not sufficient for PR approval validation."
        in exc_info.value.errors
    )


def test_protected_areas_require_high_risk_fails() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_workflow_file(fixture_path("medium-protected-area.yml"))

    assert (
        "Workflows touching protected areas must use HIGH risk."
        in exc_info.value.errors
    )


def test_protected_areas_require_escalation_fails() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_workflow_file(
            fixture_path("high-protected-area-without-escalation.yml")
        )

    assert (
        "Workflows touching protected areas must set escalation_required to true."
        in exc_info.value.errors
    )


def test_malformed_yaml_fails() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_workflow_file(fixture_path("malformed.yml"))

    assert "Invalid YAML" in exc_info.value.errors[0]
