from __future__ import annotations

from datetime import date, timedelta
import re
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
REQUIRED_PHASES_BY_RISK: dict[str, set[str]] = {
    RiskLevel.LOW.value: {"planning", "implementation", "review"},
    RiskLevel.MEDIUM.value: {
        "planning",
        "architecture-check",
        "implementation",
        "review",
        "qa",
    },
    RiskLevel.HIGH.value: {
        "planning",
        "architecture-check",
        "implementation",
        "review",
        "qa",
        "approval",
    },
}
EXPIRING_OVERRIDE_WINDOW_DAYS = 7


def inspect_workflow_file(path: str | Path) -> tuple[WorkflowDocument, list[str]]:
    raw_data = _load_workflow_yaml(Path(path))
    return inspect_workflow_data(raw_data)


def validate_workflow_file(path: str | Path) -> WorkflowDocument:
    workflow, _warnings = inspect_workflow_file(path)
    return workflow


def validate_workflow_data(raw_data: dict[str, Any]) -> WorkflowDocument:
    workflow, _warnings = inspect_workflow_data(raw_data)
    return workflow


def inspect_workflow_data(raw_data: dict[str, Any]) -> tuple[WorkflowDocument, list[str]]:
    normalized_data = normalize_workflow_payload(raw_data)
    errors, warnings = _collect_validation_findings(normalized_data)

    if errors:
        raise WorkflowValidationError(errors)

    try:
        return WorkflowDocument.model_validate(normalized_data), warnings
    except ValidationError as exc:
        raise WorkflowValidationError(_format_pydantic_errors(exc)) from exc


def validate_pull_request(
    workflow_path: str | Path, pr_body_path: str | Path
) -> WorkflowDocument:
    workflow = validate_workflow_file(workflow_path)
    pr_body = _load_markdown_file(Path(pr_body_path))
    errors = _collect_pull_request_errors(workflow, pr_body)

    if errors:
        raise WorkflowValidationError(errors)

    return workflow


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


def _load_markdown_file(path: Path) -> str:
    if not path.exists():
        raise WorkflowValidationError([f"PR body file not found: {path}"])

    return path.read_text(encoding="utf-8")


def _collect_validation_findings(data: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    workflow = data.get("workflow")
    context = data.get("context")
    governance = data.get("governance")
    execution = data.get("execution")
    evidence = data.get("evidence")
    contracts = data.get("contracts")
    overrides = data.get("overrides")
    runtime = data.get("runtime")
    handoffs = data.get("handoffs")
    override_lifecycle = _collect_override_lifecycle_statuses(overrides)

    if not isinstance(workflow, dict):
        errors.append("workflow metadata is required")

    if context.get("workflow_file") in (None, ""):
        errors.append("context.workflow_file is required")

    risk_level = context.get("risk_level")
    if risk_level in (None, ""):
        errors.append("context.risk_level is required")
    elif risk_level not in {level.value for level in RiskLevel}:
        errors.append("risk_level must be one of: LOW, MEDIUM, HIGH")

    _append_confidence_errors(errors, context.get("confidence"))

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

    approval_evidence = governance.get("approval_evidence")
    if risk_level == RiskLevel.HIGH.value and (
        not isinstance(approval_evidence, list) or not approval_evidence
    ):
        errors.append("HIGH risk workflows must include non-empty approval evidence.")

    protected_areas = _normalize_protected_areas(
        governance.get("protected_areas_touched")
    )
    if protected_areas:
        if risk_level != RiskLevel.HIGH.value:
            errors.append("Workflows touching protected areas must use HIGH risk.")
        if governance.get("escalation_required") is not True:
            errors.append(
                "Workflows touching protected areas must set escalation_required to true."
            )

    _append_override_errors(errors, warnings, overrides, override_lifecycle)

    if not isinstance(execution, dict) or execution.get("mode") in (None, ""):
        errors.append("execution.mode is required")

    phases = execution.get("phases") if isinstance(execution, dict) else None
    if phases is None:
        errors.append("execution.phases is required")
    elif not isinstance(phases, list) or not phases:
        errors.append("execution.phases must be a non-empty list")
    elif risk_level in REQUIRED_PHASES_BY_RISK:
        declared_phases = {
            phase.get("phase")
            for phase in phases
            if isinstance(phase, dict) and isinstance(phase.get("phase"), str)
        }
        missing_phases = sorted(REQUIRED_PHASES_BY_RISK[risk_level] - declared_phases)
        if missing_phases:
            missing_phases_text = ", ".join(missing_phases)
            errors.append(
                f"{risk_level} risk workflows must declare execution phases: "
                f"{missing_phases_text}"
            )
        else:
            phase_states = {
                phase.get("phase"): phase.get("state")
                for phase in phases
                if isinstance(phase, dict)
                and isinstance(phase.get("phase"), str)
                and isinstance(phase.get("state"), str)
            }
            _append_transition_errors(errors, risk_level, phase_states)
            _append_completed_evidence_errors(errors, phase_states, evidence)
            _append_completed_contract_errors(errors, phase_states, contracts)
            _append_handoff_errors(
                errors, phase_states, handoffs, overrides, override_lifecycle
            )
            _append_runtime_errors(errors, phase_states, runtime, handoffs)

    return errors, warnings


def _append_confidence_errors(errors: list[str], confidence: Any) -> None:
    if confidence in (None, ""):
        errors.append("context.confidence is required")
        return

    if not isinstance(confidence, dict):
        errors.append("context.confidence must be a mapping")
        return

    for field_name in (
        "planning",
        "implementation",
        "tests",
        "residual_uncertainty",
    ):
        value = confidence.get(field_name)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"context.confidence.{field_name} is required")


def _append_transition_errors(
    errors: list[str], risk_level: str, phase_states: dict[str, str]
) -> None:
    if _phase_started(phase_states, "implementation") and not _phase_completed(
        phase_states, "planning"
    ):
        errors.append("implementation cannot start until planning is completed.")

    if (
        risk_level in {RiskLevel.MEDIUM.value, RiskLevel.HIGH.value}
        and _phase_started(phase_states, "implementation")
        and not _phase_completed(phase_states, "architecture-check")
    ):
        errors.append(
            f"{risk_level} risk implementation cannot start until "
            "architecture-check is completed."
        )

    if _phase_started(phase_states, "review") and not _phase_completed(
        phase_states, "implementation"
    ):
        errors.append("review cannot start until implementation is completed.")

    if _phase_started(phase_states, "qa") and not _phase_completed(
        phase_states, "review"
    ):
        errors.append("qa cannot start until review is completed.")

    if _phase_started(phase_states, "approval") and not _phase_completed(
        phase_states, "qa"
    ):
        errors.append("approval cannot start until qa is completed.")


def _append_completed_evidence_errors(
    errors: list[str], phase_states: dict[str, str], evidence: Any
) -> None:
    evidence_blocks = evidence if isinstance(evidence, dict) else {}
    evidence_phase_map = {
        "planning": "planning",
        "architecture-check": "architecture-check",
        "review": "review",
        "qa": "qa",
        "approval": "approval",
    }

    for phase_name, evidence_key in evidence_phase_map.items():
        if _phase_completed(phase_states, phase_name) and evidence_blocks.get(
            evidence_key
        ) in (None, ""):
            errors.append(
                f"Completed phase '{phase_name}' requires matching evidence block: "
                f"{evidence_key}"
            )


def _append_completed_contract_errors(
    errors: list[str], phase_states: dict[str, str], contracts: Any
) -> None:
    contract_blocks = contracts if isinstance(contracts, dict) else {}
    contract_phase_map = {
        "planning": "planning",
        "architecture-check": "architecture-check",
        "implementation": "implementation",
        "review": "review",
        "qa": "qa",
    }

    for phase_name, contract_key in contract_phase_map.items():
        if _phase_completed(phase_states, phase_name) and contract_blocks.get(
            contract_key
        ) in (None, ""):
            errors.append(
                f"Completed phase '{phase_name}' requires matching contract block: "
                f"{contract_key}"
            )


def _append_handoff_errors(
    errors: list[str],
    phase_states: dict[str, str],
    handoffs: Any,
    overrides: Any,
    override_lifecycle: dict[str, str],
) -> None:
    if not isinstance(handoffs, list):
        return

    override_ids = {
        override.get("id")
        for override in (overrides if isinstance(overrides, list) else [])
        if isinstance(override, dict)
    }

    for index, handoff in enumerate(handoffs):
        if not isinstance(handoff, dict):
            continue

        required_inputs = handoff.get("required_inputs")
        if not isinstance(required_inputs, list) or not required_inputs:
            errors.append(f"handoffs.{index}.required_inputs must be a non-empty list")

        produced_outputs = handoff.get("produced_outputs")
        if not isinstance(produced_outputs, list) or not produced_outputs:
            errors.append(f"handoffs.{index}.produced_outputs must be a non-empty list")

        from_phase = handoff.get("from_phase")
        if isinstance(from_phase, str) and not _phase_completed(phase_states, from_phase):
            errors.append(
                f"handoff from phase '{from_phase}' requires the phase to be completed."
            )

        override_refs = handoff.get("override_refs")
        if isinstance(override_refs, list):
            for override_ref in override_refs:
                if override_ref not in override_ids:
                    errors.append(
                        f"handoff override reference not found in workflow overrides: {override_ref}"
                    )
                elif override_lifecycle.get(override_ref) == "revalidation_required":
                    errors.append(
                        "handoff override reference requires revalidation and cannot "
                        f"remain active: {override_ref}"
                    )


def _append_runtime_errors(
    errors: list[str],
    phase_states: dict[str, str],
    runtime: Any,
    handoffs: Any,
) -> None:
    if not isinstance(runtime, dict):
        return

    status = runtime.get("status")
    current_phase = runtime.get("current_phase")
    active_agent = runtime.get("active_agent")

    if status in {"in_progress", "handoff_pending", "blocked"}:
        if current_phase in (None, ""):
            errors.append("runtime.current_phase is required when runtime.status is active.")
        if active_agent in (None, ""):
            errors.append("runtime.active_agent is required when runtime.status is active.")

    if status == "in_progress" and isinstance(current_phase, str):
        if phase_states.get(current_phase) != "in_progress":
            errors.append(
                "runtime.status in_progress requires runtime.current_phase to be in_progress in execution.phases."
            )

    if status == "blocked":
        if runtime.get("block_reason") in (None, ""):
            errors.append("runtime.block_reason is required when runtime.status is blocked.")
        if isinstance(current_phase, str) and phase_states.get(current_phase) != "blocked":
            errors.append(
                "runtime.status blocked requires runtime.current_phase to be blocked in execution.phases."
            )

    if status == "handoff_pending":
        has_open_handoff = False
        if isinstance(handoffs, list) and isinstance(current_phase, str):
            for handoff in handoffs:
                if not isinstance(handoff, dict):
                    continue
                if (
                    handoff.get("from_phase") == current_phase
                    and handoff.get("status") == "pending"
                ):
                    has_open_handoff = True
                    break
        if not has_open_handoff:
            errors.append(
                "runtime.status handoff_pending requires an open pending handoff from the current phase."
            )
        elif phase_states.get(current_phase) != "completed":
            errors.append(
                "runtime.status handoff_pending requires runtime.current_phase to be completed in execution.phases."
            )


def _phase_started(phase_states: dict[str, str], phase_name: str) -> bool:
    return phase_states.get(phase_name) in {"in_progress", "completed"}


def _phase_completed(phase_states: dict[str, str], phase_name: str) -> bool:
    return phase_states.get(phase_name) == "completed"


def _collect_pull_request_errors(workflow: WorkflowDocument, pr_body: str) -> list[str]:
    errors: list[str] = []
    sections = _parse_markdown_sections(pr_body)
    governance_section = sections.get("Governance", "")

    linked_issue = sections.get("Linked Issue", "").strip()
    if not linked_issue:
        errors.append("PR body must include a non-empty Linked Issue section.")

    workflow_file = _extract_workflow_file(sections.get("Workflow File", ""))
    if not workflow_file:
        errors.append("PR body must include a Workflow File entry.")
    elif workflow_file != workflow.context.workflow_file:
        errors.append(
            "PR body Workflow File must match context.workflow_file: "
            f"{workflow.context.workflow_file}"
        )

    declared_risk_level = _extract_declared_risk_level(governance_section)
    if not declared_risk_level:
        errors.append(
            "PR body must include Declared risk level in the Governance section."
        )
    elif declared_risk_level != workflow.context.risk_level.value:
        errors.append(
            "PR body Declared risk level must match context.risk_level: "
            f"{workflow.context.risk_level.value}"
        )

    if _extract_governance_value(governance_section, "Confidence summary") is None:
        errors.append(
            "PR body must include Confidence summary in the Governance section."
        )

    if not _has_workflow_confirmation(sections.get("Confirmation", "")):
        errors.append(
            "PR body must confirm that the linked workflow file governed this change."
        )

    if not _has_workflow_first_confirmation(sections.get("Confirmation", "")):
        errors.append(
            "PR body must confirm that the workflow file existed before implementation "
            "and governed the work from the start."
        )

    if not _has_workflow_lock_confirmation(sections.get("Confirmation", "")):
        errors.append(
            "PR body must confirm that scope, non-goals, and risk were fixed in the "
            "workflow before implementation started."
        )

    if not _has_workflow_phase_confirmation(sections.get("Confirmation", "")):
        errors.append(
            "PR body must confirm that required workflow phases were executed as "
            "visible working steps, not only documented after the fact."
        )

    _append_pr_evidence_reference_errors(
        errors, workflow, sections.get("Evidence", "")
    )
    _append_pr_human_approval_errors(errors, workflow, governance_section)
    _append_pr_override_reference_errors(
        errors, workflow, sections.get("Overrides", "")
    )

    return errors


def _append_pr_evidence_reference_errors(
    errors: list[str], workflow: WorkflowDocument, evidence_section: str
) -> None:
    if workflow.evidence is None:
        return

    expected_references = {
        "Planning evidence": (
            workflow.evidence.planning is not None,
            "evidence.planning",
        ),
        "Architecture evidence": (
            workflow.evidence.architecture_check is not None,
            "evidence.architecture-check",
        ),
        "Review evidence": (
            workflow.evidence.review is not None,
            "evidence.review",
        ),
        "QA evidence": (
            workflow.evidence.qa is not None,
            "evidence.qa",
        ),
        "Approval evidence": (
            workflow.evidence.approval is not None,
            "evidence.approval",
        ),
    }

    for label, (required, expected_reference) in expected_references.items():
        if not required:
            continue

        actual_reference = _extract_evidence_reference(evidence_section, label)
        if actual_reference is None:
            errors.append(
                f"PR body must reference workflow evidence block: {expected_reference}"
            )
        elif actual_reference != expected_reference:
            errors.append(
                f"PR body {label} must reference workflow {expected_reference}"
            )


def _append_pr_override_reference_errors(
    errors: list[str], workflow: WorkflowDocument, overrides_section: str
) -> None:
    if not workflow.overrides:
        return

    for override in workflow.overrides:
        actual_type = _extract_override_type(overrides_section, override.id)
        if actual_type is None:
            errors.append(f"PR body must reference workflow override: {override.id}")
            continue
        if actual_type != override.type:
            errors.append(
                f"PR body Override {override.id} must declare type {override.type}"
            )
        if override.approved_by is not None:
            actual_login = _extract_override_field(
                overrides_section, override.id, "Approved by login"
            )
            if actual_login is None:
                errors.append(
                    f"PR body Override {override.id} must declare approved_by login "
                    f"{override.approved_by}"
                )
            elif actual_login != override.approved_by:
                errors.append(
                    f"PR body Override {override.id} must declare approved_by login "
                    f"{override.approved_by}"
                )
        if override.approval_reference is not None:
            actual_reference = _extract_override_field(
                overrides_section, override.id, "Approval reference"
            )
            if actual_reference is None:
                errors.append(
                    f"PR body Override {override.id} must declare approval reference "
                    f"{override.approval_reference}"
                )
            elif actual_reference != override.approval_reference:
                errors.append(
                    f"PR body Override {override.id} must declare approval reference "
                    f"{override.approval_reference}"
                )


def _append_pr_human_approval_errors(
    errors: list[str], workflow: WorkflowDocument, governance_section: str
) -> None:
    if not workflow.governance.human_approval_required:
        return

    approval_evidence = workflow.evidence.approval if workflow.evidence else None
    if approval_evidence is None:
        errors.append(
            "Workflow with human approval required must declare evidence.approval."
        )
        return

    expected_login = approval_evidence.approved_by
    if expected_login in (None, ""):
        errors.append(
            "Workflow with human approval required must declare "
            "evidence.approval.approved_by as a GitHub login."
        )
    else:
        actual_login = _extract_governance_value(
            governance_section, "Human approval login if required"
        )
        if actual_login is None or actual_login != expected_login:
            errors.append(
                f"PR body must declare Human approval login if required: "
                f"{expected_login}"
            )

    expected_reference = approval_evidence.reference
    actual_reference = _extract_governance_value(
        governance_section, "Human approval reference if required"
    )
    if actual_reference is None or actual_reference != expected_reference:
        errors.append(
            f"PR body must declare Human approval reference if required: "
            f"{expected_reference}"
        )


def _parse_markdown_sections(markdown: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current_heading: str | None = None
    current_lines: list[str] = []

    for line in markdown.splitlines():
        if line.startswith("## "):
            if current_heading is not None:
                sections[current_heading] = "\n".join(current_lines).strip()
            current_heading = line[3:].strip()
            current_lines = []
            continue

        if current_heading is not None:
            current_lines.append(line)

    if current_heading is not None:
        sections[current_heading] = "\n".join(current_lines).strip()

    return sections


def _extract_workflow_file(section_text: str) -> str | None:
    for raw_line in section_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        line = re.sub(r"^-+\s*", "", line)
        line = line.strip("` ")
        if line:
            return line
    return None


def _extract_declared_risk_level(section_text: str) -> str | None:
    match = re.search(
        r"^- Declared risk level:\s*(LOW|MEDIUM|HIGH)\s*$",
        section_text,
        re.MULTILINE,
    )
    if match is None:
        return None
    return match.group(1)


def _extract_evidence_reference(section_text: str, label: str) -> str | None:
    match = re.search(
        rf"^- {re.escape(label)}:\s*([^\s]+)\s*$",
        section_text,
        re.MULTILINE,
    )
    if match is None:
        return None
    return match.group(1).strip("` ")


def _extract_override_type(section_text: str, override_id: str) -> str | None:
    field_value = _extract_override_field(section_text, override_id, "Override type")
    if field_value is None:
        return None
    return field_value.strip("` ")


def _extract_override_field(
    section_text: str, override_id: str, field_label: str
) -> str | None:
    lines = section_text.splitlines()
    for index, raw_line in enumerate(lines):
        match = re.match(r"^- Override ID:\s*([^\s]+)\s*$", raw_line.strip())
        if match is None or match.group(1) != override_id:
            continue
        for candidate in lines[index + 1 :]:
            candidate = candidate.strip()
            if not candidate:
                continue
            field_match = re.match(
                rf"^- {re.escape(field_label)}:\s*(.+?)\s*$", candidate
            )
            if field_match is not None:
                return field_match.group(1).strip("` ")
            if candidate.startswith("- Override ID:"):
                break
        return None
    return None


def _extract_governance_value(section_text: str, label: str) -> str | None:
    match = re.search(
        rf"^- {re.escape(label)}:\s*(.+?)\s*$",
        section_text,
        re.MULTILINE,
    )
    if match is None:
        return None
    value = match.group(1).strip("` ")
    if not value:
        return None
    return value


def _has_workflow_confirmation(section_text: str) -> bool:
    return bool(
        re.search(
            r"^- \[[xX]\] The linked workflow file governed this change\s*$",
            section_text,
            re.MULTILINE,
        )
    )


def _has_workflow_first_confirmation(section_text: str) -> bool:
    return bool(
        re.search(
            r"^- \[[xX]\] The workflow file existed before implementation and governed the work from the start\s*$",
            section_text,
            re.MULTILINE,
        )
    )


def _has_workflow_lock_confirmation(section_text: str) -> bool:
    return bool(
        re.search(
            r"^- \[[xX]\] Scope, non-goals, and risk were fixed in the workflow before implementation started\s*$",
            section_text,
            re.MULTILINE,
        )
    )


def _has_workflow_phase_confirmation(section_text: str) -> bool:
    return bool(
        re.search(
            r"^- \[[xX]\] Required workflow phases were executed as visible working steps, not only documented after the fact\s*$",
            section_text,
            re.MULTILINE,
        )
    )


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


def _append_override_errors(
    errors: list[str],
    warnings: list[str],
    overrides: Any,
    override_lifecycle: dict[str, str],
) -> None:
    if not isinstance(overrides, list):
        return

    for override in overrides:
        if not isinstance(override, dict):
            continue

        override_id = str(override.get("id", "")).strip()
        override_type = str(override.get("type", "")).strip()

        has_review_by = override.get("review_by") not in (None, "")
        has_expires_on = override.get("expires_on") not in (None, "")
        if has_review_by == has_expires_on:
            errors.append(
                f"Override '{override_id}' must declare exactly one of review_by or expires_on."
            )

        if override_type in {"risk_exception", "approval_bypass"} and (
            override.get("approved_by") in (None, "")
            or override.get("approval_reference") in (None, "")
        ):
            errors.append(
                f"Override '{override_id}' of type '{override_type}' requires approved_by and approval_reference."
            )

        lifecycle_status = override_lifecycle.get(override_id)
        if lifecycle_status == "expiring":
            warnings.append(
                f"Override '{override_id}' is expiring soon and should be revalidated by "
                f"{_override_deadline_text(override)}."
            )
        elif lifecycle_status == "revalidation_required":
            errors.append(
                f"Override '{override_id}' requires revalidation because "
                f"{_override_deadline_field(override)} has passed."
            )


def _collect_override_lifecycle_statuses(overrides: Any) -> dict[str, str]:
    if not isinstance(overrides, list):
        return {}

    statuses: dict[str, str] = {}
    today = _current_date()
    expiring_threshold = today + timedelta(days=EXPIRING_OVERRIDE_WINDOW_DAYS)

    for override in overrides:
        if not isinstance(override, dict):
            continue

        override_id = str(override.get("id", "")).strip()
        if not override_id:
            continue

        deadline = _override_deadline(override)
        if deadline is None:
            continue

        if deadline < today:
            statuses[override_id] = "revalidation_required"
        elif deadline <= expiring_threshold:
            statuses[override_id] = "expiring"
        else:
            statuses[override_id] = "active"

    return statuses


def _override_deadline(override: dict[str, Any]) -> date | None:
    review_by = _coerce_date(override.get("review_by"))
    expires_on = _coerce_date(override.get("expires_on"))

    if review_by is not None and expires_on is None:
        return review_by
    if expires_on is not None and review_by is None:
        return expires_on
    return None


def _override_deadline_field(override: dict[str, Any]) -> str:
    if override.get("review_by") not in (None, ""):
        return "review_by"
    return "expires_on"


def _override_deadline_text(override: dict[str, Any]) -> str:
    deadline = _override_deadline(override)
    if deadline is None:
        return "the declared review window"
    return deadline.isoformat()


def _coerce_date(value: Any) -> date | None:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
    return None


def _current_date() -> date:
    return date.today()
