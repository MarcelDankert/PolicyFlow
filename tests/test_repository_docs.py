from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parents[1]


def test_repository_agents_guidance_is_discoverable() -> None:
    agents_path = ROOT / "AGENTS.md"

    assert agents_path.exists()

    text = agents_path.read_text(encoding="utf-8")
    assert "PolicyFlow Agent Guidance" in text
    assert "Repository Identity" in text
    assert "Workflow-First Delivery" in text
    assert "Required Validation" in text
    assert "Framework Asset Boundaries" in text


def test_readme_links_repository_agents_guidance() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "AGENTS.md" in readme
    assert "PolicyFlow repository guidance" in readme


def test_readme_has_public_repository_status_badges() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "actions/workflows/policyflow-governance.yml/badge.svg" in readme
    assert "img.shields.io/pypi/v/policyflow.svg" in readme
    assert "img.shields.io/pypi/pyversions/policyflow.svg" in readme
    assert "License-MIT" in readme
    assert "typed-yes" in readme


def test_readme_matches_current_consumer_onboarding_positioning() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "lightweight workflow orchestration layer" in readme
    assert "not a hosted scheduler, merge bot, or provider credential manager" in readme
    assert "policyflow init ." in readme
    assert "policyflow doctor ." in readme
    assert "Copy `github/ISSUE_TEMPLATE/*`" not in readme
    assert "Copy `rules/`, `agents/`, `workflows/`, and `prompts/`" not in readme
    assert "Not a runtime orchestration system" not in readme
    assert "GitHub API-based PR validation as a later target state" not in readme


def test_public_root_docs_do_not_include_machine_local_paths() -> None:
    for relative_path in ("AGENTS.md", "README.md"):
        text = (ROOT / relative_path).read_text(encoding="utf-8")

        assert "D:\\" not in text
        assert "C:\\" not in text


def test_getting_started_has_end_to_end_consumer_quickstart() -> None:
    text = (ROOT / "docs/getting-started.md").read_text(encoding="utf-8")

    assert "## Consumer Quickstart" in text
    for command in (
        "python -m pip install policyflow==0.2.0",
        "policyflow init .",
        "policyflow doctor .",
        "policyflow new-workflow feature --id first-feature --risk LOW",
        "policyflow validate ai/workflows/features/first-feature.yml",
        "policyflow status ai/workflows/features/first-feature.yml",
        "policyflow audit ai/workflows",
        "policyflow validate-pr ai/workflows/features/first-feature.yml pr-body.md",
        "policyflow validate-github-approvals ai/workflows/features/first-feature.yml pr-body.md pr-reviews.json",
        "policyflow sync .",
    ):
        assert command in text


def test_getting_started_documents_github_app_governance_preflight() -> None:
    text = (ROOT / "docs/getting-started.md").read_text(encoding="utf-8")

    assert "policyflow doctor . --github-app-preflight OWNER/REPO" in text
    for capability in (
        "read metadata",
        "create branches",
        "push commits",
        "create/edit issues",
        "create/edit pull requests",
        "apply labels",
        "assign milestones",
        "read pull request reviews",
    ):
        assert capability in text
    assert "GH_TOKEN" in text
    assert "D:\\" not in text
    assert "C:\\" not in text


def test_docs_clarify_high_risk_approval_evidence_contract() -> None:
    getting_started = (ROOT / "docs/getting-started.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "governance.approval_evidence" in getting_started
    assert "evidence.approval" in getting_started
    assert "evidence.approval.approved_by" in getting_started
    assert (
        "PR approval validation reads the required GitHub login from "
        "`evidence.approval.approved_by`"
    ) in getting_started
    assert "governance.approval_evidence` does not replace `evidence.approval" in getting_started
    assert "Approval evidence: `evidence.approval`" in readme


def test_docs_define_pr_rerun_and_draft_stacked_semantics() -> None:
    getting_started = (ROOT / "docs/getting-started.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "docs/governance-enforcement-roadmap.md").read_text(
        encoding="utf-8"
    )
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "editing a PR body may not trigger a new GitHub Actions run" in getting_started
    assert "rerun the failed PolicyFlow job or push a new commit" in getting_started
    assert "draft PRs are planning or preview artifacts" in getting_started
    assert "stacked PRs are dependency-bound" in getting_started
    assert "not normal merge candidates until upstream dependencies are merged or otherwise satisfied" in getting_started
    assert "documentation-only guidance" in roadmap
    assert "Draft and stacked PRs need explicit merge-readiness semantics" in readme


def test_release_docs_define_release_readiness_artifact_shape() -> None:
    release = (ROOT / "docs/release-and-upgrade.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "docs/governance-enforcement-roadmap.md").read_text(
        encoding="utf-8"
    )

    for expected in (
        "release_readiness:",
        "release_blockers:",
        "blocked_issues:",
        "issue_ordering:",
        "external_credentials_required:",
        "non_executable_checks:",
        "draft_prs:",
        "done",
        "preparatory",
        "blocked",
        "ready for release",
    ):
        assert expected in release

    assert "does not make PolicyFlow a release orchestrator or scheduler" in release
    assert "release-readiness evidence remains declarative" in roadmap


def test_schema_docs_define_evaluation_governance_shape() -> None:
    schema = (ROOT / "docs/schema-compatibility.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "docs/roadmap-agentic-governance.md").read_text(
        encoding="utf-8"
    )

    for expected in (
        "evaluation:",
        "categories:",
        "required_metrics:",
        "thresholds:",
        "evidence_refs:",
        "compliance_status:",
        "PolicyFlow does not run evaluation tooling",
    ):
        assert expected in schema

    assert "Evaluation Governance defines measurable quality criteria" in roadmap
    assert "PolicyFlow should not execute evaluation tooling" in schema


def test_evaluation_governance_docs_define_consumer_usage() -> None:
    evaluation_doc = (ROOT / "docs/evaluation-governance.md").read_text(
        encoding="utf-8"
    )
    packaged_doc = (
        ROOT / "policyflow/assets/docs/evaluation-governance.md"
    ).read_text(encoding="utf-8")
    getting_started = (ROOT / "docs/getting-started.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    for expected in (
        "## Scope",
        "## Non-Scope",
        "## Required Fields",
        "## Evidence",
        "## Examples",
        "workflows/examples/evaluation-governance-workflow.yml",
        "CI, scanners, test tooling, benchmark tools, and human reviewers remain external",
        "PolicyFlow records, validates, and reports declared evaluation governance",
    ):
        assert expected in evaluation_doc

    assert packaged_doc == evaluation_doc
    assert "docs/evaluation-governance.md" in getting_started
    assert "docs/evaluation-governance.md" in readme


def test_workflow_templates_reference_evaluation_schema() -> None:
    for relative_path in (
        "workflows/templates/feature-workflow.template.yml",
        "workflows/templates/bugfix-workflow.template.yml",
        "workflows/templates/architecture-change-workflow.template.yml",
        "workflows/templates/low-risk-workflow.template.yml",
        "policyflow/assets/workflows/templates/feature-workflow.template.yml",
        "policyflow/assets/workflows/templates/bugfix-workflow.template.yml",
        "policyflow/assets/workflows/templates/architecture-change-workflow.template.yml",
        "policyflow/assets/workflows/templates/low-risk-workflow.template.yml",
    ):
        text = (ROOT / relative_path).read_text(encoding="utf-8")

        assert "evaluation:" in text
        assert "required_metrics" in text
        assert "thresholds" in text
        assert "evidence_refs" in text
        assert "compliance_status" in text
        assert "PolicyFlow does not run evaluation tooling" in text


def test_workflow_templates_reference_release_readiness_evidence() -> None:
    for relative_path in (
        "workflows/templates/feature-workflow.template.yml",
        "workflows/templates/bugfix-workflow.template.yml",
        "workflows/templates/architecture-change-workflow.template.yml",
        "workflows/templates/low-risk-workflow.template.yml",
        "policyflow/assets/workflows/templates/feature-workflow.template.yml",
        "policyflow/assets/workflows/templates/bugfix-workflow.template.yml",
        "policyflow/assets/workflows/templates/architecture-change-workflow.template.yml",
        "policyflow/assets/workflows/templates/low-risk-workflow.template.yml",
    ):
        text = (ROOT / relative_path).read_text(encoding="utf-8")

        assert "release_readiness" in text
        assert "done, preparatory, blocked, or ready for release" in text


def test_pr_template_shows_high_risk_approval_evidence_path() -> None:
    for relative_path in (
        "github/PULL_REQUEST_TEMPLATE.md",
        "policyflow/assets/github/PULL_REQUEST_TEMPLATE.md",
    ):
        text = (ROOT / relative_path).read_text(encoding="utf-8")

        assert "Approval evidence: `evidence.approval`" in text
        assert "governance.human_approval_required: true" in text
        assert "evidence.approval.approved_by" in text


def test_getting_started_keeps_manual_copy_out_of_primary_path() -> None:
    text = (ROOT / "docs/getting-started.md").read_text(encoding="utf-8")

    assert "## Advanced Manual Adoption" in text
    primary_text = text.split("## Advanced Manual Adoption", maxsplit=1)[0]

    assert "Copy `github/ISSUE_TEMPLATE/*`" not in primary_text
    assert "Copy `rules/`, `agents/`, `workflows/`, and `prompts/`" not in primary_text


def test_packaged_getting_started_matches_source_doc() -> None:
    for relative_path in (
        "evaluation-governance.md",
        "getting-started.md",
        "overview.md",
        "governance-enforcement-roadmap.md",
        "public-api.md",
        "release-and-upgrade.md",
        "schema-compatibility.md",
    ):
        source = (ROOT / "docs" / relative_path).read_text(encoding="utf-8")
        packaged = (ROOT / "policyflow/assets/docs" / relative_path).read_text(
            encoding="utf-8"
        )

        assert packaged == source


def test_overview_and_roadmap_reflect_current_capabilities() -> None:
    overview = (ROOT / "docs/overview.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "docs/governance-enforcement-roadmap.md").read_text(
        encoding="utf-8"
    )

    assert "future automated governance validation" not in overview
    assert "lightweight workflow orchestration layer" in overview
    assert "policyflow new-workflow" in roadmap
    assert "policyflow validate-github-approvals" in roadmap
    assert "GitHub API-based PR validation after the markdown-file workflow" not in roadmap


def test_release_docs_define_pinned_release_channel_and_artifacts() -> None:
    text = (ROOT / "docs/release-and-upgrade.md").read_text(encoding="utf-8")

    assert "python -m pip install policyflow==0.2.0" in text
    assert "PyPI" in text
    assert "GitHub Release" in text
    assert "policyflow sync ." in text
    assert "policyflow validate" in text
    assert "release artifacts" in text


def test_schema_compatibility_docs_define_canonical_and_legacy_policy() -> None:
    text = (ROOT / "docs/schema-compatibility.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    release = (ROOT / "docs/release-and-upgrade.md").read_text(encoding="utf-8")

    assert "## Canonical Workflow Schema" in text
    assert "context.workflow_file" in text
    assert "governance.required_reviews" in text
    assert "root-level fallback fields" in text
    assert "0.x compatibility window" in text
    assert "new generated workflows must use the canonical schema" in text
    assert "policyflow validate" in text
    assert "policyflow new-workflow" in text
    assert "policyflow sync ." in text
    assert "policyflow.api" in text
    assert "docs/schema-compatibility.md" in readme
    assert "schema compatibility" in release


def test_schema_todo_was_replaced_with_migration_path() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    schemas = (ROOT / "policyflow/schemas.py").read_text(encoding="utf-8")

    assert "Normalize the workflow schema into a single canonical governance block" not in readme
    assert "TODO: Normalize workflow governance" not in schemas


def test_public_api_docs_define_stable_import_boundary() -> None:
    text = (ROOT / "docs/public-api.md").read_text(encoding="utf-8")

    assert "from policyflow import validate_workflow" in text
    assert "from policyflow.api import validate_pr_body" in text
    assert "get_workflow_status" in text
    assert "start_workflow_phase" in text
    assert "audit_workflows" in text
    assert "validate_github_approvals" in text
    assert "internal implementation details" in text


def test_public_repository_standard_files_are_present() -> None:
    expected_files = {
        "CONTRIBUTING.md": ("workflow-first", "pull request"),
        "SECURITY.md": ("security", "vulnerability"),
        "CHANGELOG.md": ("0.2.0", "Evaluation Governance"),
    }

    for relative_path, expected_terms in expected_files.items():
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        lowered = text.lower()

        for term in expected_terms:
            assert term.lower() in lowered


def test_readme_uses_finished_compatibility_language() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "TODO:" not in readme
    assert "## Compatibility" in readme
    assert "docs/schema-compatibility.md" in readme
    assert "## Project Status" in readme
    assert "PolicyFlow `0.2.0` is published" in readme


def test_release_docs_reflect_published_release_state() -> None:
    for relative_path in ("README.md", "docs/getting-started.md", "docs/release-and-upgrade.md"):
        text = (ROOT / relative_path).read_text(encoding="utf-8")

        assert "policyflow==0.2.0" in text
        assert "once `policyflow==0.2.0` is published" not in text
        assert "https://pypi.org/project/policyflow/0.2.0/" in text
        assert "https://github.com/MarcelDankert/PolicyFlow/releases/tag/v0.2.0" in text


def test_pyproject_has_public_package_metadata() -> None:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = data["project"]

    assert project["authors"]
    assert project["keywords"]
    assert project["classifiers"]
    assert project["urls"]["Repository"] == "https://github.com/MarcelDankert/PolicyFlow"
    assert project["urls"]["Documentation"].endswith("#readme")
    assert "Typing :: Typed" in project["classifiers"]
