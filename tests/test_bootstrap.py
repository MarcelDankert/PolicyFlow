from __future__ import annotations

from pathlib import Path

import yaml
from typer.testing import CliRunner

from policyflow.bootstrap import (
    bootstrap_assets,
    bootstrap_consumer_repo,
    packaged_asset_root,
)
from policyflow.cli import app
from policyflow.config import load_config


runner = CliRunner()


def test_bootstrap_fresh_repo_creates_consumer_layout(tmp_path: Path) -> None:
    result = bootstrap_consumer_repo(tmp_path)

    assert result.created
    assert not result.skipped
    assert (tmp_path / "policyflow.yml").exists()
    assert (tmp_path / "policyflow/change.example.yml").exists()
    assert (tmp_path / ".github/PULL_REQUEST_TEMPLATE.md").exists()
    assert (tmp_path / ".github/workflows/policyflow.yml").exists()
    assert not (tmp_path / ".policyflow/bootstrap.json").exists()
    assert not (tmp_path / "policyflow.runners.yml").exists()
    assert not (tmp_path / "ai").exists()

    change = yaml.safe_load((tmp_path / "policyflow/change.example.yml").read_text())
    assert change["version"] == 2
    assert "runtime" not in change
    assert "handoffs" not in change
    assert "execution" not in change

    config = load_config(tmp_path / "policyflow.yml")
    assert config.version == 2
    assert config.paths.changes == Path("policyflow")


def test_bootstrap_assets_do_not_include_runner_or_codex_assets() -> None:
    bootstrap_consumer_repo_assets = bootstrap_assets()
    asset_root = packaged_asset_root()
    targets = {asset.target.as_posix() for asset in bootstrap_consumer_repo_assets}
    source_names = {
        asset.source.relative_to(asset_root).as_posix()
        for asset in bootstrap_consumer_repo_assets
        if asset.source is not None
    }

    assert "policyflow.runners.yml" not in targets
    assert ".policyflow/bootstrap.json" not in targets
    assert "policyflow/change.example.yml" in targets
    assert ".github/workflows/policyflow.yml" in targets
    assert not any("codex" in source.lower() for source in source_names)
    assert not any("runner" in target.lower() for target in targets)
    assert not any(target.startswith("ai/") for target in targets)


def test_bootstrap_can_skip_github_assets(tmp_path: Path) -> None:
    result = bootstrap_consumer_repo(tmp_path, github=False)

    assert "policyflow.yml" in result.created
    assert "policyflow/change.example.yml" in result.created
    assert ".github/PULL_REQUEST_TEMPLATE.md" not in result.created
    assert ".github/workflows/policyflow.yml" not in result.created


def test_bootstrap_dry_run_does_not_write_files(tmp_path: Path) -> None:
    result = bootstrap_consumer_repo(tmp_path, dry_run=True)

    assert result.would_create
    assert not result.created
    assert not (tmp_path / "policyflow.yml").exists()
    assert not (tmp_path / "policyflow").exists()


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
    assert load_config(existing).version == 2


def test_init_command_reports_created_files(tmp_path: Path) -> None:
    result = runner.invoke(app, ["init", str(tmp_path)])

    assert result.exit_code == 0
    assert "[SUCCESS] PolicyFlow bootstrap completed." in result.stdout
    assert "created policyflow.yml" in result.stdout
    assert "created policyflow/change.example.yml" in result.stdout
    assert (tmp_path / "policyflow.yml").exists()


def test_init_command_supports_dry_run(tmp_path: Path) -> None:
    result = runner.invoke(app, ["init", str(tmp_path), "--dry-run"])

    assert result.exit_code == 0
    assert "would create policyflow.yml" in result.stdout
    assert "would create policyflow/change.example.yml" in result.stdout
    assert not (tmp_path / "policyflow.yml").exists()


def test_init_command_supports_without_github(tmp_path: Path) -> None:
    result = runner.invoke(app, ["init", str(tmp_path), "--no-github"])

    assert result.exit_code == 0
    assert (tmp_path / "policyflow.yml").exists()
    assert (tmp_path / "policyflow/change.example.yml").exists()
    assert not (tmp_path / ".github/PULL_REQUEST_TEMPLATE.md").exists()
