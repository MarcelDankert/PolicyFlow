from pathlib import Path


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


def test_public_root_docs_do_not_include_machine_local_paths() -> None:
    for relative_path in ("AGENTS.md", "README.md"):
        text = (ROOT / relative_path).read_text(encoding="utf-8")

        assert "D:\\" not in text
        assert "C:\\" not in text


def test_getting_started_has_end_to_end_consumer_quickstart() -> None:
    text = (ROOT / "docs/getting-started.md").read_text(encoding="utf-8")

    assert "## Consumer Quickstart" in text
    for command in (
        "python -m pip install policyflow==0.1.0",
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


def test_getting_started_keeps_manual_copy_out_of_primary_path() -> None:
    text = (ROOT / "docs/getting-started.md").read_text(encoding="utf-8")

    assert "## Advanced Manual Adoption" in text
    primary_text = text.split("## Advanced Manual Adoption", maxsplit=1)[0]

    assert "Copy `github/ISSUE_TEMPLATE/*`" not in primary_text
    assert "Copy `rules/`, `agents/`, `workflows/`, and `prompts/`" not in primary_text


def test_packaged_getting_started_matches_source_doc() -> None:
    for relative_path in (
        "getting-started.md",
        "overview.md",
        "governance-enforcement-roadmap.md",
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
