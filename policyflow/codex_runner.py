from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run a PolicyFlow phase through Codex CLI and write result JSON."
    )
    parser.add_argument("--input", required=True, dest="input_path")
    parser.add_argument("--output", required=True, dest="output_path")
    parser.add_argument("--codex-command", default="codex")
    parser.add_argument("--model")
    parser.add_argument("--profile")
    parser.add_argument("--sandbox", default="workspace-write")
    args = parser.parse_args(argv)

    codex_path = shutil.which(args.codex_command)
    if codex_path is None:
        _print_error(
            f"Codex CLI command not found: {args.codex_command}\n"
            "Install Codex CLI or set policyflow.runners.yml to a valid codex command."
        )
        return 2

    try:
        payload = _load_json(Path(args.input_path))
        result = _run_codex(codex_path, payload, args)
        _validate_result(payload, result)
        Path(args.output_path).write_text(
            json.dumps(result, indent=2),
            encoding="utf-8",
        )
    except RunnerError as exc:
        _print_error(str(exc))
        return exc.code

    return 0


class RunnerError(Exception):
    def __init__(self, message: str, code: int = 4) -> None:
        super().__init__(message)
        self.code = code


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise RunnerError(f"PolicyFlow input JSON not found: {path}", code=4)

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RunnerError(f"PolicyFlow input JSON is invalid: {exc}", code=4) from exc

    if not isinstance(data, dict):
        raise RunnerError("PolicyFlow input JSON must be a top-level object.", code=4)

    return data


def _run_codex(codex_path: str, payload: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as temp_dir_name:
        last_message_path = Path(temp_dir_name) / "codex-last-message.txt"
        command = [
            codex_path,
            "exec",
            "-o",
            str(last_message_path),
            "--sandbox",
            str(args.sandbox),
            "-",
        ]
        if args.model:
            command[2:2] = ["--model", str(args.model)]
        if args.profile:
            command[2:2] = ["--profile", str(args.profile)]

        completed = subprocess.run(
            command,
            input=_build_prompt(payload),
            text=True,
            capture_output=True,
            check=False,
        )

        if completed.returncode != 0:
            message = completed.stderr.strip() or completed.stdout.strip()
            remediation = (
                "Run `codex doctor` to check auth/runtime readiness, or update "
                "policyflow.runners.yml with the correct Codex command."
            )
            raise RunnerError(
                f"Codex CLI failed with exit code {completed.returncode}. "
                f"{message}\n{remediation}",
                code=3,
            )

        if not last_message_path.exists():
            raise RunnerError(
                "Codex CLI did not write a final message. Expected output from "
                "`codex exec -o <file>`.",
                code=4,
            )

        return _parse_result_json(last_message_path.read_text(encoding="utf-8"))


def _build_prompt(payload: dict[str, Any]) -> str:
    phase = payload.get("phase")
    owner_agent = payload.get("owner_agent")
    return "\n".join(
        [
            "Run the PolicyFlow workflow phase using the supplied JSON contract.",
            "Return only one JSON object as the final response. Do not include markdown.",
            "",
            "Required response fields:",
            "- phase: must match the requested phase",
            "- owner_agent: must match the requested owner_agent",
            "- status: completed or blocked",
            "- summary: short plain-text result",
            "- blockers: required when status is blocked",
            "- evidence_updates: optional object for evidence-bearing phases",
            "- contract_updates: optional object for agent-owned phase contracts",
            "- handoff: optional object with to_phase, required_inputs, produced_outputs",
            "",
            f"Requested phase: {phase}",
            f"Expected owner_agent: {owner_agent}",
            "",
            "PolicyFlow input JSON:",
            json.dumps(payload, indent=2),
        ]
    )


def _parse_result_json(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()

    try:
        data = json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise RunnerError(f"Codex final message was not valid JSON: {exc}", code=4) from exc

    if not isinstance(data, dict):
        raise RunnerError("Codex final message must be a top-level JSON object.", code=4)

    return data


def _validate_result(payload: dict[str, Any], result: dict[str, Any]) -> None:
    phase = str(payload.get("phase", "")).strip()
    owner_agent = str(payload.get("owner_agent", "")).strip()

    if str(result.get("phase", "")).strip() != phase:
        raise RunnerError(f"Codex result phase must match requested phase: {phase}", code=4)
    if str(result.get("owner_agent", "")).strip() != owner_agent:
        raise RunnerError(
            f"Codex result owner_agent must match expected owner: {owner_agent}",
            code=4,
        )

    status = str(result.get("status", "")).strip()
    if status not in {"completed", "blocked"}:
        raise RunnerError("Codex result status must be 'completed' or 'blocked'.", code=4)
    if status == "blocked" and not result.get("blockers") and not result.get("summary"):
        raise RunnerError("Blocked Codex results must include blockers or summary.", code=4)


def _print_error(message: str) -> None:
    print(message, file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
