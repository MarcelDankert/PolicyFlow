from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from policyflow.cli import app


FIXTURES_DIR = Path(__file__).parent / "fixtures"
runner = CliRunner()


def fixture_path(name: str) -> Path:
    return FIXTURES_DIR / name


def test_cli_help_exposes_only_v2_governance_commands() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    for command in ("init", "validate", "validate-pr", "doctor"):
        assert command in result.stdout
    for removed_command in (
        "audit",
        "block-phase",
        "complete-phase",
        "config-check",
        "evaluation-report",
        "handoff-status",
        "loop-report",
        "new-workflow",
        "next-step",
        "record-handoff",
        "run-phase",
        "start-phase",
        "status",
        "sync",
        "validate-github-approvals",
    ):
        assert removed_command not in result.stdout


def test_removed_runtime_command_is_not_registered() -> None:
    result = runner.invoke(app, ["run-phase", str(fixture_path("valid-low.yml")), "implementation"])

    assert result.exit_code != 0
    assert "No such command" in result.output


def test_validate_v2_json_reports_pass() -> None:
    result = runner.invoke(app, ["validate", str(fixture_path("valid-v2-governance.yml")), "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == "policyflow.validation.v2"
    assert payload["decision"] == "PASS"
    assert payload["merge_ready"] is True


def test_validate_v2_json_blocks_missing_required_evidence() -> None:
    result = runner.invoke(
        app,
        ["validate", str(fixture_path("v2-missing-required-evidence.yml")), "--json"],
    )

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["decision"] == "BLOCK"
    assert payload["merge_ready"] is False
    assert payload["errors"][0]["code"] == "missing_required_evidence"


def test_validate_pr_with_github_reviews_succeeds() -> None:
    result = runner.invoke(
        app,
        [
            "validate-pr",
            str(fixture_path("valid-high.yml")),
            str(fixture_path("valid-high-pr-body.md")),
            "--github-reviews",
            str(fixture_path("github-reviews-valid-high.json")),
        ],
    )

    assert result.exit_code == 0
    assert "[SUCCESS] Pull request validation passed." in result.stdout


def test_validate_pr_with_github_reviews_allows_pending_when_requested() -> None:
    result = runner.invoke(
        app,
        [
            "validate-pr",
            str(fixture_path("valid-high.yml")),
            str(fixture_path("valid-high-pr-body.md")),
            "--github-reviews",
            str(fixture_path("github-reviews-missing-human-approval.json")),
            "--allow-pending",
        ],
    )

    assert result.exit_code == 0
    assert "[PENDING] GitHub approval pending." in result.stdout
    assert "arch-board" in result.stdout


def test_validate_pr_with_github_reviews_json_reports_pending() -> None:
    result = runner.invoke(
        app,
        [
            "validate-pr",
            str(fixture_path("valid-high.yml")),
            str(fixture_path("valid-high-pr-body.md")),
            "--github-reviews",
            str(fixture_path("github-reviews-missing-human-approval.json")),
            "--allow-pending",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == "policyflow.pr_validation.v1"
    assert payload["decision"] == "WARN"
    assert payload["github_approval_status"] == "pending"
    assert payload["pending_logins"] == ["arch-board"]
