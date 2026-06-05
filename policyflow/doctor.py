from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import Any

import yaml

from policyflow.consumer_config import ConsumerConfig, load_consumer_config
from policyflow.exceptions import WorkflowValidationError


def doctor_consumer_repo(target: str | Path = Path(".")) -> dict[str, Any]:
    target_root = Path(target)
    checks: list[dict[str, str]] = [_check_python_runtime()]

    config: ConsumerConfig | None = None
    try:
        config = load_consumer_config(target_root / "policyflow.yml")
        checks.append(_check("consumer_config", "pass", "policyflow.yml is valid."))
    except WorkflowValidationError as exc:
        checks.append(
            _check(
                "consumer_config",
                "failure",
                "; ".join(exc.errors),
                "Run `policyflow init` or add a valid root policyflow.yml.",
            )
        )

    if config is not None:
        checks.append(_check_bootstrap_artifacts(target_root, config))
        checks.append(_check_runner_config(target_root, config))
        checks.append(_check_project_context(target_root, config))
        checks.append(_check_github_templates(target_root, config))
        checks.append(_check_github_cli(config))

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


def _check_bootstrap_artifacts(target_root: Path, config: ConsumerConfig) -> dict[str, str]:
    required = [
        config.paths.workflows,
        config.paths.prompts,
        config.paths.agents,
        config.paths.rules,
        Path(".policyflow/bootstrap.json"),
    ]
    missing = _missing_paths(target_root, required)
    if missing:
        return _check(
            "bootstrap_artifacts",
            "failure",
            f"Missing bootstrap artifacts: {', '.join(missing)}",
            "Run `policyflow init` to scaffold missing PolicyFlow assets.",
        )
    return _check("bootstrap_artifacts", "pass", "Required bootstrap artifacts exist.")


def _check_runner_config(target_root: Path, config: ConsumerConfig) -> dict[str, str]:
    runner_path = target_root / config.paths.runner_config
    if not runner_path.exists():
        return _check(
            "runner_config",
            "failure",
            f"Runner config not found: {config.paths.runner_config.as_posix()}",
            "Run `policyflow init` to create policyflow.runners.yml.",
        )

    try:
        runner_data = yaml.safe_load(runner_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return _check(
            "runner_config",
            "failure",
            f"Runner config YAML is invalid: {exc}",
            "Fix policyflow.runners.yml or rerun `policyflow init --force`.",
        )

    if not isinstance(runner_data, dict):
        return _check(
            "runner_config",
            "failure",
            "Runner config must contain a top-level mapping.",
            "Fix policyflow.runners.yml or rerun `policyflow init --force`.",
        )

    default_runner = str(runner_data.get("default_runner", "")).strip()
    runners = runner_data.get("runners")
    if not default_runner or not isinstance(runners, dict) or default_runner not in runners:
        return _check(
            "runner_config",
            "failure",
            "Runner config must declare default_runner and matching runners entry.",
            "Fix policyflow.runners.yml runner settings.",
        )

    runner = runners.get(default_runner)
    if not isinstance(runner, dict):
        return _check(
            "runner_config",
            "failure",
            f"Runner definition for {default_runner} must be a mapping.",
            "Fix policyflow.runners.yml runner settings.",
        )

    command = runner.get("command")
    if not isinstance(command, list) or not command:
        return _check(
            "runner_config",
            "failure",
            f"Runner definition for {default_runner} must declare a non-empty command.",
            "Fix policyflow.runners.yml runner command settings.",
        )

    missing_assets = _missing_runner_assets(target_root, runner)
    if missing_assets:
        return _check(
            "runner_config",
            "failure",
            f"Missing runner assets: {', '.join(missing_assets)}",
            "Run `policyflow init` to scaffold missing runner prompt/agent assets.",
        )

    return _check("runner_config", "pass", "Runner config and referenced assets are present.")


def _missing_runner_assets(target_root: Path, runner: dict[str, Any]) -> list[str]:
    paths: list[Path] = []
    for key in ("prompt_paths", "agent_paths"):
        phase_paths = runner.get(key)
        if not isinstance(phase_paths, dict):
            continue
        for configured_path in phase_paths.values():
            if isinstance(configured_path, str) and configured_path.strip():
                paths.append(Path(configured_path))
    return _missing_paths(target_root, paths)


def _check_project_context(target_root: Path, config: ConsumerConfig) -> dict[str, str]:
    project_context_path = target_root / config.paths.project_context
    if not project_context_path.exists():
        return _check(
            "project_context",
            "failure",
            f"Project context not found: {config.paths.project_context.as_posix()}",
            "Run `policyflow init` or add ai/project-context.yml.",
        )
    try:
        data = yaml.safe_load(project_context_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return _check(
            "project_context",
            "failure",
            f"Project context YAML is invalid: {exc}",
            "Fix ai/project-context.yml.",
        )
    if not isinstance(data, dict):
        return _check(
            "project_context",
            "failure",
            "Project context must contain a top-level mapping.",
            "Fix ai/project-context.yml.",
        )
    return _check("project_context", "pass", "Project context is present and parseable.")


def _check_github_templates(target_root: Path, config: ConsumerConfig) -> dict[str, str]:
    if not config.features.pr_validation:
        return _check("github_templates", "pass", "GitHub PR validation is disabled.")

    missing = _missing_paths(
        target_root,
        [config.paths.pr_template, config.paths.issue_templates],
    )
    if missing:
        return _check(
            "github_templates",
            "failure",
            f"Missing GitHub governance templates: {', '.join(missing)}",
            "Run `policyflow init` to scaffold GitHub governance templates.",
        )
    return _check("github_templates", "pass", "GitHub governance templates are present.")


def _check_github_cli(config: ConsumerConfig) -> dict[str, str]:
    if not config.features.github_approval_checks:
        return _check("github_cli", "pass", "GitHub approval checks are disabled.")

    if shutil.which("gh") is None:
        return _check(
            "github_cli",
            "warning",
            "GitHub CLI was not found; live PR approval checks may not run locally.",
            "Install GitHub CLI and authenticate with `gh auth login` for live approval checks.",
        )
    return _check("github_cli", "pass", "GitHub CLI is available.")


def _missing_paths(target_root: Path, paths: list[Path]) -> list[str]:
    missing: list[str] = []
    for path in paths:
        if not (target_root / path).exists():
            missing.append(path.as_posix())
    return missing
