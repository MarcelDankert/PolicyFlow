from __future__ import annotations

import zipfile
from pathlib import Path

import tomllib

from policyflow.bootstrap import packaged_asset_root


ROOT = Path(__file__).resolve().parents[1]


def test_pyproject_includes_policyflow_asset_package_data() -> None:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    package_data = data["tool"]["setuptools"]["package-data"]["policyflow"]

    assert "assets/agents/*.md" in package_data
    assert "assets/prompts/*.md" in package_data
    assert "assets/rules/*.md" in package_data
    assert "assets/workflows/templates/*.yml" in package_data
    assert "assets/github/ISSUE_TEMPLATE/*.yml" in package_data
    assert "assets/github/workflows/*.yml" in package_data
    assert "assets/examples/*.yml" in package_data
    assert "assets/docs/*.md" in package_data


def test_packaged_asset_root_contains_bootstrap_assets() -> None:
    asset_root = packaged_asset_root()

    assert (asset_root / "agents/planning-agent.md").exists()
    assert (asset_root / "prompts/planning-agent.prompt.md").exists()
    assert (asset_root / "rules/risk-classification.md").exists()
    assert (asset_root / "workflows/templates/feature-workflow.template.yml").exists()
    assert (asset_root / "github/PULL_REQUEST_TEMPLATE.md").exists()
    assert (asset_root / "github/workflows/policyflow-governance.yml").exists()
    assert (asset_root / "examples/project-context.yml").exists()
    assert (asset_root / "docs/getting-started.md").exists()
    assert (asset_root / "docs/runner-contract.md").exists()


def test_built_wheel_contains_bootstrap_assets(tmp_path: Path) -> None:
    import build.__main__ as build_main

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

    assert "policyflow/assets/agents/planning-agent.md" in names
    assert "policyflow/assets/prompts/planning-agent.prompt.md" in names
    assert "policyflow/assets/rules/risk-classification.md" in names
    assert "policyflow/assets/workflows/templates/feature-workflow.template.yml" in names
    assert "policyflow/assets/github/PULL_REQUEST_TEMPLATE.md" in names
    assert "policyflow/assets/github/workflows/policyflow-governance.yml" in names
    assert "policyflow/assets/examples/project-context.yml" in names
    assert "policyflow/assets/docs/getting-started.md" in names
    assert "policyflow/assets/docs/runner-contract.md" in names
