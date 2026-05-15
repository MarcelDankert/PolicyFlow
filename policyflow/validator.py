from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from policyflow.exceptions import WorkflowValidationError
from policyflow.models import RiskLevel, WorkflowDocument
from policyflow.schemas import normalize_workflow_payload


REQUIRED_REVIEWS_BY_RISK: dict[str, set[str]] = {
    RiskLevel.LOW.value: {"review-agent"},
    RiskLevel.MEDIUM.value: {"architecture-agent", "review-agent", "qa-agent"},
    RiskLevel.HIGH.value: {"architecture-agent", "review-agent", "qa-agent"},
}


def validate_workflow_file(path: str | Path) -> WorkflowDocument:
    raw_data = _load_workflow_yaml(Path(path))
    normalized_data = normalize_workflow_payload(raw_data)
    errors = _collect_validation_errors(normalized_data)

    if errors:
        raise WorkflowValidationError(errors)

    try:
        return WorkflowDocument.model_validate(normalized_data)
    except ValidationError as exc:
        raise WorkflowValidationError(_format_pydantic_errors(exc)) from exc


def _load_workflow_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise WorkflowValidationError([f"Workflow file not found: {path}"])

    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except yaml.YAMLError as exc:
        raise WorkflowValidationError([f"Invalid YAML: {exc}"]) from exc

    if not isinstance(data, dict):
        raise WorkflowValidationError(
            ["Workflow file must contain a top-level YAML mapping"]
        )

    return data


def _collect_validation_errors(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    workflow = data.get("workflow")
    context = data.get("context")
    governance = data.get("governance")

    if not isinstance(workflow, dict):
        errors.append("workflow metadata is required")

    if context.get("workflow_file") in (None, ""):
        errors.append("context.workflow_file is required")

    risk_level = context.get("risk_level")
    if risk_level in (None, ""):
        errors.append("context.risk_level is required")
    elif risk_level not in {level.value for level in RiskLevel}:
        errors.append("risk_level must be one of: LOW, MEDIUM, HIGH")

    required_reviews = governance.get("required_reviews")
    if required_reviews is None:
        errors.append("governance.required_reviews is required")
    elif not isinstance(required_reviews, list) or not required_reviews:
        errors.append("governance.required_reviews must be a non-empty list")
    elif risk_level in REQUIRED_REVIEWS_BY_RISK:
        required_reviews_set = {
            review for review in required_reviews if isinstance(review, str)
        }
        missing_reviews = sorted(
            REQUIRED_REVIEWS_BY_RISK[risk_level] - required_reviews_set
        )
        if missing_reviews:
            missing_reviews_text = ", ".join(missing_reviews)
            errors.append(
                f"{risk_level} risk workflows must include required reviews: "
                f"{missing_reviews_text}"
            )

    if risk_level == RiskLevel.HIGH.value and governance.get(
        "human_approval_required"
    ) is not True:
        errors.append("HIGH risk workflows require human approval.")

    protected_areas_touched = governance.get("protected_areas_touched")
    protected_areas = _normalize_protected_areas(protected_areas_touched)
    if protected_areas:
        if risk_level != RiskLevel.HIGH.value:
            errors.append("Workflows touching protected areas must use HIGH risk.")
        if governance.get("escalation_required") is not True:
            errors.append(
                "Workflows touching protected areas must set escalation_required to true."
            )

    approval_evidence = governance.get("approval_evidence")
    if risk_level == RiskLevel.HIGH.value and (
        not isinstance(approval_evidence, list) or not approval_evidence
    ):
        errors.append("HIGH risk workflows must include non-empty approval evidence.")

    return errors


def _format_pydantic_errors(exc: ValidationError) -> list[str]:
    messages: list[str] = []
    for error in exc.errors():
        location = ".".join(str(part) for part in error["loc"])
        messages.append(f"{location}: {error['msg']}")
    return messages


def _normalize_protected_areas(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []

    normalized = []
    for item in value:
        if not isinstance(item, str):
            continue
        if item.strip().lower() == "none":
            continue
        normalized.append(item)
    return normalized
