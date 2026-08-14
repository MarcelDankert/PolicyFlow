from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from policyflow.bootstrap import bootstrap_consumer_repo
from policyflow.cli import app


runner = CliRunner()


def test_new_workflow_command_is_removed_from_v2_cli(tmp_path: Path) -> None:
    bootstrap_consumer_repo(tmp_path)

    result = runner.invoke(
        app,
        [
            "new-workflow",
            "feature",
            "--id",
            "cli-feature",
            "--risk",
            "LOW",
            "--target",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 2
    assert "No such command" in result.output
    assert not (tmp_path / "ai/workflows/features/cli-feature.yml").exists()


def test_v2_init_does_not_create_workflow_generator_template_tree(tmp_path: Path) -> None:
    bootstrap_consumer_repo(tmp_path)

    assert not (tmp_path / "ai/workflows").exists()
    assert not (tmp_path / "workflows/templates").exists()
    assert (tmp_path / "policyflow/change.example.yml").exists()
