from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner
import yaml

from policyflow.bootstrap import bootstrap_consumer_repo
from policyflow.cli import app
from policyflow.consumer_config import load_consumer_config


runner = CliRunner()


def test_bootstrap_fresh_repo_creates_consumer_layout(tmp_path: Path) -> None:
    result = bootstrap_consumer_repo(tmp_path)

    assert result.created
    assert not result.skipped
    assert (tmp_path / "policyflow.yml").exists()
    assert (tmp_path / "policyflow.runners.yml").exists()
    assert (tmp_path / "ai/project-context.yml").exists()
    assert (tmp_path / "ai/agents/planning-agent.md").exists()
    assert (tmp_path / "ai/prompts/planning-agent.prompt.md").exists()
    assert (tmp_path / "ai/rules/risk-classification.md").exists()
    assert (tmp_path / "ai/workflows/templates/feature-workflow.template.yml").exists()
    assert (tmp_path / "ai/workflows/features/starter-workflow.yml").exists()
    assert (tmp_path / ".github/PULL_REQUEST_TEMPLATE.md").exists()
    assert (tmp_path / ".github/ISSUE_TEMPLATE/feature.yml").exists()
    starter_workflow = (tmp_path / "ai/workflows/features/starter-workflow.yml").read_text(
        encoding="utf-8"
    )
    assert "confidence:" in starter_workflow
    assert "residual_uncertainty:" in starter_workflow

    runner_config = yaml.safe_load(
        (tmp_path / "policyflow.runners.yml").read_text(encoding="utf-8")
    )
    assert runner_config["default_runner"] == "command"
    command_runner = runner_config["runners"]["command"]
    assert command_runner["type"] == "command"
    assert command_runner["command"] == [
        "policyflow-runner",
        "--input",
        "{input_path}",
        "--output",
        "{output_path}",
    ]
    codex_runner = runner_config["runners"]["codex"]
    codex_command = codex_runner["command"]
    assert codex_runner["type"] == "codex"
    assert "scripts/policyflow_codex_wrapper.py" not in codex_command
    assert codex_command[:3] == ["{python_executable}", "-m", "policyflow.codex_runner"]

    config = load_consumer_config(tmp_path / "policyflow.yml")
    assert config.paths.workflows == Path("ai/workflows")

    metadata = json.loads(
        (tmp_path / ".policyflow/bootstrap.json").read_text(encoding="utf-8")
    )
    assert metadata["policyflow_version"] == "0.2.0"
    assert "policyflow.yml" in metadata["managed_assets"]
    assert "ai/workflows/templates/feature-workflow.template.yml" in metadata["managed_assets"]
    assert "ai/workflows/features/starter-workflow.yml" in metadata["managed_assets"]
    assert metadata["asset_hashes"]["policyflow.yml"]
    assert metadata["asset_hashes"]["ai/workflows/templates/feature-workflow.template.yml"]


def test_bootstrap_dry_run_does_not_write_files(tmp_path: Path) -> None:
    result = bootstrap_consumer_repo(tmp_path, dry_run=True)

    assert result.would_create
    assert not result.created
    assert not (tmp_path / "policyflow.yml").exists()
    assert not (tmp_path / "ai").exists()


def test_bootstrap_skips_existing_files_without_force(tmp_path: Path) -> None:
    existing = tmp_path / "policyflow.yml"
    existing.write_text("version: 1\n# local edit\n", encoding="utf-8")
    metadata = tmp_path / ".policyflow/bootstrap.json"
    metadata.parent.mkdir(parents=True)
    metadata.write_text('{"local": true}', encoding="utf-8")

    result = bootstrap_consumer_repo(tmp_path)

    assert "policyflow.yml" in result.skipped
    assert existing.read_text(encoding="utf-8") == "version: 1\n# local edit\n"
    assert metadata.read_text(encoding="utf-8") == '{"local": true}'


def test_bootstrap_force_overwrites_existing_files(tmp_path: Path) -> None:
    existing = tmp_path / "policyflow.yml"
    existing.write_text("not: policyflow\n", encoding="utf-8")

    result = bootstrap_consumer_repo(tmp_path, force=True)

    assert "policyflow.yml" in result.overwritten
    assert load_consumer_config(existing).version == 1


def test_init_command_reports_created_files(tmp_path: Path) -> None:
    result = runner.invoke(app, ["init", str(tmp_path)])

    assert result.exit_code == 0
    assert "[SUCCESS] PolicyFlow bootstrap completed." in result.stdout
    assert "created policyflow.yml" in result.stdout
    assert (tmp_path / "policyflow.yml").exists()


def test_init_command_supports_dry_run(tmp_path: Path) -> None:
    result = runner.invoke(app, ["init", str(tmp_path), "--dry-run"])

    assert result.exit_code == 0
    assert "would create policyflow.yml" in result.stdout
    assert not (tmp_path / "policyflow.yml").exists()
