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


def test_doctor_github_app_preflight_passes_with_governance_permissions(
    tmp_path: Path,
) -> None:
    bootstrap_consumer_repo(tmp_path)

    report = doctor_consumer_repo(
        tmp_path,
        github_app_preflight_repo="owner/repo",
        gh_runner=_fake_gh_runner(
            {
                "metadata": "read",
                "contents": "write",
                "issues": "write",
                "pull_requests": "write",
            }
        ),
    )

    checks = {check["check"]: check for check in report["checks"]}
    preflight = checks["github_app_governance_preflight"]
    assert preflight["status"] == "pass"
    assert "read metadata" in preflight["message"]
    assert "create branches" in preflight["message"]
    assert "push commits" in preflight["message"]
    assert "create/edit issues" in preflight["message"]
    assert "create/edit pull requests" in preflight["message"]
    assert "apply labels" in preflight["message"]
    assert "assign milestones" in preflight["message"]
    assert "read pull request reviews" in preflight["message"]


def test_doctor_github_app_preflight_reports_missing_permission_area(
    tmp_path: Path,
) -> None:
    bootstrap_consumer_repo(tmp_path)

    report = doctor_consumer_repo(
        tmp_path,
        github_app_preflight_repo="owner/repo",
        gh_runner=_fake_gh_runner(
            {
                "metadata": "read",
                "contents": "write",
                "issues": "read",
                "pull_requests": "write",
            }
        ),
    )

    assert report["ready"] is False
    checks = {check["check"]: check for check in report["checks"]}
    preflight = checks["github_app_governance_preflight"]
    assert preflight["status"] == "failure"
    assert "create/edit issues" in preflight["message"]
    assert "Issues: write" in preflight["message"]
    assert "apply labels" in preflight["message"]
    assert "assign milestones" in preflight["message"]
    assert "Configure the GitHub App installation" in preflight["remediation"]


def test_doctor_github_app_preflight_uses_read_probes_when_app_permissions_are_unavailable(
    tmp_path: Path,
) -> None:
    bootstrap_consumer_repo(tmp_path)
    calls: list[list[str]] = []

    def run_gh(args: list[str]) -> tuple[int, str, str]:
        calls.append(args)
        if args == ["api", "repos/owner/repo"]:
            return (
                0,
                json.dumps(
                    {
                        "permissions": {
                            "admin": False,
                            "maintain": False,
                            "pull": False,
                            "push": False,
                            "triage": False,
                        }
                    }
                ),
                "",
            )
        if args == ["api", "repos/owner/repo/installation"]:
            return 1, "", "A JSON web token could not be decoded"
        return 0, "[]", ""

    report = doctor_consumer_repo(
        tmp_path,
        github_app_preflight_repo="owner/repo",
        gh_runner=run_gh,
    )

    checks = {check["check"]: check for check in report["checks"]}
    preflight = checks["github_app_governance_preflight"]
    assert preflight["status"] == "pass"
    assert "verified non-mutating repository access" in preflight["message"]
    assert ["api", "repos/owner/repo/labels?per_page=1"] in calls
    assert ["api", "repos/owner/repo/milestones?per_page=1"] in calls
    assert ["api", "repos/owner/repo/pulls?per_page=1"] in calls


def test_doctor_github_app_preflight_cli_does_not_print_token_or_secret_path(
    tmp_path: Path,
    monkeypatch,
) -> None:
    bootstrap_consumer_repo(tmp_path)
    monkeypatch.setenv("GH_TOKEN", "ghs_super_secret_value")
    monkeypatch.setenv(
        "SENTINEL_FLOW_TOKEN_HELPER",
        "D:\\dev\\Sentinel-Flow\\token.ps1",
    )
    monkeypatch.setattr("policyflow.doctor.shutil.which", lambda _command: None)

    result = runner.invoke(
        app,
        ["doctor", str(tmp_path), "--github-app-preflight", "owner/repo"],
    )

    assert result.exit_code == 1
    assert "ghs_super_secret_value" not in result.stdout
    assert "D:\\dev\\Sentinel-Flow" not in result.stdout
    assert "GH_TOKEN" in result.stdout
    assert "GitHub CLI" in result.stdout


def _write_runner_command(tmp_path: Path, command: list[str]) -> None:
    runner_path = tmp_path / "policyflow.runners.yml"
    runner_data = yaml.safe_load(runner_path.read_text(encoding="utf-8"))
    runner_data["runners"][runner_data["default_runner"]]["command"] = command
    runner_path.write_text(yaml.safe_dump(runner_data, sort_keys=False), encoding="utf-8")


def _fake_gh_runner(permissions: dict[str, str]):
    def run_gh(_args: list[str]) -> tuple[int, str, str]:
        return 0, json.dumps({"permissions": permissions}), ""

    return run_gh
