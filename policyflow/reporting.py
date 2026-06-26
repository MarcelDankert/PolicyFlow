from __future__ import annotations

from pathlib import Path
from typing import Any

from policyflow.exceptions import WorkflowValidationError
from policyflow.runtime import load_workflow_raw
from policyflow.validator import (
    _collect_override_lifecycle_statuses,
    inspect_workflow_file,
)


def workflow_status(path: Path) -> dict[str, Any]:
    workflow, warnings = inspect_workflow_file(path)
    raw = load_workflow_raw(path)
    phase_states = _phase_states(raw)
    runtime = workflow.runtime
    handoffs = workflow.handoffs or []
    open_handoffs = [handoff for handoff in handoffs if handoff.status == "pending"]
    override_statuses = _override_statuses(raw)
    blockers: list[str] = []

    if runtime and runtime.status == "blocked" and runtime.block_reason:
        blockers.append(runtime.block_reason)

    merge_ready = _is_merge_ready(
        workflow.context.risk_level.value,
        phase_states,
        runtime.status.value if runtime else "idle",
        override_statuses,
        blockers,
    )

    current_phase = runtime.current_phase.value if runtime and runtime.current_phase else None
    runtime_status = runtime.status.value if runtime else "idle"
    active_agent = runtime.active_agent if runtime else None

    return {
        "path": str(path),
        "workflow_id": workflow.workflow.id,
        "risk_level": workflow.context.risk_level.value,
        "current_phase": current_phase,
        "runtime_status": runtime_status,
        "active_agent": active_agent,
        "open_handoffs": len(open_handoffs),
        "handoffs": [
            {
                "from_phase": handoff.from_phase.value,
                "to_phase": handoff.to_phase.value,
                "status": handoff.status.value,
                "required_inputs": handoff.required_inputs,
                "produced_outputs": handoff.produced_outputs,
            }
            for handoff in open_handoffs
        ],
        "override_statuses": override_statuses,
        "blocked": bool(blockers),
        "blockers": blockers,
        "warnings": warnings,
        "errors": [],
        "valid": True,
        "merge_ready": merge_ready,
        "loop_governance": _loop_governance_summary(raw, []),
        "evaluation": _evaluation_summary(raw, []),
    }


def audit_directory(directory: Path) -> dict[str, Any]:
    workflows: list[dict[str, Any]] = []

    for path in sorted(directory.rglob("*.yml")):
        try:
            workflows.append(workflow_status(path))
        except WorkflowValidationError as exc:
            raw = _load_invalid_workflow_raw(path)
            workflows.append(
                {
                    "path": str(path),
                    "workflow_id": None,
                    "risk_level": None,
                    "current_phase": None,
                    "runtime_status": "invalid",
                    "active_agent": None,
                    "open_handoffs": 0,
                    "handoffs": [],
                    "override_statuses": {"active": 0, "expiring": 0, "revalidation_required": 0},
                    "blocked": False,
                    "blockers": [],
                    "warnings": [],
                    "errors": exc.errors,
                    "valid": False,
                    "merge_ready": False,
                    "loop_governance": _loop_governance_summary(raw, exc.errors),
                    "evaluation": _evaluation_summary(raw, exc.errors),
                }
            )

    return {"directory": str(directory), "workflows": workflows}


def status_lines(status: dict[str, Any]) -> list[str]:
    lines = [
        f"Workflow ID: {status['workflow_id']}",
        f"Path: {status['path']}",
        f"Risk level: {status['risk_level']}",
        f"Current phase: {status['current_phase'] or 'none'}",
        f"Runtime status: {status['runtime_status']}",
        f"Active agent: {status['active_agent'] or 'none'}",
        f"Open handoffs: {status['open_handoffs']}",
        (
            "Overrides: "
            f"active={status['override_statuses']['active']}, "
            f"expiring={status['override_statuses']['expiring']}, "
            f"revalidation_required={status['override_statuses']['revalidation_required']}"
        ),
        f"Merge ready: {'yes' if status['merge_ready'] else 'no'}",
    ]

    if status["blockers"]:
        lines.append(f"Blockers: {', '.join(status['blockers'])}")
    if status["warnings"]:
        lines.append(f"Warnings: {' | '.join(status['warnings'])}")

    return lines


def audit_lines(audit: dict[str, Any]) -> list[str]:
    lines: list[str] = []

    for workflow in audit["workflows"]:
        if not workflow["valid"]:
            lines.append(
                f"{Path(workflow['path']).name} | invalid | "
                f"loop={workflow['loop_governance']['compliance_status']} | "
                f"evaluation={workflow['evaluation']['compliance_status']} | "
                f"errors={'; '.join(workflow['errors'])}"
            )
            continue

        lines.append(
            f"{workflow['workflow_id']} | risk={workflow['risk_level']} | "
            f"phase={workflow['current_phase'] or 'none'} | runtime={workflow['runtime_status']} | "
            f"handoffs={workflow['open_handoffs']} | blockers={len(workflow['blockers'])} | "
            f"loop={workflow['loop_governance']['compliance_status']} | "
            f"evaluation={workflow['evaluation']['compliance_status']} | "
            f"merge_ready={'yes' if workflow['merge_ready'] else 'no'}"
        )

    return lines


def _phase_states(raw: dict[str, Any]) -> dict[str, str]:
    phases = raw.get("execution", {}).get("phases", [])
    return {
        phase.get("phase"): phase.get("state")
        for phase in phases
        if isinstance(phase, dict)
    }


def _load_invalid_workflow_raw(path: Path) -> dict[str, Any]:
    try:
        raw = load_workflow_raw(path)
    except Exception:
        return {}
    return raw if isinstance(raw, dict) else {}


def _loop_governance_summary(
    raw: dict[str, Any], validation_errors: list[str]
) -> dict[str, Any]:
    loops = _raw_loops(raw)
    errors = [
        error for error in validation_errors if error.startswith("loop_governance")
    ]

    if not loops:
        return {
            "declared": False,
            "compliance_status": "not_declared",
            "total_loops": 0,
            "status_counts": {},
            "errors": errors,
        }

    status_counts: dict[str, int] = {}
    for loop in loops:
        status = str(loop.get("status", "unknown"))
        status_counts[status] = status_counts.get(status, 0) + 1

    return {
        "declared": True,
        "compliance_status": "failed" if errors else "passed",
        "total_loops": len(loops),
        "status_counts": status_counts,
        "errors": errors,
    }


def _evaluation_summary(
    raw: dict[str, Any], validation_errors: list[str]
) -> dict[str, Any]:
    evaluation = raw.get("evaluation")
    errors = [
        error
        for error in validation_errors
        if error.startswith("evaluation") or error.startswith("HIGH evaluation")
    ]

    if not isinstance(evaluation, dict):
        return {
            "declared": False,
            "compliance_status": "not_declared",
            "categories": 0,
            "required_metrics": 0,
            "blocking_metrics": 0,
            "failed_metrics": 0,
            "blocking_failed_metrics": 0,
            "errors": errors,
        }

    categories = [
        category
        for category in evaluation.get("categories", [])
        if isinstance(category, dict)
    ]
    metrics = [
        metric
        for category in categories
        for metric in category.get("required_metrics", [])
        if isinstance(metric, dict)
    ]
    failed_metrics = [
        metric
        for metric in metrics
        if metric.get("status") in {"failed", "blocked"} or _metric_has_error(metric, errors)
    ]
    blocking_failed_metrics = [
        metric for metric in failed_metrics if metric.get("blocks_merge") is True
    ]

    compliance_status = str(evaluation.get("compliance_status", "unknown"))
    if errors:
        compliance_status = "failed"

    return {
        "declared": True,
        "compliance_status": compliance_status,
        "categories": len(categories),
        "required_metrics": sum(1 for metric in metrics if metric.get("required") is True),
        "blocking_metrics": sum(1 for metric in metrics if metric.get("blocks_merge") is True),
        "failed_metrics": len(failed_metrics),
        "blocking_failed_metrics": len(blocking_failed_metrics),
        "errors": errors,
    }


def _raw_loops(raw: dict[str, Any]) -> list[dict[str, Any]]:
    loop_governance = raw.get("loop_governance")
    if not isinstance(loop_governance, dict):
        return []
    return [
        loop
        for loop in loop_governance.get("loops", [])
        if isinstance(loop, dict)
    ]


def _metric_has_error(metric: dict[str, Any], errors: list[str]) -> bool:
    metric_id = metric.get("id")
    if not isinstance(metric_id, str):
        return False
    return any(f".{metric_id}'" in error or f".{metric_id} " in error for error in errors)


def _override_statuses(raw: dict[str, Any]) -> dict[str, int]:
    statuses = {"active": 0, "expiring": 0, "revalidation_required": 0}
    lifecycle = _collect_override_lifecycle_statuses(raw.get("overrides"))
    for state in lifecycle.values():
        if state in statuses:
            statuses[state] += 1
    return statuses


def _is_merge_ready(
    risk_level: str,
    phase_states: dict[str, str],
    runtime_status: str,
    override_statuses: dict[str, int],
    blockers: list[str],
) -> bool:
    if blockers:
        return False
    if runtime_status == "blocked":
        return False
    if override_statuses["revalidation_required"] > 0:
        return False

    required_by_risk = {
        "LOW": ["planning", "implementation", "review"],
        "MEDIUM": ["planning", "architecture-check", "implementation", "review", "qa"],
        "HIGH": [
            "planning",
            "architecture-check",
            "implementation",
            "review",
            "qa",
            "approval",
        ],
    }

    for phase_name in required_by_risk.get(risk_level, []):
        if phase_states.get(phase_name) != "completed":
            return False

    return True
