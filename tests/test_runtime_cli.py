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


def write_fake_codex(path: Path) -> Path:
    fake_codex_script = path / "fake-codex.py"
    fake_codex_script.write_text(
        "\n".join(
            [
                "#!/usr/bin/env python3",
                "import json",
                "import sys",
                "from pathlib import Path",
                "",
                "output_path = None",
                "for index, arg in enumerate(sys.argv):",
                "    if arg == '-o' and index + 1 < len(sys.argv):",
                "        output_path = Path(sys.argv[index + 1])",
                "if output_path is None:",
                "    raise SystemExit('missing -o output path')",
                "result = {",
                "    'phase': 'implementation',",
                "    'owner_agent': 'senior-dev-agent',",
                "    'status': 'completed',",
                "    'summary': 'Phase completed by fake Codex CLI.',",
                "    'contract_updates': {",
                "        'owner_agent': 'senior-dev-agent',",
                "        'implementation_summary': 'Implemented the bounded parser validation slice.',",
                "        'changed_files': ['parser/module.py'],",
                "        'test_summary': 'Added parser validation tests.',",
                "        'docs_updates': ['docs/runtime-notes.md'],",
                "        'known_limitations': ['none'],",
                "        'unresolved_questions': ['none']",
                "    },",
                "    'handoff': {",
                "        'to_phase': 'review',",
                "        'required_inputs': ['implementation_summary', 'test_summary'],",
                "        'produced_outputs': ['review_findings']",
                "    }",
                "}",
                "output_path.write_text(json.dumps(result), encoding='utf-8')",
            ]
        ),
        encoding="utf-8",
    )
    fake_codex_script.chmod(0o755)

    if sys.platform == "win32":
        script_path = path / "fake-codex.cmd"
        script_path.write_text(
            f'@echo off\n"{sys.executable}" "{fake_codex_script}" %*\n',
            encoding="utf-8",
        )
        return script_path

    script_path = path / "fake-codex"
    script_path.write_text(fake_codex_script.read_text(encoding="utf-8"), encoding="utf-8")
    script_path.chmod(0o755)
    return script_path


def write_packaged_codex_runner_config(path: Path, fake_codex_path: Path) -> Path:
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
                "      - -m",
                "      - policyflow.codex_runner",
                "      - --input",
                "      - \"{input_path}\"",
                "      - --output",
                "      - \"{output_path}\"",
                "      - --codex-command",
                f"      - {json.dumps(str(fake_codex_path))}",
            ]
        ),
        encoding="utf-8",
    )
    return config_path


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


def test_audit_json_reports_loop_and_evaluation_governance(tmp_path: Path) -> None:
    evaluation_path = tmp_path / "evaluation-governance-workflow.yml"
    evaluation_path.write_text(
        Path("workflows/examples/evaluation-governance-workflow.yml").read_text(
            encoding="utf-8"
        ),
        encoding="utf-8",
    )
    loop_path = tmp_path / "loop-governance-workflow.yml"
    loop_path.write_text(
        Path("workflows/examples/loop-governance-workflow.yml").read_text(
            encoding="utf-8"
        ),
        encoding="utf-8",
    )
    plain_path = tmp_path / "runtime-startable-medium.yml"
    plain_path.write_text(
        fixture_path("runtime-startable-medium.yml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["audit", str(tmp_path), "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    evaluation_entry = next(
        entry
        for entry in payload["workflows"]
        if entry["workflow_id"] == "evaluation-governance-workflow"
    )
    loop_entry = next(
        entry
        for entry in payload["workflows"]
        if entry["workflow_id"] == "loop-governance-workflow"
    )
    plain_entry = next(
        entry
        for entry in payload["workflows"]
        if entry["workflow_id"] == "runtime-startable-medium"
    )

    assert evaluation_entry["valid"] is True
    assert evaluation_entry["merge_ready"] is True
    assert evaluation_entry["evaluation"]["declared"] is True
    assert evaluation_entry["evaluation"]["compliance_status"] == "passed"
    assert evaluation_entry["evaluation"]["categories"] == 6
    assert evaluation_entry["evaluation"]["required_metrics"] == 3
    assert evaluation_entry["evaluation"]["blocking_metrics"] == 3
    assert evaluation_entry["evaluation"]["failed_metrics"] == 0
    assert evaluation_entry["evaluation"]["blocking_failed_metrics"] == 0
    assert evaluation_entry["evaluation"]["errors"] == []

    assert loop_entry["loop_governance"]["declared"] is True
    assert loop_entry["loop_governance"]["compliance_status"] == "passed"
    assert loop_entry["loop_governance"]["total_loops"] == 5
    assert loop_entry["loop_governance"]["status_counts"] == {
        "active": 2,
        "completed": 1,
        "escalated": 1,
        "terminated": 1,
    }
    assert loop_entry["loop_governance"]["errors"] == []

    assert plain_entry["loop_governance"] == {
        "declared": False,
        "compliance_status": "not_declared",
        "total_loops": 0,
        "status_counts": {},
        "errors": [],
    }
    assert plain_entry["evaluation"] == {
        "declared": False,
        "compliance_status": "not_declared",
        "categories": 0,
        "required_metrics": 0,
        "blocking_metrics": 0,
        "failed_metrics": 0,
        "blocking_failed_metrics": 0,
        "errors": [],
    }


def test_audit_summarizes_invalid_loop_and_evaluation_governance(
    tmp_path: Path,
) -> None:
    invalid_loop_path = tmp_path / "loop-governance-invalid-max.yml"
    invalid_loop_path.write_text(
        fixture_path("loop-governance-invalid-max.yml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    invalid_evaluation_path = tmp_path / "evaluation-threshold-mismatch.yml"
    invalid_evaluation_path.write_text(
        fixture_path("evaluation-threshold-mismatch.yml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    json_result = runner.invoke(app, ["audit", str(tmp_path), "--json"])
    text_result = runner.invoke(app, ["audit", str(tmp_path)])

    assert json_result.exit_code == 0
    payload = json.loads(json_result.stdout)
    invalid_loop_entry = next(
        entry
        for entry in payload["workflows"]
        if entry["path"].endswith("loop-governance-invalid-max.yml")
    )
    invalid_evaluation_entry = next(
        entry
        for entry in payload["workflows"]
        if entry["path"].endswith("evaluation-threshold-mismatch.yml")
    )

    assert invalid_loop_entry["valid"] is False
    assert invalid_loop_entry["loop_governance"]["declared"] is True
    assert invalid_loop_entry["loop_governance"]["compliance_status"] == "failed"
    assert invalid_loop_entry["loop_governance"]["total_loops"] == 1
    assert invalid_loop_entry["loop_governance"]["errors"] == [
        "loop_governance loop 'review-feedback' declaration error: max_iterations must be a positive integer."
    ]

    assert invalid_evaluation_entry["valid"] is False
    assert invalid_evaluation_entry["evaluation"]["declared"] is True
    assert invalid_evaluation_entry["evaluation"]["compliance_status"] == "failed"
    assert invalid_evaluation_entry["evaluation"]["categories"] == 2
    assert invalid_evaluation_entry["evaluation"]["failed_metrics"] == 2
    assert invalid_evaluation_entry["evaluation"]["errors"] == [
        "evaluation metric 'tests.tests-passed' references missing workflow evidence 'evidence.qa'.",
        "evaluation metric 'coverage.coverage-percent' actual_value 72 does not satisfy threshold greater_than_or_equal 80.",
    ]

    assert text_result.exit_code == 0
    assert "loop=failed" in text_result.stdout
    assert "evaluation=failed" in text_result.stdout


def test_evaluation_report_json_summarizes_compliant_directory(tmp_path: Path) -> None:
    evaluation_path = tmp_path / "evaluation-governance-workflow.yml"
    evaluation_path.write_text(
        Path("workflows/examples/evaluation-governance-workflow.yml").read_text(
            encoding="utf-8"
        ),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["evaluation-report", str(tmp_path), "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["summary"] == {
        "total_workflows": 1,
        "evaluations_declared": 1,
        "missing_required_evaluations": 0,
        "passed": 1,
        "failed": 0,
        "failing_gates": 0,
        "missing_evidence_references": 0,
    }
    assert payload["workflows"] == [
        {
            "path": str(evaluation_path),
            "workflow_id": "evaluation-governance-workflow",
            "valid": True,
            "declared": True,
            "compliance_status": "passed",
            "missing_required_evaluation": False,
            "failing_gates": [],
            "missing_evidence_references": [],
            "errors": [],
        }
    ]


def test_evaluation_report_identifies_non_compliant_directory(
    tmp_path: Path,
) -> None:
    plain_path = tmp_path / "runtime-startable-medium.yml"
    plain_path.write_text(
        fixture_path("runtime-startable-medium.yml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    missing_evidence_path = tmp_path / "evaluation-threshold-mismatch.yml"
    missing_evidence_path.write_text(
        fixture_path("evaluation-threshold-mismatch.yml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    failing_gate_path = tmp_path / "evaluation-metrics-non-compliant.yml"
    failing_gate_path.write_text(
        fixture_path("evaluation-metrics-non-compliant.yml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    json_result = runner.invoke(app, ["evaluation-report", str(tmp_path), "--json"])
    text_result = runner.invoke(app, ["evaluation-report", str(tmp_path)])

    assert json_result.exit_code == 0
    payload = json.loads(json_result.stdout)
    assert payload["summary"] == {
        "total_workflows": 3,
        "evaluations_declared": 2,
        "missing_required_evaluations": 1,
        "passed": 0,
        "failed": 2,
        "failing_gates": 2,
        "missing_evidence_references": 1,
    }

    plain_entry = next(
        entry
        for entry in payload["workflows"]
        if entry["path"].endswith("runtime-startable-medium.yml")
    )
    missing_evidence_entry = next(
        entry
        for entry in payload["workflows"]
        if entry["path"].endswith("evaluation-threshold-mismatch.yml")
    )
    failing_gate_entry = next(
        entry
        for entry in payload["workflows"]
        if entry["path"].endswith("evaluation-metrics-non-compliant.yml")
    )

    assert plain_entry["missing_required_evaluation"] is True
    assert plain_entry["compliance_status"] == "missing"
    assert missing_evidence_entry["missing_evidence_references"] == [
        "evaluation metric 'tests.tests-passed' references missing workflow evidence 'evidence.qa'."
    ]
    assert missing_evidence_entry["failing_gates"] == [
        "evaluation metric 'coverage.coverage-percent' actual_value 72 does not satisfy threshold greater_than_or_equal 80."
    ]
    assert failing_gate_entry["failing_gates"] == [
        "evaluation metric 'qa.unresolved-risk-count' actual_value 2 does not satisfy threshold equals 0."
    ]

    assert text_result.exit_code == 0
    assert "missing_required_evaluation=yes" in text_result.stdout
    assert "missing_evidence_refs=1" in text_result.stdout
    assert "failing_gates=1" in text_result.stdout


def test_loop_report_json_summarizes_review_and_qa_loops(tmp_path: Path) -> None:
    loop_path = tmp_path / "loop-governance-workflow.yml"
    loop_path.write_text(
        Path("workflows/examples/loop-governance-workflow.yml").read_text(
            encoding="utf-8"
        ),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["loop-report", str(tmp_path), "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["summary"] == {
        "total_workflows": 1,
        "loops_declared": 1,
        "missing_loop_governance": 0,
        "passed": 1,
        "failed": 0,
        "total_loops": 5,
        "exceeded_iterations": 0,
        "missing_stop_evidence": 0,
        "missing_escalation_evidence": 0,
        "unresolved_blocked_loops": 1,
    }
    assert payload["workflows"] == [
        {
            "path": str(loop_path),
            "workflow_id": "loop-governance-workflow",
            "valid": True,
            "declared": True,
            "compliance_status": "passed",
            "missing_loop_governance": False,
            "total_loops": 5,
            "status_counts": {
                "active": 2,
                "completed": 1,
                "escalated": 1,
                "terminated": 1,
            },
            "exceeded_iterations": [],
            "missing_stop_evidence": [],
            "missing_escalation_evidence": [],
            "unresolved_blocked_loops": ["security-review"],
            "errors": [],
        }
    ]


def test_loop_report_identifies_non_compliant_directory(tmp_path: Path) -> None:
    plain_path = tmp_path / "runtime-startable-medium.yml"
    plain_path.write_text(
        fixture_path("runtime-startable-medium.yml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    exceeded_path = tmp_path / "loop-governance-iteration-exceeded.yml"
    exceeded_path.write_text(
        fixture_path("loop-governance-iteration-exceeded.yml").read_text(
            encoding="utf-8"
        ),
        encoding="utf-8",
    )

    missing_stop = load_yaml(Path("workflows/examples/loop-governance-workflow.yml"))
    missing_stop["workflow"]["id"] = "loop-missing-stop-evidence"
    missing_stop["context"]["workflow_file"] = str(tmp_path / "loop-missing-stop-evidence.yml")
    missing_stop["loop_governance"]["loops"][1]["evidence_refs"] = [
        "evidence.qa",
        "artifact://regression-report",
    ]
    missing_stop_path = tmp_path / "loop-missing-stop-evidence.yml"
    missing_stop_path.write_text(yaml.safe_dump(missing_stop, sort_keys=False), encoding="utf-8")

    missing_escalation = load_yaml(Path("workflows/examples/loop-governance-workflow.yml"))
    missing_escalation["workflow"]["id"] = "loop-missing-escalation-evidence"
    missing_escalation["context"]["workflow_file"] = str(
        tmp_path / "loop-missing-escalation-evidence.yml"
    )
    missing_escalation["loop_governance"]["loops"][2]["evidence_refs"] = [
        "evidence.review",
        "artifact://security-report",
    ]
    missing_escalation_path = tmp_path / "loop-missing-escalation-evidence.yml"
    missing_escalation_path.write_text(
        yaml.safe_dump(missing_escalation, sort_keys=False), encoding="utf-8"
    )

    json_result = runner.invoke(app, ["loop-report", str(tmp_path), "--json"])
    text_result = runner.invoke(app, ["loop-report", str(tmp_path)])

    assert json_result.exit_code == 0
    payload = json.loads(json_result.stdout)
    assert payload["summary"] == {
        "total_workflows": 4,
        "loops_declared": 3,
        "missing_loop_governance": 1,
        "passed": 0,
        "failed": 3,
        "total_loops": 11,
        "exceeded_iterations": 1,
        "missing_stop_evidence": 1,
        "missing_escalation_evidence": 1,
        "unresolved_blocked_loops": 2,
    }

    plain_entry = next(
        entry
        for entry in payload["workflows"]
        if entry["path"].endswith("runtime-startable-medium.yml")
    )
    exceeded_entry = next(
        entry
        for entry in payload["workflows"]
        if entry["path"].endswith("loop-governance-iteration-exceeded.yml")
    )
    missing_stop_entry = next(
        entry
        for entry in payload["workflows"]
        if entry["path"].endswith("loop-missing-stop-evidence.yml")
    )
    missing_escalation_entry = next(
        entry
        for entry in payload["workflows"]
        if entry["path"].endswith("loop-missing-escalation-evidence.yml")
    )

    assert plain_entry["missing_loop_governance"] is True
    assert plain_entry["compliance_status"] == "missing"
    assert exceeded_entry["exceeded_iterations"] == [
        "loop_governance loop 'review-feedback' compliance failure: current_iteration 4 exceeds max_iterations 3."
    ]
    assert missing_stop_entry["missing_stop_evidence"] == [
        "loop_governance loop 'qa-regression' compliance failure: completed or terminated loops must reference at least one declared stop condition in evidence_refs."
    ]
    assert missing_escalation_entry["missing_escalation_evidence"] == [
        "loop_governance loop 'security-review' compliance failure: escalated loops must reference at least one declared escalation condition in evidence_refs."
    ]

    assert text_result.exit_code == 0
    assert "missing_loop_governance=yes" in text_result.stdout
    assert "exceeded_iterations=1" in text_result.stdout
    assert "missing_stop_evidence=1" in text_result.stdout
    assert "missing_escalation_evidence=1" in text_result.stdout


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


def test_run_phase_executes_packaged_codex_wrapper(tmp_path: Path) -> None:
    workflow_path = tmp_path / "runtime-startable-medium.yml"
    workflow_path.write_text(
        fixture_path("runtime-startable-medium.yml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    fake_codex_path = write_fake_codex(tmp_path)
    config_path = write_packaged_codex_runner_config(tmp_path, fake_codex_path)

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
    assert data["handoffs"][-1]["produced_outputs"] == ["review_findings"]


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
