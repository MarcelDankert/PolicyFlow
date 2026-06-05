from pathlib import Path

import pytest
from typer.testing import CliRunner

from policyflow.cli import app
from policyflow.consumer_config import load_consumer_config
from policyflow.exceptions import WorkflowValidationError


runner = CliRunner()
ROOT = Path(__file__).resolve().parents[1]


def test_default_consumer_config_uses_plug_and_play_paths(tmp_path: Path) -> None:
    config_path = tmp_path / "policyflow.yml"
    config_path.write_text("version: 1\n", encoding="utf-8")

    config = load_consumer_config(config_path)

    assert config.version == 1
    assert config.paths.workflows == Path("ai/workflows")
    assert config.paths.prompts == Path("ai/prompts")
    assert config.paths.agents == Path("ai/agents")
    assert config.paths.rules == Path("ai/rules")
    assert config.paths.project_context == Path("ai/project-context.yml")
    assert config.paths.runner_config == Path("policyflow.runners.yml")
    assert config.paths.pr_template == Path(".github/PULL_REQUEST_TEMPLATE.md")
    assert config.paths.issue_templates == Path(".github/ISSUE_TEMPLATE")
    assert config.paths.governance_workflow == Path(
        ".github/workflows/policyflow-governance.yml"
    )
    assert config.features.pr_validation is True
    assert config.features.github_approval_checks is True
    assert config.features.runner_execution is True
    assert config.features.bootstrap_managed_assets is True
    assert config.bootstrap.managed_assets == []


def test_consumer_config_accepts_path_and_feature_overrides(tmp_path: Path) -> None:
    config_path = tmp_path / "policyflow.yml"
    config_path.write_text(
        "\n".join(
            [
                "version: 1",
                "paths:",
                "  workflows: workflows",
                "  prompts: prompts",
                "  agents: agents",
                "features:",
                "  github_approval_checks: false",
                "  runner_execution: false",
                "bootstrap:",
                "  managed_assets:",
                "    - ai/workflows",
                "    - .github/PULL_REQUEST_TEMPLATE.md",
            ]
        ),
        encoding="utf-8",
    )

    config = load_consumer_config(config_path)

    assert config.paths.workflows == Path("workflows")
    assert config.paths.prompts == Path("prompts")
    assert config.paths.agents == Path("agents")
    assert config.paths.rules == Path("ai/rules")
    assert config.features.github_approval_checks is False
    assert config.features.runner_execution is False
    assert config.bootstrap.managed_assets == [
        Path("ai/workflows"),
        Path(".github/PULL_REQUEST_TEMPLATE.md"),
    ]


def test_consumer_config_rejects_absolute_paths(tmp_path: Path) -> None:
    config_path = tmp_path / "policyflow.yml"
    config_path.write_text(
        "\n".join(
            [
                "version: 1",
                "paths:",
                "  workflows: C:/tmp/workflows",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(WorkflowValidationError) as exc_info:
        load_consumer_config(config_path)

    assert "paths.workflows must be a relative path" in exc_info.value.errors


def test_consumer_config_missing_file_fails_with_actionable_error(tmp_path: Path) -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        load_consumer_config(tmp_path / "policyflow.yml")

    assert "Consumer config file not found" in exc_info.value.errors[0]


def test_config_check_command_reports_valid_config(tmp_path: Path) -> None:
    config_path = tmp_path / "policyflow.yml"
    config_path.write_text("version: 1\n", encoding="utf-8")

    result = runner.invoke(app, ["config-check", str(config_path)])

    assert result.exit_code == 0
    assert "[SUCCESS] Consumer config validation passed." in result.stdout


def test_config_check_command_reports_invalid_config(tmp_path: Path) -> None:
    config_path = tmp_path / "policyflow.yml"
    config_path.write_text("version: 2\n", encoding="utf-8")

    result = runner.invoke(app, ["config-check", str(config_path)])

    assert result.exit_code == 1
    assert "[ERROR] Consumer config validation failed." in result.stdout
    assert "version must be 1" in result.stdout


def test_published_consumer_config_examples_are_valid() -> None:
    minimal = load_consumer_config(ROOT / "examples" / "policyflow.minimal.yml")
    github_governed = load_consumer_config(
        ROOT / "examples" / "policyflow.github-governed.yml"
    )

    assert minimal.features.pr_validation is False
    assert minimal.features.github_approval_checks is False
    assert minimal.features.runner_execution is False
    assert github_governed.features.pr_validation is True
    assert github_governed.features.github_approval_checks is True
    assert github_governed.bootstrap.managed_assets
