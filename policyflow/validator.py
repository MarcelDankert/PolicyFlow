from __future__ import annotations

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


def _collect_validation_errors(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    workflow = data.get("workflow")
    context = data.get("context")
    governance = data.get("governance")
    execution = data.get("execution")
    evidence = data.get("evidence")

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

    return errors


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


def _phase_started(phase_states: dict[str, str], phase_name: str) -> bool:
    return phase_states.get(phase_name) in {"in_progress", "completed"}


def _phase_completed(phase_states: dict[str, str], phase_name: str) -> bool:
    return phase_states.get(phase_name) == "completed"


def _collect_pull_request_errors(workflow: WorkflowDocument, pr_body: str) -> list[str]:
    errors: list[str] = []
    sections = _parse_markdown_sections(pr_body)

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

    declared_risk_level = _extract_declared_risk_level(sections.get("Governance", ""))
    if not declared_risk_level:
        errors.append(
            "PR body must include Declared risk level in the Governance section."
        )
    elif declared_risk_level != workflow.context.risk_level.value:
        errors.append(
            "PR body Declared risk level must match context.risk_level: "
            f"{workflow.context.risk_level.value}"
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

    return errors


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
