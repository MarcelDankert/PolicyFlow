from __future__ import annotations

from dataclasses import dataclass, field
from importlib.metadata import PackageNotFoundError, version
import json
from pathlib import Path
from typing import Iterable

import yaml


@dataclass(frozen=True)
class BootstrapAsset:
    source: Path | None
    target: Path
    content: str | None = None


@dataclass
class BootstrapResult:
    created: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    overwritten: list[str] = field(default_factory=list)
    would_create: list[str] = field(default_factory=list)
    would_skip: list[str] = field(default_factory=list)


def bootstrap_consumer_repo(
    target: str | Path = Path("."),
    *,
    dry_run: bool = False,
    force: bool = False,
) -> BootstrapResult:
    target_root = Path(target)
    source_root = Path(__file__).resolve().parents[1]
    assets = _bootstrap_assets(source_root)
    result = BootstrapResult()

    for asset in assets:
        destination = target_root / asset.target
        relative_target = _as_posix(asset.target)
        exists = destination.exists()

        if dry_run:
            if exists and not force:
                result.would_skip.append(relative_target)
            else:
                result.would_create.append(relative_target)
            continue

        if exists and not force:
            result.skipped.append(relative_target)
            continue

        destination.parent.mkdir(parents=True, exist_ok=True)
        _write_asset(asset, destination)
        if exists:
            result.overwritten.append(relative_target)
        else:
            result.created.append(relative_target)

    if not dry_run:
        _write_bootstrap_metadata(target_root, assets, force)

    return result


def _bootstrap_assets(source_root: Path) -> list[BootstrapAsset]:
    assets: list[BootstrapAsset] = [
        BootstrapAsset(None, Path("policyflow.yml"), _consumer_config_content()),
        BootstrapAsset(None, Path("policyflow.runners.yml"), _consumer_runner_config_content()),
        BootstrapAsset(
            source_root / "examples" / "project-context.yml",
            Path("ai/project-context.yml"),
        ),
        BootstrapAsset(
            source_root / "github" / "PULL_REQUEST_TEMPLATE.md",
            Path(".github/PULL_REQUEST_TEMPLATE.md"),
        ),
    ]

    for source_dir, target_dir in (
        ("agents", "ai/agents"),
        ("prompts", "ai/prompts"),
        ("rules", "ai/rules"),
        ("workflows/templates", "ai/workflows/templates"),
        ("github/ISSUE_TEMPLATE", ".github/ISSUE_TEMPLATE"),
    ):
        assets.extend(_copy_tree_assets(source_root / source_dir, Path(target_dir)))

    return assets


def _copy_tree_assets(source_dir: Path, target_dir: Path) -> list[BootstrapAsset]:
    return [
        BootstrapAsset(path, target_dir / path.relative_to(source_dir))
        for path in sorted(source_dir.rglob("*"))
        if path.is_file()
    ]


def _consumer_config_content() -> str:
    payload = {
        "version": 1,
        "paths": {
            "workflows": "ai/workflows",
            "prompts": "ai/prompts",
            "agents": "ai/agents",
            "rules": "ai/rules",
            "project_context": "ai/project-context.yml",
            "runner_config": "policyflow.runners.yml",
            "pr_template": ".github/PULL_REQUEST_TEMPLATE.md",
            "issue_templates": ".github/ISSUE_TEMPLATE",
            "governance_workflow": ".github/workflows/policyflow-governance.yml",
        },
        "features": {
            "pr_validation": True,
            "github_approval_checks": True,
            "runner_execution": True,
            "bootstrap_managed_assets": True,
        },
        "bootstrap": {
            "managed_assets": [],
        },
    }
    return yaml.safe_dump(payload, sort_keys=False)


def _consumer_runner_config_content() -> str:
    payload = {
        "default_runner": "codex",
        "runners": {
            "codex": {
                "type": "codex",
                "command": [
                    "python",
                    "scripts/policyflow_codex_wrapper.py",
                    "--input",
                    "{input_path}",
                    "--output",
                    "{output_path}",
                ],
                "prompt_paths": {
                    "planning": "ai/prompts/planning-agent.prompt.md",
                    "architecture-check": "ai/prompts/architecture-agent.prompt.md",
                    "implementation": "ai/prompts/senior-dev-agent.prompt.md",
                    "review": "ai/prompts/review-agent.prompt.md",
                    "qa": "ai/prompts/qa-agent.prompt.md",
                },
                "agent_paths": {
                    "planning": "ai/agents/planning-agent.md",
                    "architecture-check": "ai/agents/architecture-agent.md",
                    "implementation": "ai/agents/senior-dev-agent.md",
                    "review": "ai/agents/review-agent.md",
                    "qa": "ai/agents/qa-agent.md",
                },
            }
        },
    }
    return yaml.safe_dump(payload, sort_keys=False)


def _write_asset(asset: BootstrapAsset, destination: Path) -> None:
    if asset.content is not None:
        destination.write_text(asset.content, encoding="utf-8")
        return

    if asset.source is None:
        raise ValueError(f"Bootstrap asset has no source or content: {asset.target}")

    destination.write_text(asset.source.read_text(encoding="utf-8"), encoding="utf-8")


def _write_bootstrap_metadata(
    target_root: Path, assets: Iterable[BootstrapAsset], force: bool
) -> None:
    metadata_path = target_root / ".policyflow" / "bootstrap.json"
    if metadata_path.exists() and not force:
        return

    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    managed_assets = [_as_posix(asset.target) for asset in assets]
    metadata = {
        "policyflow_version": _policyflow_version(),
        "managed_assets": sorted([*managed_assets, ".policyflow/bootstrap.json"]),
        "force": force,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def _policyflow_version() -> str:
    try:
        return version("policyflow")
    except PackageNotFoundError:
        return "0.1.0"


def _as_posix(path: Path) -> str:
    return path.as_posix()
