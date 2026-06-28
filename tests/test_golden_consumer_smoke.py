from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys

from typer.testing import CliRunner
import yaml

from policyflow.cli import app


runner = CliRunner()


def test_golden_consumer_repo_path_runs_end_to_end(tmp_path: Path) -> None:
    init_result = runner.invoke(app, ["init", str(tmp_path)])
    assert init_result.exit_code == 0

    doctor_result = runner.invoke(app, ["doctor", str(tmp_path), "--json"])
    assert doctor_result.exit_code == 0

    workflow_path = tmp_path / "ai/workflows/features/starter-workflow.yml"
    assert workflow_path.exists()

    new_workflow_result = runner.invoke(
        app,
        [
            "new-workflow",
            "feature",
            "--id",
            "first-feature",
            "--risk",
            "LOW",
            "--target",
            str(tmp_path),
        ],
    )
    assert new_workflow_result.exit_code == 0
    first_workflow_path = tmp_path / "ai/workflows/features/first-feature.yml"
    assert first_workflow_path.exists()

    first_validate_result = runner.invoke(app, ["validate", str(first_workflow_path)])
    assert first_validate_result.exit_code == 0

    validate_result = runner.invoke(app, ["validate", str(workflow_path)])
    assert validate_result.exit_code == 0

    status_result = runner.invoke(app, ["status", str(workflow_path)])
    assert status_result.exit_code == 0
    assert "Workflow ID: starter-workflow" in status_result.stdout

    audit_result = runner.invoke(app, ["audit", str(tmp_path / "ai/workflows")])
    assert audit_result.exit_code == 0
    assert "starter-workflow" in audit_result.stdout

    generated_runner_config = yaml.safe_load(
        (tmp_path / "policyflow.runners.yml").read_text(encoding="utf-8")
    )
    assert generated_runner_config["default_runner"] == "command"
    generated_command = generated_runner_config["runners"]["command"]["command"]
    assert generated_command == [
        "policyflow-runner",
        "--input",
        "{input_path}",
        "--output",
        "{output_path}",
    ]
    generated_codex_command = generated_runner_config["runners"]["codex"]["command"]
    assert "scripts/policyflow_codex_wrapper.py" not in generated_codex_command
    assert generated_codex_command[:3] == [
        "{python_executable}",
        "-m",
        "policyflow.codex_runner",
    ]

    fake_runner_path = _write_fake_runner(tmp_path)
    _configure_fake_runner(tmp_path, fake_runner_path)

    run_phase_result = runner.invoke(
        app,
        [
            "run-phase",
            str(workflow_path),
            "implementation",
            "--runner-config",
            str(tmp_path / "policyflow.runners.yml"),
        ],
    )
    assert run_phase_result.exit_code == 0

    workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    assert workflow["execution"]["phases"][2]["state"] == "completed"
    assert workflow["contracts"]["implementation"]["owner_agent"] == "senior-dev-agent"
    assert workflow["runtime"]["status"] == "handoff_pending"
    assert workflow["runtime"]["current_phase"] == "implementation"
    assert workflow["handoffs"][-1]["to_phase"] == "review"
    assert workflow["handoffs"][-1]["required_inputs"] == [
        "implementation_summary",
        "test_summary",
    ]
    assert workflow["handoffs"][-1]["produced_outputs"] == ["review_findings"]

    pr_body_path = tmp_path / "pr-body.md"
    pr_body_path.write_text(_starter_pr_body(), encoding="utf-8")
    validate_pr_result = runner.invoke(
        app,
        ["validate-pr", str(workflow_path), str(pr_body_path)],
    )
    assert validate_pr_result.exit_code == 0


def test_reference_consumer_project_demonstrates_v2_governance(tmp_path: Path) -> None:
    source = Path(__file__).resolve().parents[1] / "examples/reference-consumer"
    target = tmp_path / "reference-consumer"
    shutil.copytree(source, target)

    readme = (target / "README.md").read_text(encoding="utf-8")
    for expected in (
        "bootstrap",
        "doctor",
        "workflow validation",
        "loop governance",
        "evaluation governance",
        "audit reporting",
        "No hosted runtime",
        "No provider credentials",
    ):
        assert expected in readme

    config_result = runner.invoke(app, ["config-check", str(target / "policyflow.yml")])
    assert config_result.exit_code == 0

    doctor_result = runner.invoke(app, ["doctor", str(target), "--json"])
    assert doctor_result.exit_code == 0
    doctor_payload = json.loads(doctor_result.stdout)
    assert doctor_payload["ready"] is True

    workflow_path = target / "ai/workflows/features/v2-reference-governance.yml"
    validate_result = runner.invoke(app, ["validate", str(workflow_path)])
    assert validate_result.exit_code == 0

    audit_result = runner.invoke(app, ["audit", str(target / "ai/workflows"), "--json"])
    assert audit_result.exit_code == 0
    audit_payload = json.loads(audit_result.stdout)
    assert audit_payload["schema_version"] == "policyflow.audit.v1"
    assert audit_payload["summary"]["loop_governance"]["declared"] == 1
    assert audit_payload["summary"]["evaluation_governance"]["declared"] == 1

    evaluation_result = runner.invoke(
        app,
        ["evaluation-report", str(target / "ai/workflows"), "--json"],
    )
    assert evaluation_result.exit_code == 0
    evaluation_payload = json.loads(evaluation_result.stdout)
    assert evaluation_payload["summary"]["evaluations_declared"] == 1

    loop_result = runner.invoke(
        app,
        ["loop-report", str(target / "ai/workflows"), "--json"],
    )
    assert loop_result.exit_code == 0
    loop_payload = json.loads(loop_result.stdout)
    assert loop_payload["summary"]["loops_declared"] == 1

    getting_started = (
        Path(__file__).resolve().parents[1] / "docs/getting-started.md"
    ).read_text(encoding="utf-8")
    assert "examples/reference-consumer" in getting_started


def _write_fake_runner(path: Path) -> Path:
    script_path = path / "fake-policyflow-runner.py"
    script_path.write_text(
        "\n".join(
            [
                "import argparse",
                "import json",
                "from pathlib import Path",
                "",
                "parser = argparse.ArgumentParser()",
                "parser.add_argument('--input', required=True)",
                "parser.add_argument('--output', required=True)",
                "args = parser.parse_args()",
                "",
                "payload = json.loads(Path(args.input).read_text(encoding='utf-8'))",
                "result = {",
                "    'phase': payload['phase'],",
                "    'owner_agent': payload['owner_agent'],",
                "    'status': 'completed',",
                "    'summary': 'Golden smoke fake runner completed implementation.',",
                "    'contract_updates': {",
                "        'owner_agent': 'senior-dev-agent',",
                "        'implementation_summary': 'Validated the bootstrapped runner path.',",
                "        'changed_files': ['ai/workflows/features/starter-workflow.yml'],",
                "        'test_summary': 'Golden consumer smoke executed run-phase.',",
                "        'docs_updates': ['none'],",
                "        'known_limitations': ['none'],",
                "        'unresolved_questions': ['none']",
                "    },",
                "    'handoff': {",
                "        'to_phase': 'review',",
                "        'required_inputs': ['implementation_summary', 'test_summary'],",
                "        'produced_outputs': ['review_findings']",
                "    }",
                "}",
                "Path(args.output).write_text(json.dumps(result), encoding='utf-8')",
            ]
        ),
        encoding="utf-8",
    )
    return script_path


def _configure_fake_runner(target: Path, script_path: Path) -> None:
    runner_config_path = target / "policyflow.runners.yml"
    runner_config = yaml.safe_load(runner_config_path.read_text(encoding="utf-8"))
    runner_config["default_runner"] = "command"
    runner_config["runners"]["command"]["command"] = [
        sys.executable,
        str(script_path),
        "--input",
        "{input_path}",
        "--output",
        "{output_path}",
    ]
    runner_config_path.write_text(
        yaml.safe_dump(runner_config, sort_keys=False),
        encoding="utf-8",
    )


def _starter_pr_body() -> str:
    return """## Summary

Starter PolicyFlow validation path.

## Linked Issue

#1

## Workflow File
- ai/workflows/features/starter-workflow.yml

## Scope
- In scope: starter PolicyFlow validation
- Out of scope: product changes

## Non-Goals

No runtime behavior changes.

## Governance
- Declared risk level: MEDIUM
- Confidence summary: starter workflow is ready for validation
- Required reviews completed: architecture-agent, review-agent, qa-agent
- Human approval login if required: not required
- Human approval reference if required: not required
- Escalation notes: none
- Protected areas touched: none

## Evidence
- Planning evidence: evidence.planning
- Architecture evidence: evidence.architecture-check

## Overrides
- Override ID: starter-phase-bypass
- Override type: phase_bypass
- Approved by login: architecture-agent
- Approval reference: STARTER-ARCH-OVERRIDE
- Mitigations confirmed: yes

## Confirmation
- [x] The implementation matches the declared scope
- [x] Non-goals were respected
- [x] The linked workflow file governed this change
- [x] The workflow file existed before implementation and governed the work from the start
- [x] Scope, non-goals, and risk were fixed in the workflow before implementation started
- [x] Required workflow phases were executed as visible working steps, not only documented after the fact

## Tests
```text
policyflow validate ai/workflows/features/starter-workflow.yml
```

## Docs
- [x] No docs update needed
"""
