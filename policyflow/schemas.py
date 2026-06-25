from __future__ import annotations

from typing import Any


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
