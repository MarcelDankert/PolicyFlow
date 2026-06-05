from __future__ import annotations

import hashlib
import json
from pathlib import Path

from typer.testing import CliRunner

from policyflow.bootstrap import bootstrap_consumer_repo
from policyflow.cli import app
from policyflow.sync import sync_consumer_assets


runner = CliRunner()


def test_sync_reports_fresh_bootstrap_as_unchanged(tmp_path: Path) -> None:
    bootstrap_consumer_repo(tmp_path)

    result = sync_consumer_assets(tmp_path)

    assert "policyflow.yml" in result.unchanged
    assert not result.added
    assert not result.changed
    assert not result.locally_modified
    assert not result.removed
    assert not result.applied


def test_sync_reports_upstream_changed_asset_without_overwrite(tmp_path: Path) -> None:
    bootstrap_consumer_repo(tmp_path)
    _mark_asset_as_installed_from_old_content(tmp_path, "policyflow.yml", "version: 1\nold: true\n")

    result = sync_consumer_assets(tmp_path)

    assert "policyflow.yml" in result.changed
    assert not result.applied
    assert (tmp_path / "policyflow.yml").read_text(encoding="utf-8") == "version: 1\nold: true\n"


def test_sync_apply_updates_upstream_changed_asset(tmp_path: Path) -> None:
    bootstrap_consumer_repo(tmp_path)
    _mark_asset_as_installed_from_old_content(tmp_path, "policyflow.yml", "version: 1\nold: true\n")

    result = sync_consumer_assets(tmp_path, apply=True)

    assert "policyflow.yml" in result.changed
    assert "policyflow.yml" in result.applied
    assert "old: true" not in (tmp_path / "policyflow.yml").read_text(encoding="utf-8")


def test_sync_reports_locally_modified_asset_and_preserves_it(tmp_path: Path) -> None:
    bootstrap_consumer_repo(tmp_path)
    local_content = "version: 1\n# consumer customization\n"
    (tmp_path / "policyflow.yml").write_text(local_content, encoding="utf-8")

    result = sync_consumer_assets(tmp_path, apply=True)

    assert "policyflow.yml" in result.locally_modified
    assert "policyflow.yml" not in result.applied
    assert (tmp_path / "policyflow.yml").read_text(encoding="utf-8") == local_content


def test_sync_force_overwrites_locally_modified_asset(tmp_path: Path) -> None:
    bootstrap_consumer_repo(tmp_path)
    (tmp_path / "policyflow.yml").write_text("version: 1\n# consumer customization\n", encoding="utf-8")

    result = sync_consumer_assets(tmp_path, apply=True, force=True)

    assert "policyflow.yml" in result.locally_modified
    assert "policyflow.yml" in result.applied
    assert "consumer customization" not in (tmp_path / "policyflow.yml").read_text(encoding="utf-8")


def test_sync_reports_assets_removed_from_current_package(tmp_path: Path) -> None:
    bootstrap_consumer_repo(tmp_path)
    metadata_path = tmp_path / ".policyflow/bootstrap.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["managed_assets"].append("ai/removed-template.md")
    metadata["asset_hashes"]["ai/removed-template.md"] = _sha256("removed\n")
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    (tmp_path / "ai/removed-template.md").write_text("removed\n", encoding="utf-8")

    result = sync_consumer_assets(tmp_path)

    assert "ai/removed-template.md" in result.removed
    assert (tmp_path / "ai/removed-template.md").exists()


def test_sync_command_outputs_dry_run_actions(tmp_path: Path) -> None:
    bootstrap_consumer_repo(tmp_path)
    _mark_asset_as_installed_from_old_content(tmp_path, "policyflow.yml", "version: 1\nold: true\n")

    result = runner.invoke(app, ["sync", str(tmp_path)])

    assert result.exit_code == 0
    assert "would update policyflow.yml" in result.stdout
    assert "[SUCCESS] PolicyFlow asset sync preview completed." in result.stdout


def test_sync_command_apply_updates_assets(tmp_path: Path) -> None:
    bootstrap_consumer_repo(tmp_path)
    _mark_asset_as_installed_from_old_content(tmp_path, "policyflow.yml", "version: 1\nold: true\n")

    result = runner.invoke(app, ["sync", str(tmp_path), "--apply"])

    assert result.exit_code == 0
    assert "updated policyflow.yml" in result.stdout
    assert "[SUCCESS] PolicyFlow asset sync completed." in result.stdout


def _mark_asset_as_installed_from_old_content(
    target: Path, relative_path: str, content: str
) -> None:
    (target / relative_path).write_text(content, encoding="utf-8")
    metadata_path = target / ".policyflow/bootstrap.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["asset_hashes"][relative_path] = _sha256(content)
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def _sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
