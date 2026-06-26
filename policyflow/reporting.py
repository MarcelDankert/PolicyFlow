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
        "workflow_governance": _workflow_governance_summary(True, merge_ready, blockers, []),
        "human_governance": _human_governance_summary(raw, []),
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
                    "workflow_governance": _workflow_governance_summary(
                        False, False, [], exc.errors
                    ),
                    "human_governance": _human_governance_summary(raw, exc.errors),
                }
            )

    return {
        "schema_version": "policyflow.audit.v1",
        "report_type": "workflow_audit",
        "compatibility": {
            "existing_workflow_fields_preserved": True,
            "additive_fields": [
                "schema_version",
                "report_type",
                "compatibility",
                "summary",
                "workflow_governance",
                "human_governance",
            ],
        },
        "directory": str(directory),
        "summary": _audit_summary(workflows),
        "workflows": workflows,
    }


def evaluation_report_directory(directory: Path) -> dict[str, Any]:
    audit = audit_directory(directory)
    workflows = [
        _evaluation_report_workflow(workflow)
        for workflow in audit["workflows"]
    ]
    summary = {
        "total_workflows": len(workflows),
        "evaluations_declared": sum(1 for workflow in workflows if workflow["declared"]),
        "missing_required_evaluations": sum(
            1 for workflow in workflows if workflow["missing_required_evaluation"]
        ),
        "passed": sum(
            1 for workflow in workflows if workflow["compliance_status"] == "passed"
        ),
        "failed": sum(
            1 for workflow in workflows if workflow["compliance_status"] == "failed"
        ),
        "failing_gates": sum(len(workflow["failing_gates"]) for workflow in workflows),
        "missing_evidence_references": sum(
            len(workflow["missing_evidence_references"]) for workflow in workflows
        ),
    }

    return {
        "directory": str(directory),
        "summary": summary,
        "workflows": workflows,
    }


def loop_report_directory(directory: Path) -> dict[str, Any]:
    audit = audit_directory(directory)
    workflows = [_loop_report_workflow(workflow) for workflow in audit["workflows"]]
    summary = {
        "total_workflows": len(workflows),
        "loops_declared": sum(1 for workflow in workflows if workflow["declared"]),
        "missing_loop_governance": sum(
            1 for workflow in workflows if workflow["missing_loop_governance"]
        ),
        "passed": sum(
            1 for workflow in workflows if workflow["compliance_status"] == "passed"
        ),
        "failed": sum(
            1 for workflow in workflows if workflow["compliance_status"] == "failed"
        ),
        "total_loops": sum(workflow["total_loops"] for workflow in workflows),
        "exceeded_iterations": sum(
            len(workflow["exceeded_iterations"]) for workflow in workflows
        ),
        "missing_stop_evidence": sum(
            len(workflow["missing_stop_evidence"]) for workflow in workflows
        ),
        "missing_escalation_evidence": sum(
            len(workflow["missing_escalation_evidence"]) for workflow in workflows
        ),
        "unresolved_blocked_loops": sum(
            len(workflow["unresolved_blocked_loops"]) for workflow in workflows
        ),
    }

    return {
        "directory": str(directory),
        "summary": summary,
        "workflows": workflows,
    }


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


def loop_report_lines(report: dict[str, Any]) -> list[str]:
    summary = report["summary"]
    lines = [
        (
            "Loop report | "
            f"workflows={summary['total_workflows']} | "
            f"declared={summary['loops_declared']} | "
            f"missing_loop_governance={summary['missing_loop_governance']} | "
            f"passed={summary['passed']} | failed={summary['failed']} | "
            f"total_loops={summary['total_loops']} | "
            f"exceeded_iterations={summary['exceeded_iterations']} | "
            f"missing_stop_evidence={summary['missing_stop_evidence']} | "
            f"missing_escalation_evidence={summary['missing_escalation_evidence']} | "
            f"unresolved_blocked_loops={summary['unresolved_blocked_loops']}"
        )
    ]

    for workflow in report["workflows"]:
        lines.append(
            f"{Path(workflow['path']).name} | "
            f"workflow={workflow['workflow_id'] or 'unknown'} | "
            f"loop={workflow['compliance_status']} | "
            f"declared={'yes' if workflow['declared'] else 'no'} | "
            f"missing_loop_governance={'yes' if workflow['missing_loop_governance'] else 'no'} | "
            f"total_loops={workflow['total_loops']} | "
            f"exceeded_iterations={len(workflow['exceeded_iterations'])} | "
            f"missing_stop_evidence={len(workflow['missing_stop_evidence'])} | "
            f"missing_escalation_evidence={len(workflow['missing_escalation_evidence'])} | "
            f"unresolved_blocked_loops={len(workflow['unresolved_blocked_loops'])}"
        )

    return lines


def evaluation_report_lines(report: dict[str, Any]) -> list[str]:
    summary = report["summary"]
    lines = [
        (
            "Evaluation report | "
            f"workflows={summary['total_workflows']} | "
            f"declared={summary['evaluations_declared']} | "
            f"missing_required={summary['missing_required_evaluations']} | "
            f"passed={summary['passed']} | failed={summary['failed']} | "
            f"failing_gates={summary['failing_gates']} | "
            f"missing_evidence_refs={summary['missing_evidence_references']}"
        )
    ]

    for workflow in report["workflows"]:
        lines.append(
            f"{Path(workflow['path']).name} | "
            f"workflow={workflow['workflow_id'] or 'unknown'} | "
            f"evaluation={workflow['compliance_status']} | "
            f"declared={'yes' if workflow['declared'] else 'no'} | "
            f"missing_required_evaluation={'yes' if workflow['missing_required_evaluation'] else 'no'} | "
            f"failing_gates={len(workflow['failing_gates'])} | "
            f"missing_evidence_refs={len(workflow['missing_evidence_references'])}"
        )

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


def _audit_summary(workflows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "workflow_governance": {
            "total": len(workflows),
            "valid": sum(1 for workflow in workflows if workflow["valid"]),
            "invalid": sum(1 for workflow in workflows if not workflow["valid"]),
            "merge_ready": sum(1 for workflow in workflows if workflow["merge_ready"]),
            "blocked": sum(1 for workflow in workflows if workflow["blocked"]),
        },
        "loop_governance": {
            "declared": sum(
                1 for workflow in workflows if workflow["loop_governance"]["declared"]
            ),
            "missing": sum(
                1 for workflow in workflows if not workflow["loop_governance"]["declared"]
            ),
            "passed": sum(
                1
                for workflow in workflows
                if workflow["loop_governance"]["compliance_status"] == "passed"
            ),
            "failed": sum(
                1
                for workflow in workflows
                if workflow["loop_governance"]["compliance_status"] == "failed"
            ),
        },
        "evaluation_governance": {
            "declared": sum(
                1 for workflow in workflows if workflow["evaluation"]["declared"]
            ),
            "missing": sum(
                1 for workflow in workflows if not workflow["evaluation"]["declared"]
            ),
            "passed": sum(
                1
                for workflow in workflows
                if workflow["evaluation"]["compliance_status"] == "passed"
            ),
            "failed": sum(
                1
                for workflow in workflows
                if workflow["evaluation"]["compliance_status"] == "failed"
            ),
        },
        "human_governance": {
            "approval_required": sum(
                1
                for workflow in workflows
                if workflow["human_governance"]["approval_required"]
            ),
            "approval_evidence_present": sum(
                1
                for workflow in workflows
                if workflow["human_governance"]["approval_evidence_present"]
            ),
            "missing_approval_evidence": sum(
                1
                for workflow in workflows
                if workflow["human_governance"]["missing_approval_evidence"]
            ),
            "status_counts": _status_counts(
                workflow["human_governance"]["status"] for workflow in workflows
            ),
        },
    }


def _workflow_governance_summary(
    valid: bool, merge_ready: bool, blockers: list[str], errors: list[str]
) -> dict[str, Any]:
    return {
        "status": "passed" if valid else "failed",
        "valid": valid,
        "merge_ready": merge_ready,
        "blocked": bool(blockers),
        "errors": errors,
    }


def _human_governance_summary(
    raw: dict[str, Any], validation_errors: list[str]
) -> dict[str, Any]:
    governance = raw.get("governance") if isinstance(raw.get("governance"), dict) else {}
    evidence = raw.get("evidence") if isinstance(raw.get("evidence"), dict) else {}
    approval = evidence.get("approval") if isinstance(evidence.get("approval"), dict) else {}
    approval_required = governance.get("human_approval_required") is True
    approval_evidence_present = all(
        approval.get(field) not in (None, "", False)
        for field in ("approved_by", "reference", "scope_confirmed")
    )
    errors = [
        error
        for error in validation_errors
        if "approval" in error.lower() or "human" in error.lower()
    ]
    missing_approval_evidence = approval_required and not approval_evidence_present

    if not approval_required:
        status = "not_required"
    elif errors or missing_approval_evidence:
        status = "failed"
    else:
        status = "passed"

    return {
        "status": status,
        "approval_required": approval_required,
        "approval_evidence_present": approval_evidence_present,
        "missing_approval_evidence": missing_approval_evidence,
        "errors": errors,
    }


def _status_counts(statuses) -> dict[str, int]:
    counts = {"failed": 0, "not_required": 0, "passed": 0}
    for status in statuses:
        counts[status] = counts.get(status, 0) + 1
    return counts


def _loop_report_workflow(workflow: dict[str, Any]) -> dict[str, Any]:
    loop_governance = workflow["loop_governance"]
    loops = _raw_loops(_load_invalid_workflow_raw(Path(workflow["path"])))
    exceeded_iterations = [
        error
        for error in loop_governance["errors"]
        if "current_iteration" in error and "exceeds max_iterations" in error
    ]
    missing_stop_evidence = [
        error
        for error in loop_governance["errors"]
        if "completed or terminated loops must reference" in error
    ]
    missing_escalation_evidence = [
        error
        for error in loop_governance["errors"]
        if "escalated loops must reference" in error
    ]

    compliance_status = loop_governance["compliance_status"]
    missing_loop_governance = not loop_governance["declared"]
    if missing_loop_governance:
        compliance_status = "missing"

    return {
        "path": workflow["path"],
        "workflow_id": workflow["workflow_id"],
        "valid": workflow["valid"],
        "declared": loop_governance["declared"],
        "compliance_status": compliance_status,
        "missing_loop_governance": missing_loop_governance,
        "total_loops": loop_governance["total_loops"],
        "status_counts": loop_governance["status_counts"],
        "exceeded_iterations": exceeded_iterations,
        "missing_stop_evidence": missing_stop_evidence,
        "missing_escalation_evidence": missing_escalation_evidence,
        "unresolved_blocked_loops": [
            loop["id"]
            for loop in loops
            if loop.get("status") == "escalated" and isinstance(loop.get("id"), str)
        ],
        "errors": loop_governance["errors"],
    }


def _evaluation_report_workflow(workflow: dict[str, Any]) -> dict[str, Any]:
    evaluation = workflow["evaluation"]
    missing_evidence_references = [
        error
        for error in evaluation["errors"]
        if "references missing workflow evidence" in error
    ]
    failing_gates = [
        error
        for error in evaluation["errors"]
        if error not in missing_evidence_references
    ]

    compliance_status = evaluation["compliance_status"]
    missing_required_evaluation = not evaluation["declared"]
    if missing_required_evaluation:
        compliance_status = "missing"

    return {
        "path": workflow["path"],
        "workflow_id": workflow["workflow_id"],
        "valid": workflow["valid"],
        "declared": evaluation["declared"],
        "compliance_status": compliance_status,
        "missing_required_evaluation": missing_required_evaluation,
        "failing_gates": failing_gates,
        "missing_evidence_references": missing_evidence_references,
        "errors": evaluation["errors"],
    }


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
