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
    assert checks["config"]["status"] == "pass"
    assert checks["change_example"]["status"] == "pass"
    assert "runner_config" not in checks
    assert "project_context" not in checks
    assert "github_cli" not in checks
    assert "github_app_governance_preflight" not in checks
    assert checks["github_templates"]["status"] == "pass"


def test_doctor_reports_missing_change_example(tmp_path: Path) -> None:
    bootstrap_consumer_repo(tmp_path)
    (tmp_path / "policyflow/change.example.yml").unlink()

    report = doctor_consumer_repo(tmp_path)

    assert report["ready"] is False
    assert report["failures"] == 1
    change_check = next(
        check for check in report["checks"] if check["check"] == "change_example"
    )
    assert change_check["status"] == "failure"
    assert "policyflow/change.example.yml" in change_check["message"]
    assert "Run `policyflow init`" in change_check["remediation"]


def test_doctor_reports_missing_consumer_config(tmp_path: Path) -> None:
    report = doctor_consumer_repo(tmp_path)

    assert report["ready"] is False
    config_check = next(
        check for check in report["checks"] if check["check"] == "config"
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
    (tmp_path / ".github/workflows/policyflow.yml").unlink()

    result = runner.invoke(app, ["doctor", str(tmp_path)])

    assert result.exit_code == 1
    assert "[FAIL]" in result.stdout
    assert "github_templates" in result.stdout


def test_doctor_cli_rejects_removed_github_app_preflight_option(tmp_path: Path) -> None:
    bootstrap_consumer_repo(tmp_path)

    result = runner.invoke(
        app,
        ["doctor", str(tmp_path), "--github-app-preflight", "owner/repo"],
    )

    assert result.exit_code == 2
    assert "No such option" in result.output
