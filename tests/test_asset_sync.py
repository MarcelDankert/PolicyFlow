from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from policyflow.bootstrap import bootstrap_consumer_repo
from policyflow.cli import app


runner = CliRunner()


def test_sync_command_is_removed_from_v2_cli(tmp_path: Path) -> None:
    bootstrap_consumer_repo(tmp_path)

    result = runner.invoke(app, ["sync", str(tmp_path)])

    assert result.exit_code == 2
    assert "No such command" in result.output


def test_sync_apply_command_is_removed_from_v2_cli(tmp_path: Path) -> None:
    bootstrap_consumer_repo(tmp_path)

    result = runner.invoke(app, ["sync", str(tmp_path), "--apply"])

    assert result.exit_code == 2
    assert "No such command" in result.output
