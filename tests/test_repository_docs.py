from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_repository_agents_guidance_is_discoverable() -> None:
    text = _read("AGENTS.md")

    assert "PolicyFlow Agent Guidance" in text
    assert "Repository Identity" in text
    assert "Workflow-First Delivery" in text
    assert "Required Validation" in text


def test_public_root_docs_do_not_include_machine_local_paths() -> None:
    for relative_path in ("AGENTS.md", "README.md"):
        text = _read(relative_path)

        assert "D:\\" not in text
        assert "C:\\" not in text


def test_readme_explains_v2_governance_only_product() -> None:
    readme = _read("README.md")

    for expected in (
        "PolicyFlow 2.0 is a small provider-neutral policy-as-code governance validator",
        "PolicyFlow validates governance. It does not execute work.",
        "ADR-0004: PolicyFlow 2.0 Returns To Governance Core",
        "policyflow init .",
        "policyflow validate policyflow/change.example.yml",
        "policyflow validate-pr policyflow/change.example.yml pr-body.md",
        "policyflow doctor .",
        "merge_readiness.explanation",
        "PolicyFlow `2.0.1` is prepared as the governance-core release target",
    ):
        assert expected in readme

    for forbidden in (
        "lightweight workflow orchestration layer",
        "workflow execution state schema",
        "supports synchronous external agent execution",
        "supports dry-run and explicit-apply sync",
        "policyflow==1.0.0",
        "v1.0.0",
    ):
        assert forbidden not in readme


def test_getting_started_has_ten_minute_v2_path() -> None:
    text = _read("docs/getting-started.md")
    packaged = _read("policyflow/assets/docs/getting-started.md")

    for command in (
        "python -m pip install policyflow==2.0.1",
        "policyflow init .",
        "policyflow init . --no-github",
        "policyflow doctor .",
        "policyflow doctor . --json",
        "policyflow validate policyflow/change.example.yml",
        'policyflow validate-pr "$workflow_path" pr-body.md --github-reviews pr-reviews.json --allow-pending',
    ):
        assert command in text

    for removed_command in (
        "policyflow new-workflow",
        "policyflow status",
        "policyflow audit",
        "policyflow sync",
        "ai/workflows",
        "--github-app-preflight",
    ):
        assert removed_command not in text

    assert "read-only" in text
    assert "does not create branches" in text
    assert "mutate labels" in text
    assert "merge pull requests" in text
    assert packaged == text


def test_public_api_docs_define_v2_stable_boundary() -> None:
    text = _read("docs/public-api.md")

    for expected in (
        "PolicyFlow 2.0 exposes a governance-only public API",
        "validate_workflow_v2",
        "inspect_workflow_v2",
        "validate_pr_body",
        "validate_github_approvals",
        "policyflow.validation.v2",
        "merge_readiness",
        "Removed Public API",
        "get_workflow_status",
        "audit_workflows",
        "runtime mutation helpers should move execution",
    ):
        assert expected in text

    for forbidden in (
        "audit_workflows(",
        "start_workflow_phase(",
        "record_workflow_handoff(",
    ):
        assert forbidden not in text


def test_schema_compatibility_docs_define_v2_schema_and_removed_v1_surface() -> None:
    text = _read("docs/schema-compatibility.md")

    for expected in (
        "## V2 Governance Schema",
        "version: 2",
        "change:",
        "risk:",
        "governance:",
        "confidence:",
        "evidence:",
        "overrides: []",
        "policyflow.validation.v2",
        "merge_readiness",
        "V1 Migration Diagnostics",
        "policyflow-v1-v2-migration-matrix.md",
        "Removed V1 Surface",
        "policyflow new-workflow",
        "policyflow sync",
        "policyflow audit",
    ):
        assert expected in text

    for forbidden in (
        "0.x compatibility window",
        "new generated workflows must use the canonical schema",
        "`runtime`: current orchestration state",
        "`policyflow audit --json` and `audit_workflows` expose",
    ):
        assert forbidden not in text


def test_v2_migration_guide_covers_matrix_removed_commands_and_external_owners() -> None:
    guide = _read("docs/v2-migration-guide.md")

    for expected in (
        "# PolicyFlow V2 Migration Guide",
        "policyflow-v1-v2-migration-matrix.md",
        "V1 To V2 Field Map",
        "`context`",
        "`execution`",
        "`runtime`",
        "`handoffs`",
        "`loop_governance`",
        "`evaluation`",
        "`overrides`",
        "Removed CLI Commands",
        "policyflow new-workflow",
        "policyflow sync",
        "policyflow audit",
        "policyflow evaluation-report",
        "policyflow loop-report",
        "Removed Public API",
        "Reporting Migration",
        "policyflow.validation.v2",
        "PolicyFlow 2.0 does not add `policyflow migrate`",
    ):
        assert expected in guide


def test_release_docs_and_changelog_prepare_v2_release() -> None:
    release = _read("docs/release-and-upgrade.md")
    changelog = _read("CHANGELOG.md")

    for expected in (
        "python -m pip install policyflow==2.0.1",
        "https://pypi.org/project/policyflow/2.0.1/",
        "https://github.com/MarcelDankert/PolicyFlow/releases/tag/v2.0.1",
        "POLICYFLOW_VERSION: \"2.0.1\"",
        "2.0.1 Release Artifact Checklist",
        "V2 `validate-pr --github-reviews` approval validation behavior",
        "V2 GitHub approval evidence convention",
        "V1 compatibility statement",
        "test and package build results",
    ):
        assert expected in release

    for expected in (
        "## 2.0.1",
        "V2 GitHub Approval Validation patch release",
        "Added V2 change-file support to `policyflow validate-pr`",
        "`source: github-review:<login>`",
        "Preserved V1 `validate-pr --github-reviews` behavior",
    ):
        assert expected in changelog


def test_package_metadata_targets_v2_release() -> None:
    data = tomllib.loads(_read("pyproject.toml"))
    project = data["project"]

    assert project["version"] == "2.0.1"
    assert "Provider-neutral governance validator" in project["description"]
    assert project["urls"]["Repository"] == "https://github.com/MarcelDankert/PolicyFlow"
    assert "Typing :: Typed" in project["classifiers"]


def test_github_workflow_pins_v2_release_for_consumers() -> None:
    for relative_path in (
        "github/workflows/policyflow-governance.yml",
        "policyflow/assets/github/workflows/policyflow-governance.yml",
    ):
        text = _read(relative_path)

        assert 'POLICYFLOW_VERSION: "2.0.1"' in text
        assert "contents: read" in text
        assert "pull-requests: read" in text
        assert "policyflow validate-pr" in text
        assert "validate-github-approvals" not in text


def test_public_repository_standard_files_are_present() -> None:
    expected_files = {
        "CONTRIBUTING.md": ("workflow-first", "pull request"),
        "SECURITY.md": ("security", "vulnerability"),
        "CHANGELOG.md": ("2.0.1", "V2 GitHub Approval Validation"),
    }

    for relative_path, expected_terms in expected_files.items():
        text = _read(relative_path)
        lowered = text.lower()

        for term in expected_terms:
            assert term.lower() in lowered
