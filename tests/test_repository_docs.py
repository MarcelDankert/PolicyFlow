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

    assert "PolicyFlow 2.0 Architecture Decision" in readme
    assert "ADR-0004: PolicyFlow 2.0 Returns To Governance Core" in readme
    assert "does not execute work" in readme
    v2_section = readme.split("## PolicyFlow 2.0 Architecture Decision", maxsplit=1)[1]
    v2_section = v2_section.split("## What PolicyFlow Is", maxsplit=1)[0]
    assert "workflow orchestration framework" not in v2_section
    assert "runner configuration" in v2_section
    assert "outside the V2 core" in v2_section
    assert "not a hosted scheduler, merge bot, or provider credential manager" in readme
    assert "policyflow init ." in readme
    assert "policyflow doctor ." in readme
    assert "Copy `github/ISSUE_TEMPLATE/*`" not in readme
    assert "Copy `rules/`, `agents/`, `workflows/`, and `prompts/`" not in readme
    assert "Not a runtime orchestration system" not in readme
    assert "GitHub API-based PR validation as a later target state" not in readme


def test_v2_governance_boundary_adrs_are_consistent() -> None:
    adr2 = (ROOT / "docs/adr/0002-policyflow-is-not-an-agent-runtime.md").read_text(
        encoding="utf-8"
    )
    adr4 = (ROOT / "docs/adr/0004-policyflow-v2-return-to-governance-core.md").read_text(
        encoding="utf-8"
    )
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "docs/roadmap-agentic-governance.md").read_text(
        encoding="utf-8"
    )

    assert "PolicyFlow will not become an agent runtime" in adr2
    assert "PolicyFlow 2.0 will return to a governance-only core" in adr4
    assert "| `runtime.py` | REMOVE |" in adr4
    assert "Runtime ownership is removed from core" in adr4
    assert "ADR-0004" in readme
    assert "ADR-0004 is the final PolicyFlow 2.0 architecture decision" in roadmap
    assert "V2 target: Governance Core" in roadmap
    assert "Target: Agentic Governance Platform" not in roadmap


def test_public_root_docs_do_not_include_machine_local_paths() -> None:
    for relative_path in ("AGENTS.md", "README.md"):
        text = (ROOT / relative_path).read_text(encoding="utf-8")

        assert "D:\\" not in text
        assert "C:\\" not in text


def test_getting_started_has_end_to_end_consumer_quickstart() -> None:
    text = (ROOT / "docs/getting-started.md").read_text(encoding="utf-8")

    assert "## Consumer Quickstart" in text
    for command in (
        "python -m pip install policyflow==1.0.0",
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
    ):
        assert removed_command not in text


def test_getting_started_documents_read_only_github_boundary() -> None:
    text = (ROOT / "docs/getting-started.md").read_text(encoding="utf-8")

    for expected in (
        "read-only",
        "contents",
        "pull-requests",
        "does not create branches",
        "mutate labels",
        "assign milestones",
        "approve pull requests",
        "merge pull requests",
        "check credentials",
    ):
        assert expected in text
    assert "--github-app-preflight" not in text
    assert "GH_TOKEN" not in text
    assert "D:\\" not in text
    assert "C:\\" not in text


def test_docs_clarify_high_risk_approval_evidence_contract() -> None:
    getting_started = (ROOT / "docs/getting-started.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "human_approval_required" in getting_started
    assert "approval evidence" in getting_started
    assert "external systems publish governance evidence" in getting_started
    assert "Approval evidence: `evidence.approval`" not in readme


def test_docs_define_pr_rerun_and_draft_stacked_semantics() -> None:
    getting_started = (ROOT / "docs/getting-started.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "docs/governance-enforcement-roadmap.md").read_text(
        encoding="utf-8"
    )
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "pull_request" in getting_started
    assert "pull_request_review" in getting_started
    assert "pending approval instead of a failed governance check" in getting_started
    assert "strict local or CI runs can omit `--allow-pending`" in getting_started
    assert "documentation-only guidance" in roadmap
    assert "Draft and stacked PRs need explicit merge-readiness semantics" in readme
    assert "the governance workflow reruns on" in readme
    assert "`pull_request_review` submitted and dismissed events" in readme


def test_docs_define_pending_approval_lifecycle_split() -> None:
    getting_started = (ROOT / "docs/getting-started.md").read_text(encoding="utf-8")
    packaged_getting_started = (
        ROOT / "policyflow/assets/docs/getting-started.md"
    ).read_text(encoding="utf-8")

    for expected in (
        'policyflow validate-pr "$workflow_path" pr-body.md --github-reviews pr-reviews.json --allow-pending',
        "pending approval instead of a failed governance check",
        "Use GitHub required approving review rules to block merge while approval is pending",
        "strict local or CI runs can omit `--allow-pending`",
    ):
        assert expected in getting_started

    assert packaged_getting_started == getting_started


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


def test_schema_docs_define_loop_governance_shape() -> None:
    schema = (ROOT / "docs/schema-compatibility.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "docs/roadmap-agentic-governance.md").read_text(
        encoding="utf-8"
    )

    for expected in (
        "loop_governance:",
        "source_phase:",
        "target_phase:",
        "allowed_feedback_sources:",
        "max_iterations:",
        "stop_conditions:",
        "escalation_conditions:",
        "evidence_refs:",
        "PolicyFlow does not execute loops",
        "does not schedule loop execution, route messages, or provide memory",
    ):
        assert expected in schema

    assert "Loop Governance defines feedback-loop rules declaratively" in roadmap


def test_audit_json_docs_define_machine_readable_contract() -> None:
    schema = (ROOT / "docs/schema-compatibility.md").read_text(encoding="utf-8")

    for expected in (
        "policyflow.audit.v1",
        "workflow_audit",
        "workflow_governance",
        "loop_governance",
        "evaluation_governance",
        "human_governance",
        "existing workflow audit fields remain present",
        "Downstream consumers should treat new top-level keys as additive",
    ):
        assert expected in schema


def test_audit_reporting_docs_define_usage_and_runtime_boundary() -> None:
    audit_doc = (ROOT / "docs/audit-reporting.md").read_text(encoding="utf-8")
    getting_started = (ROOT / "docs/getting-started.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    for expected in (
        "# Reporting Boundary",
        "## Supported Output",
        "## Removed Output",
        "## Runtime Boundary",
        "policyflow validate policyflow/change.example.yml --json",
        "policyflow validate-pr policyflow/change.example.yml pr-body.md --json",
        "merge_readiness.explanation",
        "merge_readiness.blockers",
        "policyflow.audit.v1",
        "validation JSON",
        "PolicyFlow does not execute workflows",
        "calculate metrics",
        "mutate GitHub state",
    ):
        assert expected in audit_doc

    for removed_command in (
        "policyflow audit ai/workflows",
        "policyflow evaluation-report ai/workflows",
        "policyflow loop-report ai/workflows",
    ):
        assert removed_command not in audit_doc

    assert "docs/audit-reporting.md" not in getting_started
    assert "docs/audit-reporting.md" in readme


def test_evaluation_governance_docs_define_consumer_usage() -> None:
    evaluation_doc = (ROOT / "docs/evaluation-governance.md").read_text(
        encoding="utf-8"
    )
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

    assert "docs/evaluation-governance.md" not in getting_started
    assert "docs/evaluation-governance.md" in readme


def test_metric_governance_docs_define_metric_boundaries() -> None:
    metric_doc = (ROOT / "docs/metric-governance.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "docs/roadmap-agentic-governance.md").read_text(
        encoding="utf-8"
    )

    for expected in (
        "## Metric Governance Model",
        "Metric declaration",
        "Metric source",
        "Metric evidence",
        "PolicyFlow validation",
        "PolicyFlow does not calculate all metrics",
        "Consumer-Repos own metric collection",
        "Querypilot metric examples",
        "only `SELECT` allowed",
        "SQL guardrails passed",
        "docs/metric-governance.md",
    ):
        assert expected in metric_doc or expected in roadmap

    assert "docs/metric-governance.md" in roadmap


def test_workflow_templates_reference_evaluation_schema() -> None:
    for relative_path in (
        "workflows/templates/feature-workflow.template.yml",
        "workflows/templates/bugfix-workflow.template.yml",
        "workflows/templates/architecture-change-workflow.template.yml",
        "workflows/templates/low-risk-workflow.template.yml",
    ):
        text = (ROOT / relative_path).read_text(encoding="utf-8")

        assert "evaluation:" in text
        assert "required_metrics" in text
        assert "thresholds" in text
        assert "evidence_refs" in text
        assert "compliance_status" in text
        assert "PolicyFlow does not run evaluation tooling" in text


def test_workflow_templates_reference_loop_governance_schema() -> None:
    for relative_path in (
        "workflows/templates/feature-workflow.template.yml",
        "workflows/templates/bugfix-workflow.template.yml",
        "workflows/templates/architecture-change-workflow.template.yml",
        "workflows/templates/low-risk-workflow.template.yml",
    ):
        text = (ROOT / relative_path).read_text(encoding="utf-8")

        assert "loop_governance:" in text
        assert "max_iterations" in text
        assert "stop_conditions" in text
        assert "escalation_conditions" in text
        assert "PolicyFlow does not execute loops" in text


def test_loop_governance_docs_reference_examples_and_failure_fixtures() -> None:
    loop_doc = (ROOT / "docs/loop-governance.md").read_text(encoding="utf-8")
    getting_started = (ROOT / "docs/getting-started.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    for expected in (
        "## Scope",
        "## Non-Scope",
        "## Required Fields",
        "## Evidence",
        "## Escalation Expectations",
        "## Consumer Usage",
        "## Examples",
        "workflows/examples/loop-governance-workflow.yml",
        "Querypilot-inspired SQL safety loop",
        "loop-governance-invalid-max.yml",
        "loop-governance-missing-stop-conditions.yml",
        "loop-governance-missing-escalation-conditions.yml",
        "PolicyFlow does not execute loops",
        "`stop_conditions.<id>`",
        "`escalation_conditions.<id>`",
    ):
        assert expected in loop_doc

    assert "docs/loop-governance.md" not in getting_started
    assert "docs/loop-governance.md" in readme


def test_workflow_templates_reference_release_readiness_evidence() -> None:
    for relative_path in (
        "workflows/templates/feature-workflow.template.yml",
        "workflows/templates/bugfix-workflow.template.yml",
        "workflows/templates/architecture-change-workflow.template.yml",
        "workflows/templates/low-risk-workflow.template.yml",
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

    assert "## Consumer Quickstart" in text
    assert "Copy `github/ISSUE_TEMPLATE/*`" not in text
    assert "Copy `rules/`, `agents/`, `workflows/`, and `prompts/`" not in text


def test_packaged_getting_started_matches_source_doc() -> None:
    source = (ROOT / "docs/getting-started.md").read_text(encoding="utf-8")
    packaged = (ROOT / "policyflow/assets/docs/getting-started.md").read_text(
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
    assert "policyflow validate-pr --github-reviews" in roadmap
    assert "GitHub API-based PR validation after the markdown-file workflow" not in roadmap


def test_agentic_governance_roadmap_keeps_automerge_out_of_v2_core() -> None:
    roadmap = (ROOT / "docs/roadmap-agentic-governance.md").read_text(
        encoding="utf-8"
    )

    for expected in (
        "Automerge Executor",
        "## Automerge Governance Boundary",
        "not part of the v2 core platform scope",
        "PolicyFlow should not merge pull requests",
        "A future Consumer Governance extension may define declarative automerge policy",
        "The execution of that policy remains outside PolicyFlow",
        "LOW-risk automerge may be described as a future governance policy option",
        "MEDIUM-risk automerge should require an explicit human signal",
        "HIGH-risk automerge is out of scope",
    ):
        assert expected in roadmap


def test_release_docs_define_pinned_release_channel_and_artifacts() -> None:
    text = (ROOT / "docs/release-and-upgrade.md").read_text(encoding="utf-8")

    assert "python -m pip install policyflow==1.0.0" in text
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


def test_schema_compatibility_docs_define_v2_stable_governance_boundaries() -> None:
    schema = (ROOT / "docs/schema-compatibility.md").read_text(encoding="utf-8")
    public_api = (ROOT / "docs/public-api.md").read_text(encoding="utf-8")

    for expected in (
        "## v2 Stable Governance Boundary",
        "Workflow Governance",
        "Loop Governance",
        "Evaluation Governance",
        "Metric Governance",
        "Human Governance",
        "Audit Governance",
        "## v2 Breaking Changes From 0.x",
        "root-level fallback fields are deprecated",
        "new v2 workflow instances must use canonical `context` and `governance` fields",
        "HIGH-risk workflows must carry `evidence.approval`",
        "audit JSON consumers must read `schema_version`",
        "## v2 Migration Steps",
        "move root-level fallback fields into `context` and `governance`",
        "add missing `evaluation` categories and required metrics",
        "add missing `loop_governance` stop and escalation evidence",
        "verify audit integrations against `policyflow.audit.v1`",
    ):
        assert expected in schema

    for expected in (
        "PolicyFlow 2.0 exposes a governance-only public API",
        "Internal modules remain outside the compatibility boundary",
        "validate_workflow_v2",
        "inspect_workflow_v2",
        "validate_pr_body",
        "validate_github_approvals",
        "Removed Public API",
        "runtime mutation helpers should move execution and workflow state handling to external runtimes",
    ):
        assert expected in public_api


def test_v2_migration_guide_covers_contract_changes_and_examples() -> None:
    guide = (ROOT / "docs/v2-migration-guide.md").read_text(encoding="utf-8")
    release = (ROOT / "docs/release-and-upgrade.md").read_text(encoding="utf-8")

    for expected in (
        "# PolicyFlow v2 Migration Guide",
        "## Migration Scope",
        "## Deprecated 0.x Fallbacks",
        "## Workflow Governance Migration",
        "Before",
        "After",
        "workflow_file:",
        "context:",
        "governance:",
        "## Loop Governance Migration",
        "loop_governance:",
        "stop_conditions:",
        "escalation_conditions:",
        "## Evaluation And Metric Migration",
        "evaluation:",
        "required_metrics:",
        "evidence_refs:",
        "## Human Governance Migration",
        "evidence.approval",
        "governance.approval_evidence is not sufficient",
        "## Audit Integration Migration",
        "policyflow.audit.v1",
        "schema_version",
        "workflow_governance",
        "loop_governance",
        "evaluation_governance",
        "human_governance",
        "## Validation Checklist",
        "policyflow validate",
        "policyflow validate-pr",
        "policyflow audit",
        "policyflow evaluation-report",
        "policyflow loop-report",
        "PolicyFlow does not execute workflows",
    ):
        assert expected in guide

    assert "docs/v2-migration-guide.md" in release


def test_provider_neutral_integration_contract_defines_evidence_boundary() -> None:
    contract = (ROOT / "docs/provider-neutral-integration-contract.md").read_text(
        encoding="utf-8"
    )
    runner = (ROOT / "docs/runner-contract.md").read_text(encoding="utf-8")
    public_api = (ROOT / "docs/public-api.md").read_text(encoding="utf-8")

    for expected in (
        "# Provider-Neutral Integration Contract",
        "## Contract Purpose",
        "## Integration Responsibilities",
        "## Workflow Evidence",
        "## Loop Evidence",
        "## Evaluation Evidence",
        "## Human Governance Evidence",
        "## Audit And Reporting",
        "## Non-Goals",
        "external runtimes",
        "CI systems",
        "agent frameworks",
        "evidence producers",
        "PolicyFlow validates and reports",
        "PolicyFlow does not execute external systems",
        "provider SDK",
        "provider credentials",
        "workflow_file:",
        "evidence:",
        "loop_governance:",
        "evaluation:",
        "evidence.approval",
        "policyflow.audit.v1",
        "policyflow.api",
        "policyflow validate",
        "policyflow audit",
    ):
        assert expected in contract

    assert "docs/provider-neutral-integration-contract.md" in runner
    assert "provider-neutral-integration-contract.md" in public_api


def test_querypilot_pilot_docs_define_governance_boundaries() -> None:
    pilot = (ROOT / "docs/querypilot-pilot.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "docs/roadmap-agentic-governance.md").read_text(
        encoding="utf-8"
    )
    example = (
        ROOT / "workflows/examples/querypilot-pilot-workflow.yml"
    ).read_text(encoding="utf-8")

    for expected in (
        "# Querypilot Pilot",
        "## Governance Goals",
        "## Metrics",
        "## Loops",
        "## Evidence",
        "## Non-Goals",
        "## Responsibility Split",
        "SQL guardrail",
        "SELECT-only",
        "executable SQL",
        "tests",
        "coverage",
        "latency",
        "review score",
        "security findings",
        "PolicyFlow validates and reports",
        "Querypilot owns",
        "PolicyFlow does not execute SQL",
        "workflows/examples/querypilot-pilot-workflow.yml",
    ):
        assert expected in pilot

    for expected in (
        "querypilot-sql-guardrail",
        "select-only",
        "executable-sql",
        "test-pass-rate",
        "coverage-percent",
        "p95-latency-ms",
        "review-score",
        "security-findings",
        "sql-safety-loop",
        "loop_governance:",
        "evaluation:",
    ):
        assert expected in example

    assert "docs/querypilot-pilot.md" in roadmap
    assert "workflows/examples/querypilot-pilot-workflow.yml" in roadmap


def test_schema_todo_was_replaced_with_migration_path() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    schemas = (ROOT / "policyflow/schemas.py").read_text(encoding="utf-8")

    assert "Normalize the workflow schema into a single canonical governance block" not in readme
    assert "TODO: Normalize workflow governance" not in schemas


def test_public_api_docs_define_stable_import_boundary() -> None:
    text = (ROOT / "docs/public-api.md").read_text(encoding="utf-8")

    assert "from policyflow import inspect_workflow_v2, validate_pr_body" in text
    assert "validate_workflow_v2" in text
    assert "inspect_workflow_v2" in text
    assert "validate_github_approvals" in text
    assert "get_workflow_status" in text
    assert "start_workflow_phase" in text
    assert "audit_workflows" in text
    assert "removed from the public API" in text
    assert "Internal modules remain outside the compatibility boundary" in text


def test_public_repository_standard_files_are_present() -> None:
    expected_files = {
        "CONTRIBUTING.md": ("workflow-first", "pull request"),
        "SECURITY.md": ("security", "vulnerability"),
        "CHANGELOG.md": ("1.0.0", "Agentic Governance Platform"),
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
    assert "PolicyFlow `1.0.0` is published" in readme


def test_release_docs_reflect_published_release_state() -> None:
    for relative_path in ("README.md", "docs/getting-started.md", "docs/release-and-upgrade.md"):
        text = (ROOT / relative_path).read_text(encoding="utf-8")

        assert "policyflow==1.0.0" in text
        assert "once `policyflow==1.0.0` is published" not in text
        assert "https://pypi.org/project/policyflow/1.0.0/" in text
        assert "https://github.com/MarcelDankert/PolicyFlow/releases/tag/v1.0.0" in text


def test_pyproject_has_public_package_metadata() -> None:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = data["project"]

    assert project["authors"]
    assert project["keywords"]
    assert project["classifiers"]
    assert project["urls"]["Repository"] == "https://github.com/MarcelDankert/PolicyFlow"
    assert project["urls"]["Documentation"].endswith("#readme")
    assert "Typing :: Typed" in project["classifiers"]
