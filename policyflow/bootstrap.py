from __future__ import annotations

from dataclasses import dataclass, field
from importlib.metadata import PackageNotFoundError, version
import json
from pathlib import Path
from typing import Iterable
import hashlib

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
    assets = bootstrap_assets()
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


def packaged_asset_root() -> Path:
    return Path(__file__).resolve().parent / "assets"


def bootstrap_assets() -> list[BootstrapAsset]:
    return _bootstrap_assets(packaged_asset_root())


def asset_content(asset: BootstrapAsset) -> str:
    if asset.content is not None:
        return asset.content

    if asset.source is None:
        raise ValueError(f"Bootstrap asset has no source or content: {asset.target}")

    return asset.source.read_text(encoding="utf-8")


def asset_digest(asset: BootstrapAsset) -> str:
    return hashlib.sha256(asset_content(asset).encode("utf-8")).hexdigest()


def _bootstrap_assets(source_root: Path) -> list[BootstrapAsset]:
    assets: list[BootstrapAsset] = [
        BootstrapAsset(None, Path("policyflow.yml"), _consumer_config_content()),
        BootstrapAsset(None, Path("policyflow.runners.yml"), _consumer_runner_config_content()),
        BootstrapAsset(
            source_root / "examples" / "project-context.yml",
            Path("ai/project-context.yml"),
        ),
        BootstrapAsset(
            None,
            Path("ai/workflows/features/starter-workflow.yml"),
            _starter_workflow_content(),
        ),
        BootstrapAsset(
            source_root / "github" / "PULL_REQUEST_TEMPLATE.md",
            Path(".github/PULL_REQUEST_TEMPLATE.md"),
        ),
        BootstrapAsset(
            source_root / "github" / "workflows" / "policyflow-governance.yml",
            Path(".github/workflows/policyflow-governance.yml"),
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
        "default_runner": "command",
        "runners": {
            "command": {
                "type": "command",
                "command": [
                    "policyflow-runner",
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
            },
            "codex": {
                "type": "codex",
                "command": [
                    "{python_executable}",
                    "-m",
                    "policyflow.codex_runner",
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


def _starter_workflow_content() -> str:
    payload = {
        "workflow": {
            "id": "starter-workflow",
            "type": "feature",
        },
        "context": {
            "workflow_file": "ai/workflows/features/starter-workflow.yml",
            "risk_level": "MEDIUM",
            "confidence": {
                "planning": "Starter scope and non-goals are fixed before implementation.",
                "implementation": "Starter implementation is bounded to validation of the generated workflow.",
                "tests": "Starter validation uses PolicyFlow workflow validation as the first test path.",
                "residual_uncertainty": "Consumer-specific overlays must still be reviewed by the target project.",
            },
        },
        "governance": {
            "required_reviews": [
                "architecture-agent",
                "review-agent",
                "qa-agent",
            ],
            "human_approval_required": False,
            "escalation_required": False,
            "protected_areas_touched": ["none"],
        },
        "execution": {
            "mode": "strict",
            "phases": [
                {"phase": "planning", "state": "completed"},
                {"phase": "architecture-check", "state": "completed"},
                {"phase": "implementation", "state": "pending"},
                {"phase": "review", "state": "pending"},
                {"phase": "qa", "state": "pending"},
            ],
        },
        "evidence": {
            "planning": {
                "summary": "Starter workflow scope and non-goals were locked before implementation.",
                "scope_locked": ["starter PolicyFlow validation"],
                "non_goals_locked": ["no product runtime changes"],
                "risk_rationale": "MEDIUM risk starter path because architecture, review, and QA are visible.",
            },
            "architecture-check": {
                "decision": "Starter workflow architecture check completed before implementation.",
                "constraints": ["keep starter validation bounded"],
                "approval_path": "architecture-agent review",
            },
        },
        "contracts": {
            "planning": {
                "owner_agent": "planning-agent",
                "issue_brief": "Validate the starter PolicyFlow consumer path.",
                "acceptance_criteria": [
                    "workflow validates",
                    "PR body validation can reference workflow evidence",
                ],
                "approved_scope": ["starter PolicyFlow validation"],
                "non_goals": ["no product runtime changes"],
                "initial_risk_level": "MEDIUM",
                "protected_areas_touched": ["none"],
                "confidence_summary": "Starter workflow is stable enough for bootstrap validation.",
                "escalation_flags": ["none"],
            },
            "architecture-check": {
                "owner_agent": "architecture-agent",
                "architecture_assessment": "Starter workflow stays inside documentation and validation setup.",
                "approved_scope": ["starter PolicyFlow validation"],
                "module_boundaries": ["consumer bootstrap assets"],
                "contract_impact": "No product contract impact.",
                "risk_review_decision": "MEDIUM risk starter path approved.",
                "required_reviews": [
                    "architecture-agent",
                    "review-agent",
                    "qa-agent",
                ],
                "implementation_constraints": ["keep starter workflow bounded"],
            },
        },
        "overrides": [
            {
                "id": "starter-phase-bypass",
                "type": "phase_bypass",
                "reason": "Starter workflow keeps review pending while allowing bootstrap validation to demonstrate override visibility.",
                "scope_impact": "No scope expansion beyond starter validation.",
                "risk_impact": "MEDIUM risk remains unchanged because compensating controls are explicit.",
                "mitigations": [
                    "review findings must still be resolved before QA completion"
                ],
                "approved_by": "architecture-agent",
                "approval_reference": "STARTER-ARCH-OVERRIDE",
                "review_by": "2099-12-31",
                "bypassed_phase": "review",
                "compensating_controls": [
                    "review findings tracked before QA sign-off"
                ],
            }
        ],
        "runtime": {
            "status": "handoff_pending",
            "current_phase": "architecture-check",
            "active_agent": "senior-dev-agent",
            "last_transition": "architecture-check completed and ready for implementation handoff",
            "block_reason": None,
        },
        "handoffs": [
            {
                "from_phase": "architecture-check",
                "to_phase": "implementation",
                "status": "pending",
                "required_inputs": [
                    "architecture_assessment",
                    "implementation_constraints",
                ],
                "produced_outputs": [
                    "implementation_summary",
                    "test_summary",
                ],
                "blockers": [],
                "override_refs": ["starter-phase-bypass"],
            }
        ],
    }
    return yaml.safe_dump(payload, sort_keys=False)


def _write_asset(asset: BootstrapAsset, destination: Path) -> None:
    destination.write_text(asset_content(asset), encoding="utf-8")


def _write_bootstrap_metadata(
    target_root: Path, assets: Iterable[BootstrapAsset], force: bool
) -> None:
    metadata_path = target_root / ".policyflow" / "bootstrap.json"
    if metadata_path.exists() and not force:
        return

    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    managed_assets = [_as_posix(asset.target) for asset in assets]
    metadata = {
        "policyflow_version": policyflow_version(),
        "managed_assets": sorted([*managed_assets, ".policyflow/bootstrap.json"]),
        "asset_hashes": {
            _as_posix(asset.target): asset_digest(asset)
            for asset in sorted(assets, key=lambda item: _as_posix(item.target))
        },
        "force": force,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def policyflow_version() -> str:
    try:
        from policyflow import __version__

        return __version__
    except ImportError:
        pass

    try:
        return version("policyflow")
    except PackageNotFoundError:
        return "0.4.0"


def _as_posix(path: Path) -> str:
    return path.as_posix()
