from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
from typing import Any

from policyflow.bootstrap import (
    BootstrapAsset,
    asset_content,
    asset_digest,
    bootstrap_assets,
    policyflow_version,
)


METADATA_PATH = Path(".policyflow/bootstrap.json")


@dataclass
class SyncResult:
    unchanged: list[str] = field(default_factory=list)
    added: list[str] = field(default_factory=list)
    changed: list[str] = field(default_factory=list)
    locally_modified: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    applied: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


def sync_consumer_assets(
    target: str | Path = Path("."),
    *,
    apply: bool = False,
    force: bool = False,
) -> SyncResult:
    target_root = Path(target)
    metadata = _load_metadata(target_root)
    current_assets = {_as_posix(asset.target): asset for asset in bootstrap_assets()}
    installed_assets = set(metadata.get("managed_assets", []))
    installed_assets.discard(_as_posix(METADATA_PATH))
    installed_hashes = _metadata_hashes(metadata)
    result = SyncResult()

    for relative_path, asset in sorted(current_assets.items()):
        destination = target_root / relative_path
        current_hash = asset_digest(asset)
        installed_hash = installed_hashes.get(relative_path)

        if not destination.exists():
            result.added.append(relative_path)
            if apply:
                _write_current_asset(asset, destination)
                result.applied.append(relative_path)
            continue

        local_hash = _file_digest(destination)
        if installed_hash is None:
            if local_hash == current_hash:
                result.unchanged.append(relative_path)
            else:
                result.locally_modified.append(relative_path)
                result.skipped.append(relative_path)
            continue

        if local_hash == current_hash:
            result.unchanged.append(relative_path)
        elif local_hash == installed_hash:
            result.changed.append(relative_path)
            if apply:
                _write_current_asset(asset, destination)
                result.applied.append(relative_path)
        else:
            result.locally_modified.append(relative_path)
            if apply and force:
                _write_current_asset(asset, destination)
                result.applied.append(relative_path)
            else:
                result.skipped.append(relative_path)

    for relative_path in sorted(installed_assets - set(current_assets)):
        result.removed.append(relative_path)
        result.skipped.append(relative_path)

    if apply:
        _write_metadata(target_root, current_assets)

    return result


def _load_metadata(target_root: Path) -> dict[str, Any]:
    metadata_path = target_root / METADATA_PATH
    if not metadata_path.exists():
        return {"managed_assets": [], "asset_hashes": {}}

    data = json.loads(metadata_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {"managed_assets": [], "asset_hashes": {}}
    return data


def _metadata_hashes(metadata: dict[str, Any]) -> dict[str, str]:
    hashes = metadata.get("asset_hashes", {})
    if not isinstance(hashes, dict):
        return {}
    return {str(path): str(digest) for path, digest in hashes.items()}


def _write_current_asset(asset: BootstrapAsset, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(asset_content(asset), encoding="utf-8")


def _write_metadata(target_root: Path, current_assets: dict[str, BootstrapAsset]) -> None:
    metadata_path = target_root / METADATA_PATH
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata = {
        "policyflow_version": policyflow_version(),
        "managed_assets": sorted([*current_assets, _as_posix(METADATA_PATH)]),
        "asset_hashes": {
            relative_path: asset_digest(asset)
            for relative_path, asset in sorted(current_assets.items())
        },
        "force": False,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()


def _as_posix(path: Path) -> str:
    return path.as_posix()
