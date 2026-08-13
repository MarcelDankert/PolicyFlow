from __future__ import annotations

import sys
from pathlib import Path

import policyflow
from policyflow import api


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def fixture_path(name: str) -> Path:
    return FIXTURES_DIR / name


def test_public_api_exports_governance_only_symbols_from_module_and_root() -> None:
    expected = {
        "ApprovalValidationResult",
        "ValidationResultV2",
        "WorkflowDocument",
        "WorkflowDocumentV2",
        "WorkflowValidationError",
        "inspect_workflow",
        "inspect_workflow_v2",
        "inspect_workflow_v2_data",
        "validate_github_approvals",
        "validate_pr_body",
        "validate_workflow",
        "validate_workflow_data",
        "validate_workflow_v2",
        "validate_workflow_v2_data",
    }
    removed = {
        "audit_workflows",
        "block_workflow_phase",
        "complete_workflow_phase",
        "get_workflow_status",
        "record_workflow_handoff",
        "start_workflow_phase",
    }

    assert set(api.__all__) == expected
    assert expected.issubset(set(policyflow.__all__))
    for name in expected:
        assert hasattr(api, name)
        assert hasattr(policyflow, name)
    for name in removed:
        assert name not in api.__all__
        assert name not in policyflow.__all__
        assert not hasattr(api, name)
        assert not hasattr(policyflow, name)


def test_importing_policyflow_does_not_import_runtime_execution_modules() -> None:
    imported_policyflow_modules = {
        name for name in sys.modules if name == "policyflow" or name.startswith("policyflow.")
    }

    assert "policyflow.runtime" not in imported_policyflow_modules
    assert "policyflow.agent_execution" not in imported_policyflow_modules
    assert "policyflow.codex_runner" not in imported_policyflow_modules
    assert "policyflow.reporting" not in imported_policyflow_modules


def test_public_api_validates_v1_workflow_pr_body_and_github_approvals() -> None:
    workflow = api.validate_workflow(fixture_path("valid-high.yml"))
    inspected, warnings = api.inspect_workflow(fixture_path("valid-high.yml"))
    pr_workflow = api.validate_pr_body(
        fixture_path("valid-high.yml"),
        fixture_path("valid-high-pr-body.md"),
    )
    approval_result = api.validate_github_approvals(
        fixture_path("valid-high.yml"),
        fixture_path("valid-high-pr-body.md"),
        fixture_path("github-reviews-valid-high.json"),
    )

    assert workflow.workflow.id == "valid-high"
    assert inspected.workflow.id == "valid-high"
    assert warnings == []
    assert pr_workflow.workflow.id == "valid-high"
    assert approval_result.workflow.workflow.id == "valid-high"
    assert approval_result.status == "approved"


def test_public_api_validates_v2_governance_and_result_shape() -> None:
    workflow = api.validate_workflow_v2(fixture_path("valid-v2-governance.yml"))
    result = api.inspect_workflow_v2(fixture_path("valid-v2-governance.yml"))

    assert workflow.change.id == "example-change"
    assert result.decision == "PASS"
    assert result.merge_ready is True
    assert result.to_json_dict()["schema_version"] == "policyflow.validation.v2"
