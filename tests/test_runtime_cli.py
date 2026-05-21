from __future__ import annotations

import json
from pathlib import Path

import yaml
from typer.testing import CliRunner

from policyflow.cli import app
import policyflow.validator as validator_module


FIXTURES_DIR = Path(__file__).parent / "fixtures"
runner = CliRunner()


def fixture_path(name: str) -> Path:
    return FIXTURES_DIR / name


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def test_start_phase_updates_runtime_and_completes_pending_handoff(tmp_path: Path) -> None:
    workflow_path = tmp_path / "runtime-startable-medium.yml"
    workflow_path.write_text(
        fixture_path("runtime-startable-medium.yml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["start-phase", str(workflow_path), "implementation"])

    assert result.exit_code == 0
    data = load_yaml(workflow_path)
    assert data["runtime"]["status"] == "in_progress"
    assert data["runtime"]["current_phase"] == "implementation"
    assert data["execution"]["phases"][2]["state"] == "in_progress"
    assert data["handoffs"][0]["status"] == "completed"


def test_complete_phase_sets_runtime_idle_when_next_handoff_not_yet_recorded(
    tmp_path: Path,
) -> None:
    workflow_path = tmp_path / "runtime-completable-medium.yml"
    workflow_path.write_text(
        fixture_path("runtime-completable-medium.yml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["complete-phase", str(workflow_path), "implementation"])

    assert result.exit_code == 0
    data = load_yaml(workflow_path)
    assert data["runtime"]["status"] == "idle"
    assert data["execution"]["phases"][2]["state"] == "completed"


def test_record_handoff_writes_pending_handoff_with_artifacts(tmp_path: Path) -> None:
    workflow_path = tmp_path / "runtime-handoff-record.yml"
    workflow_path.write_text(
        fixture_path("runtime-handoff-record.yml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "record-handoff",
            str(workflow_path),
            "--from-phase",
            "implementation",
            "--to-phase",
            "review",
            "--required-input",
            "implementation_summary",
            "--required-input",
            "test_summary",
            "--produced-output",
            "review_findings",
        ],
    )

    assert result.exit_code == 0
    data = load_yaml(workflow_path)
    assert data["runtime"]["status"] == "handoff_pending"
    assert data["handoffs"][0]["required_inputs"] == [
        "implementation_summary",
        "test_summary",
    ]
    assert data["handoffs"][0]["produced_outputs"] == ["review_findings"]


def test_block_phase_marks_phase_and_runtime_blocked(tmp_path: Path) -> None:
    workflow_path = tmp_path / "runtime-blockable-medium.yml"
    workflow_path.write_text(
        fixture_path("runtime-blockable-medium.yml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "block-phase",
            str(workflow_path),
            "implementation",
            "--reason",
            "runtime contract uncertainty",
        ],
    )

    assert result.exit_code == 0
    data = load_yaml(workflow_path)
    assert data["runtime"]["status"] == "blocked"
    assert data["runtime"]["block_reason"] == "runtime contract uncertainty"
    assert data["execution"]["phases"][2]["state"] == "blocked"


def test_next_step_reports_pending_handoff(tmp_path: Path) -> None:
    workflow_path = tmp_path / "runtime-startable-medium.yml"
    workflow_path.write_text(
        fixture_path("runtime-startable-medium.yml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["next-step", str(workflow_path)])

    assert result.exit_code == 0
    assert "Pending handoff architecture-check -> implementation" in result.stdout


def test_handoff_status_lists_recorded_handoffs(tmp_path: Path) -> None:
    workflow_path = tmp_path / "runtime-startable-medium.yml"
    workflow_path.write_text(
        fixture_path("runtime-startable-medium.yml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["handoff-status", str(workflow_path)])

    assert result.exit_code == 0
    assert "architecture-check -> implementation [pending]" in result.stdout


def test_validate_reports_expiring_override_warning(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(
        validator_module, "_current_date", lambda: validator_module.date(2026, 5, 21)
    )
    workflow_path = tmp_path / "expiring-override.yml"
    workflow_path.write_text(
        fixture_path("expiring-override.yml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["validate", str(workflow_path)])

    assert result.exit_code == 0
    assert "[WARN]" in result.stdout
    assert "Override 'phase-bypass-1' is expiring soon" in result.stdout


def test_status_reports_handoff_and_merge_readiness(tmp_path: Path) -> None:
    workflow_path = tmp_path / "runtime-startable-medium.yml"
    workflow_path.write_text(
        fixture_path("runtime-startable-medium.yml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["status", str(workflow_path)])

    assert result.exit_code == 0
    assert "Workflow ID: runtime-startable-medium" in result.stdout
    assert "Runtime status: handoff_pending" in result.stdout
    assert "Open handoffs: 1" in result.stdout
    assert "Merge ready: no" in result.stdout


def test_status_json_reports_blocked_workflow(tmp_path: Path) -> None:
    workflow_path = tmp_path / "runtime-blockable-medium.yml"
    workflow_path.write_text(
        fixture_path("runtime-blockable-medium.yml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "block-phase",
            str(workflow_path),
            "implementation",
            "--reason",
            "runtime contract uncertainty",
        ],
    )
    assert result.exit_code == 0

    status_result = runner.invoke(app, ["status", str(workflow_path), "--json"])

    assert status_result.exit_code == 0
    payload = json.loads(status_result.stdout)
    assert payload["workflow_id"] == "runtime-blockable-medium"
    assert payload["runtime_status"] == "blocked"
    assert payload["blocked"] is True
    assert payload["merge_ready"] is False
    assert payload["blockers"] == ["runtime contract uncertainty"]


def test_audit_reports_multiple_workflows_and_invalid_entries(tmp_path: Path) -> None:
    valid_path = tmp_path / "runtime-startable-medium.yml"
    valid_path.write_text(
        fixture_path("runtime-startable-medium.yml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    invalid_path = tmp_path / "invalid-risk-level.yml"
    invalid_path.write_text(
        fixture_path("invalid-risk-level.yml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["audit", str(tmp_path)])

    assert result.exit_code == 0
    assert "runtime-startable-medium" in result.stdout
    assert "invalid-risk-level.yml" in result.stdout
    assert "invalid" in result.stdout


def test_audit_json_reports_invalid_workflow_entry(tmp_path: Path) -> None:
    valid_path = tmp_path / "runtime-startable-medium.yml"
    valid_path.write_text(
        fixture_path("runtime-startable-medium.yml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    invalid_path = tmp_path / "invalid-risk-level.yml"
    invalid_path.write_text(
        fixture_path("invalid-risk-level.yml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["audit", str(tmp_path), "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert len(payload["workflows"]) == 2
    invalid_entry = next(
        entry for entry in payload["workflows"] if entry["path"].endswith("invalid-risk-level.yml")
    )
    assert invalid_entry["valid"] is False
    assert "risk_level must be one of: LOW, MEDIUM, HIGH" in invalid_entry["errors"]
