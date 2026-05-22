from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

from policyflow.exceptions import WorkflowValidationError
from policyflow.runtime import (
    PHASE_AGENT_MAP,
    block_phase,
    complete_phase,
    load_workflow_raw,
    record_handoff,
    save_workflow_raw,
    start_phase,
)
from policyflow.validator import validate_workflow_data


DEFAULT_RUNNER_CONFIG = Path("policyflow.runners.yml")
PHASE_EVIDENCE_KEYS = {
    "planning": "planning",
    "architecture-check": "architecture-check",
    "review": "review",
    "qa": "qa",
    "approval": "approval",
}
PHASE_CONTRACT_KEYS = {
    "planning": "planning",
    "architecture-check": "architecture-check",
    "implementation": "implementation",
    "review": "review",
    "qa": "qa",
}


def run_phase_with_runner(
    workflow_path: Path, phase: str, runner_config_path: Path | None = None
) -> None:
    if phase == "approval":
        raise WorkflowValidationError(
            ["Phase 'approval' remains human-driven and cannot be run via agent execution."]
        )

    config_path = runner_config_path or DEFAULT_RUNNER_CONFIG
    runner_config = _load_runner_config(config_path)
    runner_name = str(runner_config.get("default_runner", "")).strip()
    runners = runner_config.get("runners")

    if not runner_name:
        raise WorkflowValidationError(["Runner config must declare default_runner."])
    if not isinstance(runners, dict) or runner_name not in runners:
        raise WorkflowValidationError(
            [f"Runner config must declare runner settings for '{runner_name}'."]
        )

    runner = runners[runner_name]
    if not isinstance(runner, dict):
        raise WorkflowValidationError(
            [f"Runner definition for '{runner_name}' must be a mapping."]
        )

    start_phase(workflow_path, phase)

    try:
        raw = load_workflow_raw(workflow_path)
        payload = _build_execution_payload(raw, workflow_path, phase, runner, config_path)
        result = _execute_runner(runner, payload, workflow_path, config_path)
        _apply_runner_result(workflow_path, phase, result)
    except WorkflowValidationError as exc:
        _block_phase_on_failure(workflow_path, phase, exc.errors[0])
        raise
    except Exception as exc:  # pragma: no cover - defensive catch for subprocess/json edge cases
        _block_phase_on_failure(workflow_path, phase, str(exc))
        raise WorkflowValidationError([str(exc)]) from exc


def _load_runner_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise WorkflowValidationError([f"Runner config file not found: {path}"])

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise WorkflowValidationError([f"Invalid runner config YAML: {exc}"]) from exc

    if not isinstance(data, dict):
        raise WorkflowValidationError(
            ["Runner config file must contain a top-level YAML mapping."]
        )

    return data


def _build_execution_payload(
    raw: dict[str, Any],
    workflow_path: Path,
    phase: str,
    runner: dict[str, Any],
    config_path: Path,
) -> dict[str, Any]:
    handoffs = raw.get("handoffs") or []
    inbound_handoff = None
    for handoff in handoffs:
        if (
            isinstance(handoff, dict)
            and handoff.get("to_phase") == phase
            and handoff.get("status") in {"pending", "completed"}
        ):
            inbound_handoff = handoff
            break

    return {
        "workflow_path": str(workflow_path),
        "workflow": raw,
        "phase": phase,
        "owner_agent": PHASE_AGENT_MAP.get(phase),
        "prompt_text": _load_phase_asset(runner, "prompt_paths", phase, config_path),
        "agent_text": _load_phase_asset(runner, "agent_paths", phase, config_path),
        "handoff": inbound_handoff,
    }


def _load_phase_asset(
    runner: dict[str, Any], config_key: str, phase: str, config_path: Path
) -> str | None:
    phase_map = runner.get(config_key)
    if not isinstance(phase_map, dict):
        return None
    configured_path = phase_map.get(phase)
    if not isinstance(configured_path, str) or not configured_path.strip():
        return None

    candidate = Path(configured_path)
    if candidate.exists():
        return candidate.read_text(encoding="utf-8")

    cwd_candidate = Path.cwd() / configured_path
    if cwd_candidate.exists():
        return cwd_candidate.read_text(encoding="utf-8")

    config_candidate = config_path.parent / configured_path
    if config_candidate.exists():
        return config_candidate.read_text(encoding="utf-8")

    raise WorkflowValidationError(
        [f"Runner asset for phase '{phase}' not found: {configured_path}"]
    )


def _execute_runner(
    runner: dict[str, Any],
    payload: dict[str, Any],
    workflow_path: Path,
    config_path: Path,
) -> dict[str, Any]:
    command = runner.get("command")
    if not isinstance(command, list) or not command:
        raise WorkflowValidationError(["Runner command must be a non-empty list."])

    with tempfile.TemporaryDirectory() as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        input_path = temp_dir / "policyflow-agent-input.json"
        output_path = temp_dir / "policyflow-agent-output.json"
        input_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

        substitutions = {
            "workflow_path": str(workflow_path),
            "phase": payload["phase"],
            "input_path": str(input_path),
            "output_path": str(output_path),
            "python_executable": sys.executable,
        }

        resolved_command = [
            _format_command_token(token, substitutions) for token in command
        ]

        completed = subprocess.run(
            resolved_command,
            cwd=Path.cwd(),
            text=True,
            capture_output=True,
            check=False,
        )

        if completed.returncode != 0:
            stderr = completed.stderr.strip()
            stdout = completed.stdout.strip()
            message = stderr or stdout or f"runner exited with code {completed.returncode}"
            raise WorkflowValidationError([f"Agent runner failed: {message}"])

        if not output_path.exists():
            raise WorkflowValidationError(
                [f"Agent runner did not produce output JSON: {output_path}"]
            )

        try:
            result = json.loads(output_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise WorkflowValidationError(
                [f"Agent runner produced invalid JSON: {exc}"]
            ) from exc

    if not isinstance(result, dict):
        raise WorkflowValidationError(
            ["Agent runner output must be a top-level JSON object."]
        )

    return result


def _format_command_token(token: Any, substitutions: dict[str, str]) -> str:
    if not isinstance(token, str):
        raise WorkflowValidationError(["Runner command entries must be strings."])
    return token.format(**substitutions)


def _apply_runner_result(workflow_path: Path, phase: str, result: dict[str, Any]) -> None:
    output_phase = str(result.get("phase", "")).strip()
    if output_phase != phase:
        raise WorkflowValidationError(
            [f"Agent runner output phase must match requested phase: {phase}"]
        )

    output_owner = str(result.get("owner_agent", "")).strip()
    expected_owner = PHASE_AGENT_MAP.get(phase)
    if output_owner != expected_owner:
        raise WorkflowValidationError(
            [f"Agent runner output owner_agent must match expected owner: {expected_owner}"]
        )

    status = str(result.get("status", "")).strip()
    if status not in {"completed", "blocked"}:
        raise WorkflowValidationError(
            ["Agent runner output status must be 'completed' or 'blocked'."]
        )

    if status == "blocked":
        blockers = result.get("blockers")
        if isinstance(blockers, list) and blockers:
            reason = str(blockers[0])
        else:
            reason = str(result.get("summary", "")).strip() or "agent runner blocked phase"
        _block_phase_on_failure(workflow_path, phase, reason)
        raise WorkflowValidationError([f"Agent runner blocked phase '{phase}': {reason}"])

    raw = load_workflow_raw(workflow_path)
    updated = deepcopy(raw)
    _apply_phase_updates(updated, phase, result)
    validate_workflow_data(updated)
    save_workflow_raw(workflow_path, updated)

    complete_phase(workflow_path, phase)

    handoff = result.get("handoff")
    if isinstance(handoff, dict):
        to_phase = handoff.get("to_phase")
        required_inputs = handoff.get("required_inputs")
        produced_outputs = handoff.get("produced_outputs")
        if (
            isinstance(to_phase, str)
            and isinstance(required_inputs, list)
            and isinstance(produced_outputs, list)
        ):
            record_handoff(
                workflow_path,
                phase,
                to_phase,
                [str(item) for item in required_inputs],
                [str(item) for item in produced_outputs],
                [],
                [],
            )


def _apply_phase_updates(raw: dict[str, Any], phase: str, result: dict[str, Any]) -> None:
    contract_key = PHASE_CONTRACT_KEYS.get(phase)
    contract_updates = result.get("contract_updates")
    if contract_key and isinstance(contract_updates, dict):
        raw.setdefault("contracts", {})
        raw["contracts"][contract_key] = contract_updates

    evidence_key = PHASE_EVIDENCE_KEYS.get(phase)
    evidence_updates = result.get("evidence_updates")
    if evidence_key and isinstance(evidence_updates, dict):
        raw.setdefault("evidence", {})
        raw["evidence"][evidence_key] = evidence_updates


def _block_phase_on_failure(workflow_path: Path, phase: str, reason: str) -> None:
    try:
        block_phase(workflow_path, phase, reason)
    except WorkflowValidationError:
        pass
