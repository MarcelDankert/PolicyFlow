from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from policyflow.bootstrap import bootstrap_consumer_repo
from policyflow.cli import app
from policyflow.doctor import doctor_consumer_repo


runner = CliRunner()


def test_doctor_passes_for_fresh_bootstrap(tmp_path: Path) -> None:
    bootstrap_consumer_repo(tmp_path)

    report = doctor_consumer_repo(tmp_path)

    assert report["ready"] is True
    assert report["failures"] == 0
    checks = {check["check"]: check for check in report["checks"]}
    assert checks["consumer_config"]["status"] == "pass"
    assert checks["bootstrap_artifacts"]["status"] == "pass"
    assert checks["runner_config"]["status"] == "pass"
    assert checks["project_context"]["status"] == "pass"
    assert checks["github_templates"]["status"] == "pass"


def test_doctor_reports_missing_bootstrap_files(tmp_path: Path) -> None:
    bootstrap_consumer_repo(tmp_path)
    (tmp_path / "ai/prompts/planning-agent.prompt.md").unlink()

    report = doctor_consumer_repo(tmp_path)

    assert report["ready"] is False
    assert report["failures"] == 1
    runner_check = next(
        check for check in report["checks"] if check["check"] == "runner_config"
    )
    assert runner_check["status"] == "failure"
    assert "ai/prompts/planning-agent.prompt.md" in runner_check["message"]
    assert "Run `policyflow init`" in runner_check["remediation"]


def test_doctor_reports_missing_consumer_config(tmp_path: Path) -> None:
    report = doctor_consumer_repo(tmp_path)

    assert report["ready"] is False
    config_check = next(
        check for check in report["checks"] if check["check"] == "consumer_config"
    )
    assert config_check["status"] == "failure"
    assert "policyflow.yml" in config_check["message"]


def test_doctor_command_outputs_json(tmp_path: Path) -> None:
    bootstrap_consumer_repo(tmp_path)

    result = runner.invoke(app, ["doctor", str(tmp_path), "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ready"] is True
    assert payload["failures"] == 0


def test_doctor_command_fails_on_missing_required_assets(tmp_path: Path) -> None:
    bootstrap_consumer_repo(tmp_path)
    (tmp_path / "ai/project-context.yml").unlink()

    result = runner.invoke(app, ["doctor", str(tmp_path)])

    assert result.exit_code == 1
    assert "[FAIL]" in result.stdout
    assert "project_context" in result.stdout
