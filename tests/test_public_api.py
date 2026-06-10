from __future__ import annotations

import json
from pathlib import Path

import policyflow
from policyflow import api
from policyflow.bootstrap import bootstrap_consumer_repo
from policyflow.workflow_generator import create_workflow_instance


def _create_workflow(
    tmp_path: Path,
    *,
    workflow_type: str = "feature",
    workflow_id: str = "api-feature",
    risk_level: str = "LOW",
) -> Path:
    bootstrap_consumer_repo(tmp_path)
    create_workflow_instance(
        tmp_path,
        workflow_type=workflow_type,
        workflow_id=workflow_id,
        risk_level=risk_level,
    )
    if workflow_type == "bugfix":
        return tmp_path / f"ai/workflows/bugfixes/{workflow_id}.yml"
    return tmp_path / f"ai/workflows/features/{workflow_id}.yml"


def _write_pr_body(tmp_path: Path) -> Path:
    body = """## Summary
API validation smoke.

## Linked Issue
#1

## Workflow File
- ai/workflows/features/api-feature.yml

## Governance
- Declared risk level: LOW
- Confidence summary: planning, implementation, tests, and residual uncertainty are documented.
- Required reviews completed: pending review-agent review
- Human approval login if required: not required
- Human approval reference if required: not required
- Escalation notes: none
- Protected areas touched: none

## Evidence
- Planning evidence: `evidence.planning`

## Overrides
None.

## Confirmation
- [x] The implementation matches the declared scope
- [x] Non-goals were respected
- [x] The linked workflow file governed this change
- [x] The workflow file existed before implementation and governed the work from the start
- [x] Scope, non-goals, and risk were fixed in the workflow before implementation started
- [x] Required workflow phases were executed as visible working steps, not only documented after the fact
"""
    path = tmp_path / "pr-body.md"
    path.write_text(body, encoding="utf-8")
    return path


def test_public_api_exports_stable_symbols_from_module_and_package_root() -> None:
    expected = {
        "WorkflowValidationError",
        "inspect_workflow",
        "validate_workflow",
        "validate_workflow_data",
        "validate_pr_body",
        "validate_github_approvals",
        "get_workflow_status",
        "audit_workflows",
        "start_workflow_phase",
        "complete_workflow_phase",
        "block_workflow_phase",
        "record_workflow_handoff",
    }

    assert expected.issubset(set(api.__all__))
    for name in expected:
        assert hasattr(api, name)
        assert hasattr(policyflow, name)


def test_public_api_validates_workflow_pr_body_and_github_approvals(tmp_path: Path) -> None:
    workflow_path = _create_workflow(tmp_path)
    pr_body_path = _write_pr_body(tmp_path)
    reviews_path = tmp_path / "reviews.json"
    reviews_path.write_text(json.dumps([]), encoding="utf-8")

    workflow = api.validate_workflow(workflow_path)
    inspected, warnings = api.inspect_workflow(workflow_path)
    pr_workflow = api.validate_pr_body(workflow_path, pr_body_path)
    approval_workflow = api.validate_github_approvals(
        workflow_path, pr_body_path, reviews_path
    )

    assert workflow.workflow.id == "api-feature"
    assert inspected.workflow.id == "api-feature"
    assert warnings == []
    assert pr_workflow.workflow.id == "api-feature"
    assert approval_workflow.workflow.id == "api-feature"


def test_public_api_reports_audit_and_mutates_runtime_state(tmp_path: Path) -> None:
    workflow_path = _create_workflow(
        tmp_path,
        workflow_type="bugfix",
        workflow_id="api-bugfix",
        risk_level="MEDIUM",
    )

    initial_status = api.get_workflow_status(workflow_path)
    audit = api.audit_workflows(tmp_path / "ai/workflows")

    assert initial_status["workflow_id"] == "api-bugfix"
    assert audit["workflows"][0]["workflow_id"] == "api-bugfix"

    api.start_workflow_phase(workflow_path, "implementation")
    started_status = policyflow.get_workflow_status(workflow_path)

    assert started_status["current_phase"] == "implementation"
    assert started_status["runtime_status"] == "in_progress"
