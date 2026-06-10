from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from policyflow.bootstrap import bootstrap_consumer_repo
from policyflow.cli import app
from policyflow.exceptions import WorkflowValidationError
from policyflow.validator import validate_workflow_file
from policyflow.workflow_generator import create_workflow_instance


runner = CliRunner()


def test_create_low_risk_workflow_uses_consumer_paths_and_validates(tmp_path: Path) -> None:
    bootstrap_consumer_repo(tmp_path)

    result = create_workflow_instance(
        tmp_path,
        workflow_type="feature",
        workflow_id="first-feature",
        risk_level="LOW",
    )

    workflow_path = tmp_path / "ai/workflows/features/first-feature.yml"
    assert result.created == ["ai/workflows/features/first-feature.yml"]
    assert workflow_path.exists()

    workflow = validate_workflow_file(workflow_path)
    assert workflow.workflow.id == "first-feature"
    assert workflow.workflow.type == "feature"
    assert workflow.context.workflow_file == "ai/workflows/features/first-feature.yml"
    assert workflow.context.risk_level == "LOW"
    assert workflow.governance.required_reviews == ["review-agent"]

    data = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    assert [phase["phase"] for phase in data["execution"]["phases"]] == [
        "planning",
        "implementation",
        "review",
    ]
    assert data["runtime"]["status"] == "idle"
    assert data["handoffs"] == []


@pytest.mark.parametrize(
    ("workflow_type", "risk_level", "expected_path", "expected_reviews", "expected_phases"),
    [
        (
            "bugfix",
            "MEDIUM",
            "ai/workflows/bugfixes/parser-fix.yml",
            ["architecture-agent", "review-agent", "qa-agent"],
            ["planning", "architecture-check", "implementation", "review", "qa"],
        ),
        (
            "architecture-change",
            "HIGH",
            "ai/workflows/architecture-changes/storage-boundary.yml",
            ["architecture-agent", "review-agent", "qa-agent", "human approval"],
            ["planning", "architecture-check", "implementation", "review", "qa", "approval"],
        ),
    ],
)
def test_create_medium_and_high_workflows_validate(
    tmp_path: Path,
    workflow_type: str,
    risk_level: str,
    expected_path: str,
    expected_reviews: list[str],
    expected_phases: list[str],
) -> None:
    bootstrap_consumer_repo(tmp_path)
    workflow_id = Path(expected_path).stem

    create_workflow_instance(
        tmp_path,
        workflow_type=workflow_type,
        workflow_id=workflow_id,
        risk_level=risk_level,
    )

    data = yaml.safe_load((tmp_path / expected_path).read_text(encoding="utf-8"))
    workflow = validate_workflow_file(tmp_path / expected_path)

    assert workflow.workflow.type == workflow_type
    assert workflow.context.workflow_file == expected_path
    assert workflow.context.risk_level == risk_level
    assert workflow.governance.required_reviews == expected_reviews
    assert [phase["phase"] for phase in data["execution"]["phases"]] == expected_phases


def test_new_workflow_dry_run_reports_without_writing(tmp_path: Path) -> None:
    bootstrap_consumer_repo(tmp_path)

    result = create_workflow_instance(
        tmp_path,
        workflow_type="feature",
        workflow_id="preview-feature",
        risk_level="LOW",
        dry_run=True,
    )

    assert result.would_create == ["ai/workflows/features/preview-feature.yml"]
    assert not (tmp_path / "ai/workflows/features/preview-feature.yml").exists()


def test_new_workflow_protects_existing_files(tmp_path: Path) -> None:
    bootstrap_consumer_repo(tmp_path)
    existing = tmp_path / "ai/workflows/features/existing.yml"
    existing.write_text("local: edit\n", encoding="utf-8")

    with pytest.raises(WorkflowValidationError) as exc_info:
        create_workflow_instance(
            tmp_path,
            workflow_type="feature",
            workflow_id="existing",
            risk_level="LOW",
        )

    assert "already exists" in exc_info.value.errors[0]
    assert existing.read_text(encoding="utf-8") == "local: edit\n"


def test_new_workflow_force_overwrites_existing_file(tmp_path: Path) -> None:
    bootstrap_consumer_repo(tmp_path)
    existing = tmp_path / "ai/workflows/features/existing.yml"
    existing.write_text("local: edit\n", encoding="utf-8")

    result = create_workflow_instance(
        tmp_path,
        workflow_type="feature",
        workflow_id="existing",
        risk_level="LOW",
        force=True,
    )

    assert result.overwritten == ["ai/workflows/features/existing.yml"]
    validate_workflow_file(existing)


def test_new_workflow_command_creates_valid_workflow(tmp_path: Path) -> None:
    bootstrap_consumer_repo(tmp_path)

    result = runner.invoke(
        app,
        [
            "new-workflow",
            "feature",
            "--id",
            "cli-feature",
            "--risk",
            "LOW",
            "--target",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    assert "created ai/workflows/features/cli-feature.yml" in result.stdout
    validate_workflow_file(tmp_path / "ai/workflows/features/cli-feature.yml")
