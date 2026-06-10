from __future__ import annotations

import json
from pathlib import Path
import sys

from typer.testing import CliRunner
import yaml

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
    assert checks["runner_config"]["status"] == "warning"
    assert "policyflow-runner" in checks["runner_config"]["message"]
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


def test_doctor_fails_missing_local_runner_script(tmp_path: Path) -> None:
    bootstrap_consumer_repo(tmp_path)
    _write_runner_command(
        tmp_path,
        ["python", "scripts/policyflow_codex_wrapper.py", "--input", "{input_path}"],
    )

    report = doctor_consumer_repo(tmp_path)

    assert report["ready"] is False
    runner_check = next(
        check for check in report["checks"] if check["check"] == "runner_config"
    )
    assert runner_check["status"] == "failure"
    assert "scripts/policyflow_codex_wrapper.py" in runner_check["message"]
    assert "missing local runner command path" in runner_check["message"]


def test_doctor_fails_unsupported_runner_command_placeholder(tmp_path: Path) -> None:
    bootstrap_consumer_repo(tmp_path)
    _write_runner_command(
        tmp_path,
        [
            "{python_executable}",
            "-m",
            "policyflow.codex_runner",
            "--input",
            "{input_path}",
            "--mystery",
            "{unsupported_path}",
        ],
    )

    report = doctor_consumer_repo(tmp_path)

    assert report["ready"] is False
    runner_check = next(
        check for check in report["checks"] if check["check"] == "runner_config"
    )
    assert runner_check["status"] == "failure"
    assert "{unsupported_path}" in runner_check["message"]
    assert "unsupported runner command placeholder" in runner_check["message"]


def test_doctor_passes_packaged_runner_module_command(tmp_path: Path) -> None:
    bootstrap_consumer_repo(tmp_path)
    _write_runner_command(
        tmp_path,
        [
            "{python_executable}",
            "-m",
            "policyflow.codex_runner",
            "--input",
            "{input_path}",
            "--output",
            "{output_path}",
        ],
    )

    report = doctor_consumer_repo(tmp_path)

    runner_check = next(
        check for check in report["checks"] if check["check"] == "runner_config"
    )
    assert runner_check["status"] == "pass"


def test_doctor_passes_existing_fake_runner_command_path(tmp_path: Path) -> None:
    bootstrap_consumer_repo(tmp_path)
    runner_script = tmp_path / "scripts/fake-runner.py"
    runner_script.parent.mkdir()
    runner_script.write_text("print('fake runner')\n", encoding="utf-8")
    _write_runner_command(
        tmp_path,
        [sys.executable, "scripts/fake-runner.py", "--input", "{input_path}"],
    )

    report = doctor_consumer_repo(tmp_path)

    runner_check = next(
        check for check in report["checks"] if check["check"] == "runner_config"
    )
    assert runner_check["status"] == "pass"


def test_doctor_warns_when_external_provider_command_is_missing(tmp_path: Path) -> None:
    bootstrap_consumer_repo(tmp_path)
    _write_runner_command(
        tmp_path,
        [
            "missing-policyflow-provider-cli",
            "--input",
            "{input_path}",
            "--output",
            "{output_path}",
        ],
    )

    report = doctor_consumer_repo(tmp_path)

    assert report["ready"] is True
    assert report["warnings"] == 1
    runner_check = next(
        check for check in report["checks"] if check["check"] == "runner_config"
    )
    assert runner_check["status"] == "warning"
    assert "missing-policyflow-provider-cli" in runner_check["message"]
    assert "not found on PATH" in runner_check["message"]


def _write_runner_command(tmp_path: Path, command: list[str]) -> None:
    runner_path = tmp_path / "policyflow.runners.yml"
    runner_data = yaml.safe_load(runner_path.read_text(encoding="utf-8"))
    runner_data["runners"][runner_data["default_runner"]]["command"] = command
    runner_path.write_text(yaml.safe_dump(runner_data, sort_keys=False), encoding="utf-8")
