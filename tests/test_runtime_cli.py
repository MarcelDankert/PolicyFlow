from __future__ import annotations

import json
import sys
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


def write_runner_config(
    path: Path, script_path: Path, mode: str = "success"
) -> Path:
    config_path = path / "policyflow.runners.yml"
    config_path.write_text(
        "\n".join(
            [
                "default_runner: codex",
                "runners:",
                "  codex:",
                "    type: codex",
                "    command:",
                f"      - {json.dumps(sys.executable)}",
                f"      - {json.dumps(str(script_path))}",
                "      - --input",
                "      - \"{input_path}\"",
                "      - --output",
                "      - \"{output_path}\"",
                "      - --mode",
                f"      - {mode}",
                "    prompt_paths:",
                "      planning: prompts/planning-agent.prompt.md",
                "      architecture-check: prompts/architecture-agent.prompt.md",
                "      implementation: prompts/senior-dev-agent.prompt.md",
                "      review: prompts/review-agent.prompt.md",
                "      qa: prompts/qa-agent.prompt.md",
                "    agent_paths:",
                "      planning: agents/planning-agent.md",
                "      architecture-check: agents/architecture-agent.md",
                "      implementation: agents/senior-dev-agent.md",
                "      review: agents/review-agent.md",
                "      qa: agents/qa-agent.md",
            ]
        ),
        encoding="utf-8",
    )
    return config_path


def write_mock_runner(path: Path) -> Path:
    script_path = path / "mock_codex_runner.py"
    script_path.write_text(
        "\n".join(
            [
                "import argparse",
                "import json",
                "from pathlib import Path",
                "",
                "parser = argparse.ArgumentParser()",
                "parser.add_argument('--input', required=True)",
                "parser.add_argument('--output', required=True)",
                "parser.add_argument('--mode', required=True)",
                "args = parser.parse_args()",
                "",
                "if args.mode == 'fail':",
                "    raise SystemExit(3)",
                "",
                "payload = json.loads(Path(args.input).read_text(encoding='utf-8'))",
                "phase = payload['phase']",
                "result = {",
                "    'phase': phase,",
                "    'owner_agent': payload['owner_agent'],",
                "    'status': 'completed',",
                "    'summary': 'Phase completed by mock Codex runner.',",
                "}",
                "if phase == 'implementation':",
                "    result['contract_updates'] = {",
                "        'owner_agent': 'senior-dev-agent',",
                "        'implementation_summary': 'Implemented the bounded parser validation slice.',",
                "        'changed_files': ['parser/module.py'],",
                "        'test_summary': 'Added parser validation tests.',",
                "        'docs_updates': ['docs/runtime-notes.md'],",
                "        'known_limitations': ['none'],",
                "        'unresolved_questions': ['none']",
                "    }",
                "    result['handoff'] = {",
                "        'to_phase': 'review',",
                "        'required_inputs': ['implementation_summary', 'test_summary'],",
                "        'produced_outputs': ['review_findings']",
                "    }",
                "Path(args.output).write_text(json.dumps(result), encoding='utf-8')",
            ]
        ),
        encoding="utf-8",
    )
    return script_path


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


def test_run_phase_executes_runner_and_records_handoff(tmp_path: Path) -> None:
    workflow_path = tmp_path / "runtime-startable-medium.yml"
    workflow_path.write_text(
        fixture_path("runtime-startable-medium.yml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    script_path = write_mock_runner(tmp_path)
    config_path = write_runner_config(tmp_path, script_path)

    result = runner.invoke(
        app,
        [
            "run-phase",
            str(workflow_path),
            "implementation",
            "--runner-config",
            str(config_path),
        ],
    )

    assert result.exit_code == 0
    data = load_yaml(workflow_path)
    assert data["execution"]["phases"][2]["state"] == "completed"
    assert data["contracts"]["implementation"]["owner_agent"] == "senior-dev-agent"
    assert data["runtime"]["status"] == "handoff_pending"
    assert data["runtime"]["current_phase"] == "implementation"
    assert data["handoffs"][-1]["to_phase"] == "review"


def test_run_phase_blocks_workflow_on_runner_failure(tmp_path: Path) -> None:
    workflow_path = tmp_path / "runtime-startable-medium.yml"
    workflow_path.write_text(
        fixture_path("runtime-startable-medium.yml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    script_path = write_mock_runner(tmp_path)
    config_path = write_runner_config(tmp_path, script_path, mode="fail")

    result = runner.invoke(
        app,
        [
            "run-phase",
            str(workflow_path),
            "implementation",
            "--runner-config",
            str(config_path),
        ],
    )

    assert result.exit_code == 1
    data = load_yaml(workflow_path)
    assert data["execution"]["phases"][2]["state"] == "blocked"
    assert data["runtime"]["status"] == "blocked"
