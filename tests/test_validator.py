from pathlib import Path

import pytest

from policyflow.exceptions import WorkflowValidationError
from policyflow.validator import validate_workflow_file


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def fixture_path(name: str) -> Path:
    return FIXTURES_DIR / name


def test_valid_low_workflow_passes() -> None:
    result = validate_workflow_file(fixture_path("valid-low.yml"))

    assert result.context.workflow_file == "workflows/examples/valid-low.yml"
    assert result.context.risk_level == "LOW"
    assert result.governance.required_reviews == ["review-agent"]
    assert result.governance.human_approval_required is False


def test_valid_medium_workflow_passes() -> None:
    result = validate_workflow_file(fixture_path("valid-medium.yml"))

    assert result.context.risk_level == "MEDIUM"
    assert result.governance.required_reviews == [
        "architecture-agent",
        "review-agent",
        "qa-agent",
    ]


def test_valid_high_workflow_passes() -> None:
    result = validate_workflow_file(fixture_path("valid-high.yml"))

    assert result.context.risk_level == "HIGH"
    assert result.governance.human_approval_required is True
    assert result.governance.escalation_required is True
    assert result.governance.protected_areas_touched == ["database schema"]
    assert result.governance.approval_evidence == [
        "approved in architecture review"
    ]


def test_valid_java_upgrade_workflow_passes() -> None:
    result = validate_workflow_file(fixture_path("valid-java-upgrade.yml"))

    assert result.workflow.type == "java-upgrade"
    assert result.context.source_java_version == 11
    assert result.context.target_java_version == 17
    assert result.context.risk_level == "MEDIUM"


def test_root_level_fallback_fields_are_accepted() -> None:
    result = validate_workflow_file(fixture_path("valid-root-fallback.yml"))

    assert result.context.workflow_file == "workflows/examples/root-fallback.yml"
    assert result.context.risk_level == "LOW"
    assert result.governance.required_reviews == ["review-agent"]


def test_missing_risk_level_fails() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_workflow_file(fixture_path("missing-risk-level.yml"))

    assert "context.risk_level is required" in exc_info.value.errors


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


def test_java_upgrade_requires_source_version() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_workflow_file(fixture_path("java-upgrade-missing-source.yml"))

    assert "context.source_java_version is required for java-upgrade workflows." in (
        exc_info.value.errors
    )


def test_java_upgrade_requires_target_version() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_workflow_file(fixture_path("java-upgrade-missing-target.yml"))

    assert "context.target_java_version is required for java-upgrade workflows." in (
        exc_info.value.errors
    )


def test_java_upgrade_requires_integer_versions() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_workflow_file(fixture_path("java-upgrade-invalid-version.yml"))

    assert "context.source_java_version must be a valid integer Java version." in (
        exc_info.value.errors
    )


def test_java_upgrade_requires_lts_target_version() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_workflow_file(fixture_path("java-upgrade-non-lts-target.yml"))

    assert (
        "context.target_java_version must be one of the supported LTS targets: "
        "17, 21, 25."
    ) in exc_info.value.errors


def test_java_upgrade_requires_forward_migration() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_workflow_file(fixture_path("java-upgrade-target-not-greater.yml"))

    assert (
        "context.target_java_version must be greater than "
        "context.source_java_version."
    ) in exc_info.value.errors


def test_malformed_yaml_fails() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_workflow_file(fixture_path("malformed.yml"))

    assert "Invalid YAML" in exc_info.value.errors[0]
