from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MigrationDiagnostic:
    path: str
    decision: str
    new_representation: str
    message: str


V1_MIGRATION_RULES: dict[str, tuple[str, str, str]] = {
    "workflow": (
        "RENAME",
        "change",
        "Replace workflow-centric metadata with V2 change governance metadata.",
    ),
    "context": (
        "REBUILD",
        "change, risk, confidence",
        "Split V1 context into explicit V2 governance concepts.",
    ),
    "governance": (
        "KEEP",
        "governance",
        "Keep required reviews and human approval requirement only.",
    ),
    "execution": (
        "REMOVE",
        "none",
        "Execution phase state belongs to external workflow or runtime tooling.",
    ),
    "contracts": (
        "MOVE",
        "external evidence",
        "Agent role contracts become normalized evidence produced outside PolicyFlow.",
    ),
    "runtime": (
        "REMOVE",
        "none",
        "Runtime state is replaced by PolicyFlow validation diagnostics.",
    ),
    "handoffs": (
        "MOVE",
        "external runtime evidence",
        "First-class handoff state leaves the V2 core schema.",
    ),
    "loop_governance": (
        "MOVE",
        "external runtime policy or evidence",
        "Loop state is represented outside PolicyFlow; governance-relevant outcomes become evidence.",
    ),
    "evaluation": (
        "SIMPLIFY",
        "evidence",
        "Evaluation metrics are external evidence; PolicyFlow does not calculate analytics values.",
    ),
    "overrides": (
        "KEEP",
        "overrides",
        "Keep governance exceptions in simplified V2 override records.",
    ),
    "evidence": (
        "SIMPLIFY",
        "evidence[]",
        "Convert keyed phase evidence into normalized evidence items.",
    ),
}

V2_FORBIDDEN_FIELD_NAMES = {
    "active_agent",
    "agent",
    "agent_execution",
    "codex",
    "contracts",
    "current_iteration",
    "current_phase",
    "evaluation",
    "execution",
    "handoffs",
    "loop_governance",
    "model",
    "model_id",
    "provider",
    "provider_adapter",
    "prompt",
    "prompt_id",
    "runner",
    "runner_status",
    "runtime",
    "workflow",
}


def normalize_workflow_payload(data: dict[str, Any]) -> dict[str, Any]:
    """Prefer context/governance fields and accept root-level fallbacks."""
    # Compatibility policy: docs/schema-compatibility.md defines the canonical
    # schema and the 0.x root-level fallback window.

    context = data.get("context") if isinstance(data.get("context"), dict) else {}
    governance = (
        data.get("governance") if isinstance(data.get("governance"), dict) else {}
    )
    execution = data.get("execution") if isinstance(data.get("execution"), dict) else {}
    evidence = data.get("evidence") if isinstance(data.get("evidence"), dict) else None
    evaluation = (
        data.get("evaluation") if isinstance(data.get("evaluation"), dict) else None
    )
    loop_governance = (
        data.get("loop_governance")
        if isinstance(data.get("loop_governance"), dict)
        else None
    )
    contracts = (
        data.get("contracts") if isinstance(data.get("contracts"), dict) else None
    )
    overrides = data.get("overrides") if isinstance(data.get("overrides"), list) else None
    runtime = data.get("runtime") if isinstance(data.get("runtime"), dict) else None
    handoffs = data.get("handoffs") if isinstance(data.get("handoffs"), list) else None

    return {
        "workflow": data.get("workflow"),
        "context": {
            "workflow_file": context.get("workflow_file", data.get("workflow_file")),
            "risk_level": context.get("risk_level", data.get("risk_level")),
            "confidence": context.get("confidence", data.get("confidence")),
        },
        "governance": {
            "required_reviews": governance.get(
                "required_reviews", data.get("required_reviews")
            ),
            "human_approval_required": governance.get(
                "human_approval_required", data.get("human_approval_required", False)
            ),
            "escalation_required": governance.get(
                "escalation_required", data.get("escalation_required", False)
            ),
            "protected_areas_touched": governance.get(
                "protected_areas_touched", data.get("protected_areas_touched")
            ),
            "approval_evidence": governance.get(
                "approval_evidence", data.get("approval_evidence")
            ),
        },
        "execution": {
            "mode": execution.get("mode"),
            "phases": execution.get("phases"),
        },
        "evidence": evidence,
        "evaluation": evaluation,
        "loop_governance": loop_governance,
        "contracts": contracts,
        "overrides": overrides,
        "runtime": runtime,
        "handoffs": handoffs,
    }


def normalize_workflow_v2_payload(data: dict[str, Any]) -> dict[str, Any]:
    """Return the V2 governance payload without V1 compatibility fallbacks."""
    normalized = {
        key: data[key]
        for key in (
            "version",
            "change",
            "risk",
            "governance",
            "confidence",
            "evidence",
            "overrides",
        )
        if key in data
    }
    normalized.update(
        {
            key: value
            for key, value in data.items()
            if key
            not in {
                "version",
                "change",
                "risk",
                "governance",
                "confidence",
                "evidence",
                "overrides",
            }
        }
    )
    return normalized


def collect_v1_migration_diagnostics(data: dict[str, Any]) -> list[MigrationDiagnostic]:
    diagnostics: list[MigrationDiagnostic] = []

    for field_name, (decision, new_representation, message) in V1_MIGRATION_RULES.items():
        if field_name not in data:
            continue
        diagnostics.append(
            MigrationDiagnostic(
                path=field_name,
                decision=decision,
                new_representation=new_representation,
                message=message,
            )
        )

    diagnostics.extend(_collect_nested_v1_migration_diagnostics(data))
    return diagnostics


def collect_v2_forbidden_field_errors(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for path in _walk_mapping_paths(data):
        field_name = path.rsplit(".", 1)[-1]
        if field_name not in V2_FORBIDDEN_FIELD_NAMES:
            continue
        errors.append(
            f"{path} is not allowed in V2 governance schema; "
            "external systems may produce normalized evidence, but PolicyFlow "
            "does not own execution, provider, model, runner, handoff, loop, "
            "or analytics state."
        )
    return errors


def _collect_nested_v1_migration_diagnostics(
    data: dict[str, Any]
) -> list[MigrationDiagnostic]:
    diagnostics: list[MigrationDiagnostic] = []

    context = data.get("context")
    if isinstance(context, dict):
        if "risk_level" in context:
            diagnostics.append(
                MigrationDiagnostic(
                    path="context.risk_level",
                    decision="RENAME",
                    new_representation="risk.level",
                    message="Convert LOW/MEDIUM/HIGH to low/medium/high.",
                )
            )
        if "confidence" in context:
            diagnostics.append(
                MigrationDiagnostic(
                    path="context.confidence",
                    decision="SIMPLIFY",
                    new_representation="confidence",
                    message="Collapse phase-specific confidence into one governance confidence level and summary.",
                )
            )

    governance = data.get("governance")
    if isinstance(governance, dict):
        if "protected_areas_touched" in governance:
            diagnostics.append(
                MigrationDiagnostic(
                    path="governance.protected_areas_touched",
                    decision="RENAME",
                    new_representation="risk.protected_areas",
                    message="Move protected-area declaration under risk.",
                )
            )
        if "approval_evidence" in governance:
            diagnostics.append(
                MigrationDiagnostic(
                    path="governance.approval_evidence",
                    decision="SIMPLIFY",
                    new_representation="evidence[] with type: approval",
                    message="Replace descriptive approval evidence references with normalized evidence items.",
                )
            )

    runtime = data.get("runtime")
    if isinstance(runtime, dict) and "active_agent" in runtime:
        diagnostics.append(
            MigrationDiagnostic(
                path="runtime.active_agent",
                decision="REMOVE",
                new_representation="none",
                message="Active agent state is execution ownership and is not represented in V2.",
            )
        )

    loop_governance = data.get("loop_governance")
    if isinstance(loop_governance, dict):
        diagnostics.append(
            MigrationDiagnostic(
                path="loop_governance.loops",
                decision="MOVE",
                new_representation="external evidence",
                message="Loop progress, iteration limits, and final outcomes should be emitted by external systems as evidence when governance requires them.",
            )
        )

    evaluation = data.get("evaluation")
    if isinstance(evaluation, dict):
        diagnostics.append(
            MigrationDiagnostic(
                path="evaluation.categories",
                decision="SIMPLIFY",
                new_representation="evidence[]",
                message="Evaluation categories and metrics become externally produced evidence; PolicyFlow validates evidence status, not metric calculation.",
            )
        )

    return diagnostics


def _walk_mapping_paths(value: Any, prefix: str = "") -> list[str]:
    paths: list[str] = []
    if not isinstance(value, dict):
        return paths

    for key, child in value.items():
        if not isinstance(key, str):
            continue
        path = f"{prefix}.{key}" if prefix else key
        paths.append(path)
        if isinstance(child, dict):
            paths.extend(_walk_mapping_paths(child, path))
        elif isinstance(child, list):
            for index, item in enumerate(child):
                paths.extend(_walk_mapping_paths(item, f"{path}.{index}"))

    return paths
