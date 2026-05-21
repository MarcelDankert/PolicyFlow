from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

from policyflow.exceptions import WorkflowValidationError
from policyflow.validator import validate_workflow_data, validate_workflow_file


PHASE_AGENT_MAP = {
    "planning": "planning-agent",
    "architecture-check": "architecture-agent",
    "implementation": "senior-dev-agent",
    "review": "review-agent",
    "qa": "qa-agent",
    "approval": "human approval",
}

PHASE_ORDER = [
    "planning",
    "architecture-check",
    "implementation",
    "review",
    "qa",
    "approval",
]


def load_workflow_raw(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise WorkflowValidationError(["Workflow file must contain a top-level YAML mapping"])
    return data


def save_workflow_raw(path: Path, data: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, sort_keys=False)


def next_step_summary(path: Path) -> str:
    workflow = validate_workflow_file(path)
    workflow_data = workflow.model_dump(by_alias=True, mode="json")

    if workflow.runtime and workflow.runtime.status == "blocked":
        reason = workflow.runtime.block_reason or "no reason recorded"
        return f"Workflow is blocked in phase {workflow.runtime.current_phase}: {reason}"

    pending_handoff = _find_pending_handoff(workflow_data)
    if pending_handoff is not None:
        return (
            f"Pending handoff {pending_handoff['from_phase']} -> {pending_handoff['to_phase']} "
            f"with inputs {', '.join(pending_handoff['required_inputs'])}"
        )

    phase_states = _phase_states(workflow.model_dump(by_alias=True))
    for phase_name in PHASE_ORDER:
        if phase_states.get(phase_name) == "pending" and _can_start_phase(phase_states, phase_name):
            return f"Next startable phase: {phase_name}"

    return "No next step available."


def handoff_status_summary(path: Path) -> list[str]:
    workflow = validate_workflow_file(path)
    handoffs = workflow.model_dump(by_alias=True, mode="json").get("handoffs") or []
    if not handoffs:
        return ["No handoffs recorded."]

    lines: list[str] = []
    for handoff in handoffs:
        lines.append(
            f"{handoff['from_phase']} -> {handoff['to_phase']} [{handoff['status']}] "
            f"inputs={', '.join(handoff['required_inputs'])} "
            f"outputs={', '.join(handoff['produced_outputs'])}"
        )
    return lines


def start_phase(path: Path, phase: str) -> None:
    raw = load_workflow_raw(path)
    validate_workflow_data(raw)
    phase_states = _phase_states(raw)

    if phase_states.get(phase) != "pending":
        raise WorkflowValidationError([f"Phase '{phase}' must be pending before it can be started."])
    if not _can_start_phase(phase_states, phase):
        raise WorkflowValidationError([f"Phase '{phase}' cannot be started from the current workflow state."])

    updated = deepcopy(raw)
    _set_phase_state(updated, phase, "in_progress")
    _complete_matching_handoff(updated, phase)
    _ensure_runtime(updated)
    updated["runtime"].update(
        {
            "status": "in_progress",
            "current_phase": phase,
            "active_agent": PHASE_AGENT_MAP.get(phase),
            "last_transition": f"started {phase}",
            "block_reason": None,
        }
    )
    validate_workflow_data(updated)
    save_workflow_raw(path, updated)


def complete_phase(path: Path, phase: str) -> None:
    raw = load_workflow_raw(path)
    validate_workflow_data(raw)
    phase_states = _phase_states(raw)

    if phase_states.get(phase) != "in_progress":
        raise WorkflowValidationError([f"Phase '{phase}' must be in_progress before it can be completed."])

    updated = deepcopy(raw)
    _set_phase_state(updated, phase, "completed")
    _ensure_runtime(updated)
    updated["runtime"].update(
        {
            "status": "idle",
            "current_phase": phase,
            "active_agent": PHASE_AGENT_MAP.get(phase),
            "last_transition": f"completed {phase}",
            "block_reason": None,
        }
    )
    validate_workflow_data(updated)
    save_workflow_raw(path, updated)


def block_phase(path: Path, phase: str, reason: str) -> None:
    raw = load_workflow_raw(path)
    validate_workflow_data(raw)

    if phase not in _phase_states(raw):
        raise WorkflowValidationError([f"Phase '{phase}' is not declared in execution.phases."])

    updated = deepcopy(raw)
    _set_phase_state(updated, phase, "blocked")
    _ensure_runtime(updated)
    updated["runtime"].update(
        {
            "status": "blocked",
            "current_phase": phase,
            "active_agent": PHASE_AGENT_MAP.get(phase),
            "last_transition": f"blocked {phase}",
            "block_reason": reason,
        }
    )
    validate_workflow_data(updated)
    save_workflow_raw(path, updated)


def record_handoff(
    path: Path,
    from_phase: str,
    to_phase: str,
    required_inputs: list[str],
    produced_outputs: list[str],
    blockers: list[str] | None = None,
    override_refs: list[str] | None = None,
) -> None:
    raw = load_workflow_raw(path)
    validate_workflow_data(raw)
    phase_states = _phase_states(raw)

    if phase_states.get(from_phase) != "completed":
        raise WorkflowValidationError([f"Handoff source phase '{from_phase}' must be completed."])
    if phase_states.get(to_phase) not in {"pending", "in_progress"}:
        raise WorkflowValidationError([f"Handoff target phase '{to_phase}' must be pending or in_progress."])
    if not required_inputs or not produced_outputs:
        raise WorkflowValidationError(["Handoffs require non-empty required_inputs and produced_outputs."])

    updated = deepcopy(raw)
    handoff = {
        "from_phase": from_phase,
        "to_phase": to_phase,
        "status": "pending",
        "required_inputs": required_inputs,
        "produced_outputs": produced_outputs,
        "blockers": blockers or [],
        "override_refs": override_refs or [],
    }
    updated.setdefault("handoffs", [])
    updated["handoffs"] = [
        existing
        for existing in updated["handoffs"]
        if not (
            existing.get("from_phase") == from_phase
            and existing.get("to_phase") == to_phase
        )
    ]
    updated["handoffs"].append(handoff)
    _ensure_runtime(updated)
    updated["runtime"].update(
        {
            "status": "handoff_pending",
            "current_phase": from_phase,
            "active_agent": PHASE_AGENT_MAP.get(to_phase),
            "last_transition": f"handoff {from_phase} -> {to_phase}",
            "block_reason": None,
        }
    )
    validate_workflow_data(updated)
    save_workflow_raw(path, updated)


def _phase_states(raw: dict[str, Any]) -> dict[str, str]:
    phases = raw.get("execution", {}).get("phases", [])
    return {
        phase.get("phase"): phase.get("state")
        for phase in phases
        if isinstance(phase, dict)
    }


def _set_phase_state(raw: dict[str, Any], phase_name: str, state: str) -> None:
    for phase in raw.get("execution", {}).get("phases", []):
        if phase.get("phase") == phase_name:
            phase["state"] = state
            return
    raise WorkflowValidationError([f"Phase '{phase_name}' is not declared in execution.phases."])


def _ensure_runtime(raw: dict[str, Any]) -> None:
    if not isinstance(raw.get("runtime"), dict):
        raw["runtime"] = {}


def _find_pending_handoff(raw: dict[str, Any]) -> dict[str, Any] | None:
    for handoff in raw.get("handoffs", []) or []:
        if isinstance(handoff, dict) and handoff.get("status") == "pending":
            return handoff
    return None


def _complete_matching_handoff(raw: dict[str, Any], to_phase: str) -> None:
    for handoff in raw.get("handoffs", []) or []:
        if isinstance(handoff, dict) and handoff.get("to_phase") == to_phase and handoff.get("status") == "pending":
            handoff["status"] = "completed"


def _can_start_phase(phase_states: dict[str, str], phase: str) -> bool:
    if phase == "planning":
        return True
    if phase == "architecture-check":
        return phase_states.get("planning") == "completed"
    if phase == "implementation":
        return (
            phase_states.get("planning") == "completed"
            and phase_states.get("architecture-check") == "completed"
        )
    if phase == "review":
        return phase_states.get("implementation") == "completed"
    if phase == "qa":
        return phase_states.get("review") == "completed"
    if phase == "approval":
        return phase_states.get("qa") == "completed"
    return False
