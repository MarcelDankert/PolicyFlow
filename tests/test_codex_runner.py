from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def write_input_payload(path: Path) -> Path:
    input_path = path / "policyflow-agent-input.json"
    input_path.write_text(
        json.dumps(
            {
                "workflow_path": "workflows/features/example.yml",
                "workflow": {
                    "workflow": {"id": "example", "type": "feature"},
                    "context": {
                        "workflow_file": "workflows/features/example.yml",
                        "risk_level": "MEDIUM",
                    },
                },
                "phase": "implementation",
                "owner_agent": "senior-dev-agent",
                "prompt_text": "Implement the approved scope.",
                "agent_text": "You are the senior dev agent.",
                "handoff": {
                    "from_phase": "architecture-check",
                    "to_phase": "implementation",
                    "required_inputs": ["implementation_constraints"],
                    "produced_outputs": ["implementation_summary"],
                },
            }
        ),
        encoding="utf-8",
    )
    return input_path


def write_fake_codex(path: Path) -> Path:
    fake_codex = path / "fake-codex"
    fake_codex.write_text(
        "\n".join(
            [
                "#!/usr/bin/env python3",
                "import json",
                "import sys",
                "from pathlib import Path",
                "",
                "output_path = None",
                "for index, arg in enumerate(sys.argv):",
                "    if arg == '-o' and index + 1 < len(sys.argv):",
                "        output_path = Path(sys.argv[index + 1])",
                "if output_path is None:",
                "    raise SystemExit('missing -o output path')",
                "result = {",
                "    'phase': 'implementation',",
                "    'owner_agent': 'senior-dev-agent',",
                "    'status': 'completed',",
                "    'summary': 'Implementation completed by fake Codex.',",
                "    'contract_updates': {",
                "        'owner_agent': 'senior-dev-agent',",
                "        'implementation_summary': 'Implemented the approved scope.',",
                "        'changed_files': ['policyflow/example.py'],",
                "        'test_summary': 'Ran unit tests.',",
                "        'docs_updates': ['README.md'],",
                "        'known_limitations': ['none'],",
                "        'unresolved_questions': ['none']",
                "    },",
                "    'handoff': {",
                "        'to_phase': 'review',",
                "        'required_inputs': ['implementation_summary', 'test_summary'],",
                "        'produced_outputs': ['review_findings']",
                "    }",
                "}",
                "output_path.write_text(json.dumps(result), encoding='utf-8')",
            ]
        ),
        encoding="utf-8",
    )
    fake_codex.chmod(0o755)
    return fake_codex


def test_codex_runner_writes_policyflow_result_json(tmp_path: Path) -> None:
    input_path = write_input_payload(tmp_path)
    output_path = tmp_path / "policyflow-agent-output.json"
    fake_codex = write_fake_codex(tmp_path)

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "policyflow.codex_runner",
            "--input",
            str(input_path),
            "--output",
            str(output_path),
            "--codex-command",
            str(fake_codex),
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["phase"] == "implementation"
    assert payload["owner_agent"] == "senior-dev-agent"
    assert payload["status"] == "completed"
    assert payload["contract_updates"]["owner_agent"] == "senior-dev-agent"


def test_codex_runner_reports_missing_codex_command(tmp_path: Path) -> None:
    input_path = write_input_payload(tmp_path)
    output_path = tmp_path / "policyflow-agent-output.json"
    env = {**os.environ, "PATH": ""}

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "policyflow.codex_runner",
            "--input",
            str(input_path),
            "--output",
            str(output_path),
            "--codex-command",
            "missing-policyflow-codex",
        ],
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )

    assert completed.returncode == 2
    assert "Codex CLI command not found: missing-policyflow-codex" in completed.stderr
    assert "Install Codex CLI or set policyflow.runners.yml" in completed.stderr
    assert not output_path.exists()
