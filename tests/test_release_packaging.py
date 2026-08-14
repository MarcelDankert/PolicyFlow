from __future__ import annotations

import zipfile
from pathlib import Path
import shutil

import tomllib

from policyflow.bootstrap import packaged_asset_root


ROOT = Path(__file__).resolve().parents[1]


def test_pyproject_includes_policyflow_asset_package_data() -> None:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    package_data = data["tool"]["setuptools"]["package-data"]["policyflow"]

    assert "assets/github/*.md" in package_data
    assert "assets/github/workflows/*.yml" in package_data
    assert "assets/examples/*.yml" in package_data
    assert "assets/docs/getting-started.md" in package_data
    for obsolete_pattern in (
        "assets/agents/*.md",
        "assets/prompts/*.md",
        "assets/rules/*.md",
        "assets/workflows/templates/*.yml",
        "assets/github/ISSUE_TEMPLATE/*.yml",
        "assets/docs/*.md",
    ):
        assert obsolete_pattern not in package_data


def test_packaged_asset_root_contains_bootstrap_assets() -> None:
    asset_root = packaged_asset_root()

    assert (asset_root / "github/PULL_REQUEST_TEMPLATE.md").exists()
    assert (asset_root / "github/workflows/policyflow-governance.yml").exists()
    assert (asset_root / "examples/policyflow.github-governed.yml").exists()
    assert (asset_root / "examples/policyflow.minimal.yml").exists()
    assert (asset_root / "docs/getting-started.md").exists()
    for obsolete_path in (
        "agents",
        "prompts",
        "rules",
        "workflows",
        "github/ISSUE_TEMPLATE",
        "examples/project-context.yml",
        "docs/runner-contract.md",
    ):
        assert not (asset_root / obsolete_path).exists()


def test_built_wheel_contains_bootstrap_assets(tmp_path: Path) -> None:
    import build.__main__ as build_main

    shutil.rmtree(ROOT / "build", ignore_errors=True)
    shutil.rmtree(ROOT / "policyflow.egg-info", ignore_errors=True)
    output_dir = tmp_path / "dist"
    build_main.main(
        [
            "--wheel",
            "--outdir",
            str(output_dir),
            str(ROOT),
        ]
    )

    wheel_path = next(output_dir.glob("policyflow-*.whl"))
    with zipfile.ZipFile(wheel_path) as wheel:
        names = set(wheel.namelist())

    assert "policyflow/assets/github/PULL_REQUEST_TEMPLATE.md" in names
    assert "policyflow/assets/github/workflows/policyflow-governance.yml" in names
    assert "policyflow/assets/examples/policyflow.github-governed.yml" in names
    assert "policyflow/assets/examples/policyflow.minimal.yml" in names
    assert "policyflow/assets/docs/getting-started.md" in names
    for obsolete_name in (
        "policyflow/assets/agents/planning-agent.md",
        "policyflow/assets/prompts/planning-agent.prompt.md",
        "policyflow/assets/rules/risk-classification.md",
        "policyflow/assets/workflows/templates/feature-workflow.template.yml",
        "policyflow/assets/github/ISSUE_TEMPLATE/feature.yml",
        "policyflow/assets/examples/project-context.yml",
        "policyflow/assets/docs/runner-contract.md",
        "policyflow/assets/docs/audit-reporting.md",
    ):
        assert obsolete_name not in names
