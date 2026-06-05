from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from policyflow.cli import app


runner = CliRunner()


def test_golden_consumer_repo_path_runs_end_to_end(tmp_path: Path) -> None:
    init_result = runner.invoke(app, ["init", str(tmp_path)])
    assert init_result.exit_code == 0

    doctor_result = runner.invoke(app, ["doctor", str(tmp_path), "--json"])
    assert doctor_result.exit_code == 0

    workflow_path = tmp_path / "ai/workflows/features/starter-workflow.yml"
    assert workflow_path.exists()

    validate_result = runner.invoke(app, ["validate", str(workflow_path)])
    assert validate_result.exit_code == 0

    status_result = runner.invoke(app, ["status", str(workflow_path)])
    assert status_result.exit_code == 0
    assert "Workflow ID: starter-workflow" in status_result.stdout

    audit_result = runner.invoke(app, ["audit", str(tmp_path / "ai/workflows")])
    assert audit_result.exit_code == 0
    assert "starter-workflow" in audit_result.stdout

    pr_body_path = tmp_path / "pr-body.md"
    pr_body_path.write_text(_starter_pr_body(), encoding="utf-8")
    validate_pr_result = runner.invoke(
        app,
        ["validate-pr", str(workflow_path), str(pr_body_path)],
    )
    assert validate_pr_result.exit_code == 0


def _starter_pr_body() -> str:
    return """## Summary

Starter PolicyFlow validation path.

## Linked Issue

#1

## Workflow File
- ai/workflows/features/starter-workflow.yml

## Scope
- In scope: starter PolicyFlow validation
- Out of scope: product changes

## Non-Goals

No runtime behavior changes.

## Governance
- Declared risk level: MEDIUM
- Confidence summary: starter workflow is ready for validation
- Required reviews completed: architecture-agent, review-agent, qa-agent
- Human approval login if required: not required
- Human approval reference if required: not required
- Escalation notes: none
- Protected areas touched: none

## Evidence
- Planning evidence: evidence.planning
- Architecture evidence: evidence.architecture-check

## Overrides
- Override ID: starter-phase-bypass
- Override type: phase_bypass
- Approved by login: architecture-agent
- Approval reference: STARTER-ARCH-OVERRIDE
- Mitigations confirmed: yes

## Confirmation
- [x] The implementation matches the declared scope
- [x] Non-goals were respected
- [x] The linked workflow file governed this change
- [x] The workflow file existed before implementation and governed the work from the start
- [x] Scope, non-goals, and risk were fixed in the workflow before implementation started
- [x] Required workflow phases were executed as visible working steps, not only documented after the fact

## Tests
```text
policyflow validate ai/workflows/features/starter-workflow.yml
```

## Docs
- [x] No docs update needed
"""
