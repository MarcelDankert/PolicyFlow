from __future__ import annotations

from dataclasses import dataclass, field
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

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
    github: bool = True,
) -> BootstrapResult:
    target_root = Path(target)
    assets = bootstrap_assets(github=github)
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

    return result


def packaged_asset_root() -> Path:
    return Path(__file__).resolve().parent / "assets"


def bootstrap_assets(*, github: bool = True) -> list[BootstrapAsset]:
    return _bootstrap_assets(packaged_asset_root(), github=github)


def asset_content(asset: BootstrapAsset) -> str:
    if asset.content is not None:
        return asset.content

    if asset.source is None:
        raise ValueError(f"Bootstrap asset has no source or content: {asset.target}")

    return asset.source.read_text(encoding="utf-8")


def _bootstrap_assets(source_root: Path, *, github: bool) -> list[BootstrapAsset]:
    assets: list[BootstrapAsset] = [
        BootstrapAsset(None, Path("policyflow.yml"), _consumer_config_content(github=github)),
        BootstrapAsset(
            None,
            Path("policyflow/change.example.yml"),
            _change_example_content(),
        ),
    ]

    if github:
        assets.extend(
            [
                BootstrapAsset(
                    source_root / "github" / "PULL_REQUEST_TEMPLATE.md",
                    Path(".github/PULL_REQUEST_TEMPLATE.md"),
                ),
                BootstrapAsset(
                    source_root / "github" / "workflows" / "policyflow-governance.yml",
                    Path(".github/workflows/policyflow.yml"),
                ),
            ]
        )

    return assets


def _consumer_config_content(*, github: bool) -> str:
    payload = {
        "version": 2,
        "paths": {
            "changes": "policyflow",
            "pr_template": ".github/PULL_REQUEST_TEMPLATE.md",
            "governance_workflow": ".github/workflows/policyflow.yml",
        },
        "github": {"enabled": github},
    }
    return yaml.safe_dump(payload, sort_keys=False)


def _change_example_content() -> str:
    payload = {
        "version": 2,
        "change": {
            "id": "example-change",
            "type": "feature",
            "summary": "Example governed change.",
        },
        "risk": {
            "level": "medium",
            "rationale": "Touches application behavior but no protected areas.",
            "protected_areas": [],
        },
        "governance": {
            "required_reviews": ["architecture", "qa"],
            "human_approval_required": False,
        },
        "confidence": {
            "level": "medium",
            "summary": "Example evidence is sufficient for governance validation.",
        },
        "evidence": [
            {
                "id": "tests",
                "type": "test",
                "source": "ci",
                "status": "passed",
                "ref": "ci://example/tests",
            },
            {
                "id": "review",
                "type": "review",
                "source": "pull-request",
                "status": "passed",
                "ref": "pr://example/review",
            },
        ],
        "overrides": [],
    }
    return yaml.safe_dump(payload, sort_keys=False)


def _write_asset(asset: BootstrapAsset, destination: Path) -> None:
    destination.write_text(asset_content(asset), encoding="utf-8")


def policyflow_version() -> str:
    try:
        from policyflow import __version__

        return __version__
    except ImportError:
        pass

    try:
        return version("policyflow")
    except PackageNotFoundError:
        return "2.0.1"


def _as_posix(path: Path) -> str:
    return path.as_posix()
