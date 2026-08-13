from __future__ import annotations

from datetime import date, timedelta
from typing import Callable

from policyflow.models import (
    ValidationDecision,
    ValidationFindingV2,
    ValidationResultV2,
    V2EvidenceStatus,
    V2EvidenceType,
    V2OverrideType,
    V2RiskLevel,
    WorkflowDocumentV2,
)


EXPIRING_OVERRIDE_WINDOW_DAYS = 7


def evaluate_workflow_v2(
    workflow: WorkflowDocumentV2,
    *,
    allow_pending_human_approval: bool = False,
    today: Callable[[], date] = date.today,
) -> ValidationResultV2:
    errors: list[ValidationFindingV2] = []
    warnings: list[ValidationFindingV2] = []

    _append_evidence_errors(errors, workflow)
    _append_human_approval_findings(
        errors,
        warnings,
        workflow,
        allow_pending_human_approval=allow_pending_human_approval,
    )
    _append_override_findings(errors, warnings, workflow, today=today)

    if errors:
        decision = ValidationDecision.BLOCK
    elif warnings:
        decision = ValidationDecision.WARN
    else:
        decision = ValidationDecision.PASS

    return ValidationResultV2(
        decision=decision,
        merge_ready=decision == ValidationDecision.PASS,
        workflow=workflow,
        errors=errors,
        warnings=warnings,
    )


def _append_evidence_errors(
    errors: list[ValidationFindingV2], workflow: WorkflowDocumentV2
) -> None:
    evidence_by_id = {}
    for index, evidence in enumerate(workflow.evidence):
        if evidence.id in evidence_by_id:
            errors.append(
                ValidationFindingV2(
                    code="duplicate_evidence_id",
                    path=f"evidence.{index}.id",
                    message=f"Evidence id '{evidence.id}' must be unique.",
                )
            )
        evidence_by_id[evidence.id] = evidence

        if evidence.status in {V2EvidenceStatus.FAILED, V2EvidenceStatus.MISSING}:
            errors.append(
                ValidationFindingV2(
                    code="blocking_evidence_status",
                    path=f"evidence.{index}.status",
                    message=(
                        f"Evidence '{evidence.id}' has blocking status "
                        f"{evidence.status.value}."
                    ),
                )
            )

    required_types = _required_evidence_types(workflow)
    present_non_blocking_types = {
        evidence.type
        for evidence in workflow.evidence
        if evidence.status
        not in {V2EvidenceStatus.FAILED, V2EvidenceStatus.MISSING}
    }

    for evidence_type in sorted(required_types - present_non_blocking_types):
        errors.append(
            ValidationFindingV2(
                code="missing_required_evidence",
                path="evidence",
                message=(
                    f"Required evidence type '{evidence_type.value}' is missing "
                    "or has blocking status."
                ),
            )
        )


def _append_human_approval_findings(
    errors: list[ValidationFindingV2],
    warnings: list[ValidationFindingV2],
    workflow: WorkflowDocumentV2,
    *,
    allow_pending_human_approval: bool,
) -> None:
    if not workflow.governance.human_approval_required:
        return

    approval_evidence = [
        evidence
        for evidence in workflow.evidence
        if evidence.type == V2EvidenceType.APPROVAL
    ]
    passed_approval = [
        evidence
        for evidence in approval_evidence
        if evidence.status == V2EvidenceStatus.PASSED
    ]
    pending_approval = [
        evidence
        for evidence in approval_evidence
        if evidence.status == V2EvidenceStatus.PENDING
    ]

    if passed_approval:
        return

    if allow_pending_human_approval and pending_approval:
        warnings.append(
            ValidationFindingV2(
                code="pending_human_approval",
                path="evidence",
                message=(
                    "Human approval is required and currently pending; merge "
                    "readiness remains false until approval evidence passes."
                ),
            )
        )
        return

    errors.append(
        ValidationFindingV2(
            code="missing_human_approval",
            path="evidence",
            message="Human approval is required but no passed approval evidence is present.",
        )
    )


def _append_override_findings(
    errors: list[ValidationFindingV2],
    warnings: list[ValidationFindingV2],
    workflow: WorkflowDocumentV2,
    *,
    today: Callable[[], date],
) -> None:
    current_date = today()
    expiring_threshold = current_date + timedelta(days=EXPIRING_OVERRIDE_WINDOW_DAYS)

    for index, override in enumerate(workflow.overrides):
        path = f"overrides.{index}"
        has_review_by = override.review_by is not None
        has_expires_on = override.expires_on is not None
        if has_review_by == has_expires_on:
            errors.append(
                ValidationFindingV2(
                    code="invalid_override_lifecycle",
                    path=path,
                    message=(
                        f"Override '{override.id}' must declare exactly one of "
                        "review_by or expires_on."
                    ),
                )
            )

        if override.type in {
            V2OverrideType.RISK_EXCEPTION,
            V2OverrideType.APPROVAL_EXCEPTION,
            V2OverrideType.EVIDENCE_EXCEPTION,
        } and (not override.approved_by or not override.approval_ref):
            errors.append(
                ValidationFindingV2(
                    code="missing_override_approval",
                    path=path,
                    message=(
                        f"Override '{override.id}' of type "
                        f"'{override.type.value}' requires approved_by and "
                        "approval_ref."
                    ),
                )
            )

        deadline = override.review_by or override.expires_on
        if deadline is None:
            continue
        deadline_field = "review_by" if override.review_by is not None else "expires_on"

        if deadline < current_date:
            errors.append(
                ValidationFindingV2(
                    code="expired_override",
                    path=f"{path}.{deadline_field}",
                    message=(
                        f"Override '{override.id}' is expired because "
                        f"{deadline_field} has passed."
                    ),
                )
            )
        elif deadline <= expiring_threshold:
            warnings.append(
                ValidationFindingV2(
                    code="expiring_override",
                    path=f"{path}.{deadline_field}",
                    message=(
                        f"Override '{override.id}' is still valid but expires "
                        f"or requires review by {deadline.isoformat()}."
                    ),
                )
            )


def _required_evidence_types(workflow: WorkflowDocumentV2) -> set[V2EvidenceType]:
    required = {V2EvidenceType.TEST}

    if workflow.governance.required_reviews:
        required.add(V2EvidenceType.REVIEW)

    if workflow.risk.level in {V2RiskLevel.MEDIUM, V2RiskLevel.HIGH}:
        required.add(V2EvidenceType.REVIEW)

    if workflow.risk.level == V2RiskLevel.HIGH or workflow.risk.protected_areas:
        required.add(V2EvidenceType.SECURITY)

    if workflow.governance.human_approval_required:
        required.add(V2EvidenceType.APPROVAL)

    return required
