from __future__ import annotations

from pathlib import Path

import yaml

from policyflow.bootstrap import bootstrap_consumer_repo
from policyflow.doctor import doctor_consumer_repo


ROOT = Path(__file__).resolve().parents[1]


def test_consumer_github_actions_template_has_governance_steps() -> None:
    workflow_path = ROOT / "github" / "workflows" / "policyflow-governance.yml"

    data = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    text = workflow_path.read_text(encoding="utf-8")

    assert data["name"] == "PolicyFlow Governance"
    assert data["permissions"]["contents"] == "read"
    assert data["permissions"]["pull-requests"] == "read"
    assert "pull_request_review:" in text
    assert "types: [submitted, dismissed]" in text
    steps = data["jobs"]["validate-policyflow"]["steps"]
    step_names = {step["name"] for step in steps}
    assert "Install PolicyFlow" in step_names
    assert "Resolve PR number" in step_names
    assert "Fetch live PR body" in step_names
    assert "Fetch PR reviews" in step_names
    assert "Validate PR body governance" in step_names
    resolve_step = next(step for step in steps if step["name"] == "Resolve PR number")
    assert "github.event.review.pull_request_url" in resolve_step["env"]["REVIEW_PULL_REQUEST_URL"]
    assert "REVIEW_PULL_REQUEST_URL##*/" in resolve_step["run"]
    validate_step = next(step for step in steps if step["name"] == "Validate PR body governance")
    assert "policyflow validate-pr" in validate_step["run"]
    assert "policyflow validate-github-approvals" in validate_step["run"]
    assert "--allow-pending" in validate_step["run"]
    install_step = next(step for step in steps if step["name"] == "Install PolicyFlow")
    assert "python -m pip install \"policyflow==${POLICYFLOW_VERSION}\"" in install_step["run"]
    assert "pip install policyflow\n" not in install_step["run"]


def test_repository_github_actions_workflow_reruns_on_review_events() -> None:
    workflow_path = ROOT / ".github" / "workflows" / "policyflow-governance.yml"

    text = workflow_path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)

    assert data["permissions"]["pull-requests"] == "read"
    assert "pull_request_review:" in text
    assert "types: [submitted, dismissed]" in text
    steps = data["jobs"]["validate-governance"]["steps"]
    step_names = {step["name"] for step in steps}
    assert "Resolve PR number" in step_names
    resolve_step = next(step for step in steps if step["name"] == "Resolve PR number")
    assert "github.event.review.pull_request_url" in resolve_step["env"]["REVIEW_PULL_REQUEST_URL"]
    assert "REVIEW_PULL_REQUEST_URL##*/" in resolve_step["run"]
    validate_step = next(step for step in steps if step["name"] == "Validate PR body governance")
    assert "--allow-pending" in validate_step["run"]


def test_packaged_consumer_github_actions_template_matches_source() -> None:
    source = ROOT / "github" / "workflows" / "policyflow-governance.yml"
    packaged = ROOT / "policyflow/assets/github/workflows/policyflow-governance.yml"

    assert packaged.read_text(encoding="utf-8") == source.read_text(encoding="utf-8")


def test_bootstrap_installs_consumer_github_actions_workflow(tmp_path: Path) -> None:
    result = bootstrap_consumer_repo(tmp_path)

    workflow_path = tmp_path / ".github/workflows/policyflow-governance.yml"

    assert workflow_path.exists()
    assert ".github/workflows/policyflow-governance.yml" in result.created


def test_doctor_passes_github_workflow_artifact_after_bootstrap(tmp_path: Path) -> None:
    bootstrap_consumer_repo(tmp_path)

    report = doctor_consumer_repo(tmp_path)

    assert report["ready"] is True
    github_template_check = next(
        check for check in report["checks"] if check["check"] == "github_templates"
    )
    assert github_template_check["status"] == "pass"
