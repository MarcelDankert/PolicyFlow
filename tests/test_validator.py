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


def test_malformed_yaml_fails() -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        validate_workflow_file(fixture_path("malformed.yml"))

    assert "Invalid YAML" in exc_info.value.errors[0]
