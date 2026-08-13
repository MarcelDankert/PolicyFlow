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
    assert "runner_config" not in checks
    assert checks["project_context"]["status"] == "pass"
    assert checks["github_templates"]["status"] == "pass"


def test_doctor_reports_missing_bootstrap_files(tmp_path: Path) -> None:
    bootstrap_consumer_repo(tmp_path)
    (tmp_path / ".policyflow/bootstrap.json").unlink()

    report = doctor_consumer_repo(tmp_path)

    assert report["ready"] is False
    assert report["failures"] == 1
    bootstrap_check = next(
        check for check in report["checks"] if check["check"] == "bootstrap_artifacts"
    )
    assert bootstrap_check["status"] == "failure"
    assert ".policyflow/bootstrap.json" in bootstrap_check["message"]
    assert "Run `policyflow init`" in bootstrap_check["remediation"]


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

def _fake_gh_runner(permissions: dict[str, str]):
    def run_gh(_args: list[str]) -> tuple[int, str, str]:
        return 0, json.dumps({"permissions": permissions}), ""

    return run_gh
