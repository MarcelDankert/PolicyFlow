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
