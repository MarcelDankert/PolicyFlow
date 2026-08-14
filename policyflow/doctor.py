from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from policyflow.config import PolicyFlowConfig, load_config
from policyflow.exceptions import WorkflowValidationError
from policyflow.validator import validate_workflow_v2_file


def doctor_consumer_repo(
    target: str | Path = Path("."),
) -> dict[str, Any]:
    target_root = Path(target)
    checks: list[dict[str, str]] = [_check_python_runtime()]

    config: PolicyFlowConfig | None = None
    try:
        config = load_config(target_root / "policyflow.yml")
        checks.append(_check("config", "pass", "policyflow.yml is valid."))
    except WorkflowValidationError as exc:
        checks.append(
            _check(
                "config",
                "failure",
                "; ".join(exc.errors),
                "Run `policyflow init` or add a valid root policyflow.yml.",
            )
        )

    if config is not None:
        checks.append(_check_change_example(target_root, config))
        checks.append(_check_github_templates(target_root, config))

    failures = sum(1 for check in checks if check["status"] == "failure")
    warnings = sum(1 for check in checks if check["status"] == "warning")

    return {
        "ready": failures == 0,
        "failures": failures,
        "warnings": warnings,
        "checks": checks,
    }


def _check(
    name: str,
    status: str,
    message: str,
    remediation: str = "",
) -> dict[str, str]:
    return {
        "check": name,
        "status": status,
        "message": message,
        "remediation": remediation,
    }


def _check_python_runtime() -> dict[str, str]:
    version_text = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info < (3, 11):
        return _check(
            "python_runtime",
            "failure",
            f"Python {version_text} is below PolicyFlow's minimum supported version.",
            "Install Python 3.11 or newer.",
        )
    return _check("python_runtime", "pass", f"Python {version_text} is supported.")


def _check_change_example(target_root: Path, config: PolicyFlowConfig) -> dict[str, str]:
    change_path = target_root / config.paths.changes / "change.example.yml"
    if not change_path.exists():
        return _check(
            "change_example",
            "failure",
            f"Example change file not found: {(config.paths.changes / 'change.example.yml').as_posix()}",
            "Run `policyflow init` to scaffold the V2 example change.",
        )
    try:
        validate_workflow_v2_file(change_path)
    except WorkflowValidationError as exc:
        return _check(
            "change_example",
            "failure",
            "Example change does not match the V2 governance schema: " + "; ".join(exc.errors),
            "Fix policyflow/change.example.yml or rerun `policyflow init --force`.",
        )
    return _check("change_example", "pass", "V2 example change is present and valid.")


def _check_github_templates(target_root: Path, config: PolicyFlowConfig) -> dict[str, str]:
    if not config.github.enabled:
        return _check("github_templates", "pass", "GitHub PR validation is disabled.")

    missing = _missing_paths(
        target_root,
        [config.paths.pr_template, config.paths.governance_workflow],
    )
    if missing:
        return _check(
            "github_templates",
            "failure",
            f"Missing GitHub governance files: {', '.join(missing)}",
            "Run `policyflow init` to scaffold read-only GitHub governance files.",
        )
    return _check("github_templates", "pass", "Read-only GitHub governance files are present.")


def _missing_paths(target_root: Path, paths: list[Path]) -> list[str]:
    missing: list[str] = []
    for path in paths:
        if not (target_root / path).exists():
            missing.append(path.as_posix())
    return missing
