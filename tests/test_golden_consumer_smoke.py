from __future__ import annotations

import json
from pathlib import Path
import shutil

from typer.testing import CliRunner

from policyflow.cli import app


runner = CliRunner()


def test_golden_consumer_repo_path_runs_end_to_end(tmp_path: Path) -> None:
    init_result = runner.invoke(app, ["init", str(tmp_path)])
    assert init_result.exit_code == 0

    doctor_result = runner.invoke(app, ["doctor", str(tmp_path), "--json"])
    assert doctor_result.exit_code == 0

    workflow_path = tmp_path / "policyflow/change.example.yml"
    assert workflow_path.exists()

    validate_result = runner.invoke(app, ["validate", str(workflow_path)])
    assert validate_result.exit_code == 0


def test_reference_consumer_project_demonstrates_v2_governance(tmp_path: Path) -> None:
    source = Path(__file__).resolve().parents[1] / "examples/reference-consumer"
    target = tmp_path / "reference-consumer"
    shutil.copytree(source, target)

    readme = (target / "README.md").read_text(encoding="utf-8")
    for expected in (
        "bootstrap",
        "doctor",
        "V2 governance schema validation",
        "No hosted runtime",
        "No provider credentials",
    ):
        assert expected in readme

    doctor_result = runner.invoke(app, ["doctor", str(target), "--json"])
    assert doctor_result.exit_code == 0
    doctor_payload = json.loads(doctor_result.stdout)
    assert doctor_payload["ready"] is True

    workflow_path = target / "policyflow/change.example.yml"
    validate_result = runner.invoke(app, ["validate", str(workflow_path)])
    assert validate_result.exit_code == 0

    getting_started = (
        Path(__file__).resolve().parents[1] / "docs/getting-started.md"
    ).read_text(encoding="utf-8")
    assert "examples/reference-consumer" in getting_started


