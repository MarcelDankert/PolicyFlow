from pathlib import Path

import pytest
from typer.testing import CliRunner

from policyflow.cli import app
from policyflow.config import load_config
from policyflow.exceptions import WorkflowValidationError


runner = CliRunner()
ROOT = Path(__file__).resolve().parents[1]


def test_default_config_uses_minimal_v2_paths(tmp_path: Path) -> None:
    config_path = tmp_path / "policyflow.yml"
    config_path.write_text("version: 2\n", encoding="utf-8")

    config = load_config(config_path)

    assert config.version == 2
    assert config.paths.changes == Path("policyflow")
    assert config.paths.pr_template == Path(".github/PULL_REQUEST_TEMPLATE.md")
    assert config.paths.governance_workflow == Path(".github/workflows/policyflow.yml")
    assert config.github.enabled is True


def test_config_accepts_path_and_github_overrides(tmp_path: Path) -> None:
    config_path = tmp_path / "policyflow.yml"
    config_path.write_text(
        "\n".join(
            [
                "version: 2",
                "paths:",
                "  changes: governance",
                "  pr_template: .github/pull_request_template.md",
                "github:",
                "  enabled: false",
            ]
        ),
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.paths.changes == Path("governance")
    assert config.paths.pr_template == Path(".github/pull_request_template.md")
    assert config.github.enabled is False


def test_consumer_config_rejects_absolute_paths(tmp_path: Path) -> None:
    config_path = tmp_path / "policyflow.yml"
    config_path.write_text(
        "\n".join(
            [
                "version: 2",
                "paths:",
                "  changes: C:/tmp/workflows",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(WorkflowValidationError) as exc_info:
        load_config(config_path)

    assert "paths.changes must be a relative path" in exc_info.value.errors


def test_config_missing_file_fails_with_actionable_error(tmp_path: Path) -> None:
    with pytest.raises(WorkflowValidationError) as exc_info:
        load_config(tmp_path / "policyflow.yml")

    assert "PolicyFlow config file not found" in exc_info.value.errors[0]


def test_config_check_command_is_removed_from_v2_cli(tmp_path: Path) -> None:
    config_path = tmp_path / "policyflow.yml"
    config_path.write_text("version: 2\n", encoding="utf-8")

    result = runner.invoke(app, ["config-check", str(config_path)])

    assert result.exit_code == 2
    assert "No such command" in result.output


def test_config_check_invalid_config_is_handled_by_doctor_not_cli_command(tmp_path: Path) -> None:
    config_path = tmp_path / "policyflow.yml"
    config_path.write_text("version: 1\n", encoding="utf-8")

    result = runner.invoke(app, ["config-check", str(config_path)])

    assert result.exit_code == 2
    assert "No such command" in result.output


def test_published_consumer_config_examples_are_valid() -> None:
    minimal = load_config(ROOT / "examples" / "policyflow.minimal.yml")
    github_governed = load_config(ROOT / "examples" / "policyflow.github-governed.yml")

    assert minimal.github.enabled is False
    assert github_governed.github.enabled is True
    assert github_governed.paths.changes == Path("policyflow")
