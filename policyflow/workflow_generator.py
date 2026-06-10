from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from policyflow.consumer_config import load_consumer_config
from policyflow.exceptions import WorkflowValidationError
from policyflow.validator import validate_workflow_file


SUPPORTED_WORKFLOW_TYPES = {
    "feature": "features",
    "bugfix": "bugfixes",
    "architecture-change": "architecture-changes",
    "low-risk": "features",
}
SUPPORTED_RISK_LEVELS = {"LOW", "MEDIUM", "HIGH"}


@dataclass
class WorkflowGenerationResult:
    created: list[str] = field(default_factory=list)
    overwritten: list[str] = field(default_factory=list)
    would_create: list[str] = field(default_factory=list)
    path: str = ""


def create_workflow_instance(
    target: str | Path,
    *,
    workflow_type: str,
    workflow_id: str,
    risk_level: str,
    dry_run: bool = False,
    force: bool = False,
) -> WorkflowGenerationResult:
    target_root = Path(target)
    normalized_type = _normalize_workflow_type(workflow_type)
    normalized_risk = risk_level.upper()
    if normalized_risk not in SUPPORTED_RISK_LEVELS:
        raise WorkflowValidationError(["risk must be one of: LOW, MEDIUM, HIGH"])

    config = load_consumer_config(target_root / "policyflow.yml")
    relative_path = _workflow_path(config.paths.workflows, normalized_type, workflow_id)
    destination = target_root / relative_path
    result = WorkflowGenerationResult(path=relative_path.as_posix())

    if dry_run:
        result.would_create.append(relative_path.as_posix())
        return result

    if destination.exists() and not force:
        raise WorkflowValidationError(
            [f"Workflow file already exists: {relative_path.as_posix()}"]
        )

    payload = _workflow_payload(normalized_type, workflow_id, normalized_risk, relative_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    existed = destination.exists()
    destination.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    validate_workflow_file(destination)

    if existed:
        result.overwritten.append(relative_path.as_posix())
    else:
        result.created.append(relative_path.as_posix())
    return result


def _normalize_workflow_type(workflow_type: str) -> str:
    normalized = workflow_type.strip().lower()
    if normalized not in SUPPORTED_WORKFLOW_TYPES:
        raise WorkflowValidationError(
            [
                "workflow type must be one of: "
                + ", ".join(sorted(SUPPORTED_WORKFLOW_TYPES))
            ]
        )
    if normalized == "low-risk":
        return "feature"
    return normalized


def _workflow_path(workflows_root: Path, workflow_type: str, workflow_id: str) -> Path:
    if not workflow_id.strip():
        raise WorkflowValidationError(["workflow id is required"])
    if Path(workflow_id).name != workflow_id or workflow_id != workflow_id.strip():
        raise WorkflowValidationError(
            ["workflow id must be a filename-safe id without path separators"]
        )
    directory = SUPPORTED_WORKFLOW_TYPES[workflow_type]
    return workflows_root / directory / f"{workflow_id}.yml"


def _workflow_payload(
    workflow_type: str, workflow_id: str, risk_level: str, workflow_path: Path
) -> dict:
    phases = _phases_for_risk(risk_level)
    payload = {
        "workflow": {
            "id": workflow_id,
            "type": workflow_type,
        },
        "context": {
            "workflow_file": workflow_path.as_posix(),
            "risk_level": risk_level,
            "confidence": {
                "planning": "Scope, non-goals, and risk are fixed before implementation.",
                "implementation": "Implementation is bounded to the generated workflow scope.",
                "tests": "Validation starts with policyflow validate for this workflow.",
                "residual_uncertainty": "Review must confirm project-specific assumptions.",
            },
        },
        "governance": _governance_for_risk(risk_level),
        "execution": {
            "mode": "strict",
            "phases": [{"phase": phase, "state": _initial_state(phase)} for phase in phases],
        },
        "evidence": _evidence_for_risk(risk_level),
        "contracts": _contracts_for_risk(risk_level),
        "overrides": [],
        "runtime": {
            "status": "idle",
            "current_phase": None,
            "active_agent": None,
            "last_transition": "workflow generated",
            "block_reason": None,
        },
        "handoffs": [],
    }
    return payload


def _phases_for_risk(risk_level: str) -> list[str]:
    if risk_level == "LOW":
        return ["planning", "implementation", "review"]
    if risk_level == "MEDIUM":
        return ["planning", "architecture-check", "implementation", "review", "qa"]
    return ["planning", "architecture-check", "implementation", "review", "qa", "approval"]


def _initial_state(phase: str) -> str:
    if phase in {"planning", "architecture-check"}:
        return "completed"
    return "pending"


def _governance_for_risk(risk_level: str) -> dict:
    if risk_level == "LOW":
        return {
            "required_reviews": ["review-agent"],
            "human_approval_required": False,
            "escalation_required": False,
            "protected_areas_touched": ["none"],
        }
    if risk_level == "MEDIUM":
        return {
            "required_reviews": ["architecture-agent", "review-agent", "qa-agent"],
            "human_approval_required": False,
            "escalation_required": False,
            "protected_areas_touched": ["none"],
        }
    return {
        "required_reviews": [
            "architecture-agent",
            "review-agent",
            "qa-agent",
            "human approval",
        ],
        "human_approval_required": True,
        "escalation_required": True,
        "protected_areas_touched": ["governance"],
        "approval_evidence": ["Generated HIGH-risk workflow requires human approval."],
    }


def _evidence_for_risk(risk_level: str) -> dict:
    evidence = {
        "planning": {
            "summary": "Generated workflow scope and non-goals were locked before implementation.",
            "scope_locked": ["generated workflow scope"],
            "non_goals_locked": ["no out-of-scope changes"],
            "risk_rationale": f"{risk_level} risk selected during workflow generation.",
        }
    }
    if risk_level in {"MEDIUM", "HIGH"}:
        evidence["architecture-check"] = {
            "decision": "Architecture check completed for generated workflow start.",
            "constraints": ["keep implementation inside generated scope"],
            "approval_path": "architecture-agent review",
        }
    if risk_level == "HIGH":
        evidence["approval"] = {
            "approved_by": "human-approval-required",
            "reference": "GENERATED-HIGH-RISK-APPROVAL",
            "scope_confirmed": True,
        }
    return evidence


def _contracts_for_risk(risk_level: str) -> dict:
    contracts = {
        "planning": {
            "owner_agent": "planning-agent",
            "issue_brief": "Generated workflow instance.",
            "acceptance_criteria": ["workflow validates"],
            "approved_scope": ["generated workflow scope"],
            "non_goals": ["no out-of-scope changes"],
            "initial_risk_level": risk_level,
            "protected_areas_touched": ["none"] if risk_level != "HIGH" else ["governance"],
            "confidence_summary": "Generated workflow is ready for project-specific refinement.",
            "escalation_flags": ["none"] if risk_level != "HIGH" else ["human approval required"],
        }
    }
    if risk_level in {"MEDIUM", "HIGH"}:
        contracts["architecture-check"] = {
            "owner_agent": "architecture-agent",
            "architecture_assessment": "Generated workflow architecture path is ready for implementation.",
            "approved_scope": ["generated workflow scope"],
            "module_boundaries": ["project-specific modules to be confirmed"],
            "contract_impact": "Project-specific contract impact must be confirmed before implementation.",
            "risk_review_decision": f"{risk_level} risk path approved for generated workflow.",
            "required_reviews": _governance_for_risk(risk_level)["required_reviews"],
            "implementation_constraints": ["keep implementation inside generated scope"],
        }
    return contracts
