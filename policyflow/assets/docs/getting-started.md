# Getting Started

## Consumer Quickstart

Use this path for a fresh Consumer-Repo. It starts from a package install,
bootstraps the standard layout, creates the first governed workflow, and reaches
the first PR governance checks without manually copying PolicyFlow directories.

Install and pin PolicyFlow:

```bash
python -m pip install policyflow==0.2.0
```

Release links: [PyPI](https://pypi.org/project/policyflow/0.2.0/) and
[GitHub Release](https://github.com/MarcelDankert/PolicyFlow/releases/tag/v0.2.0).

Use the same package pin in local setup, CI, and GitHub Actions. See
[release-and-upgrade.md](release-and-upgrade.md) for release notes and upgrade
expectations.

Bootstrap the Consumer-Repo:

```bash
policyflow init .
```

Bootstrap writes:

- `policyflow.yml`
- `policyflow.runners.yml`
- `.policyflow/bootstrap.json`
- `ai/project-context.yml`
- `ai/agents/`, `ai/prompts/`, `ai/rules/`
- `ai/workflows/templates/`
- `ai/workflows/features/starter-workflow.yml`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `.github/ISSUE_TEMPLATE/`
- `.github/workflows/policyflow-governance.yml`

Preview or force bootstrap only when needed:

```bash
policyflow init . --dry-run
policyflow init . --force
```

Make the minimal project-specific edits:

- update `ai/project-context.yml`
- choose local-only or GitHub-governed features in `policyflow.yml`
- configure `policyflow.runners.yml` if you will run agent-owned phases
- keep project-specific overlays separate from managed assets

Validate readiness:

```bash
policyflow config-check policyflow.yml
policyflow doctor .
policyflow doctor . --json
```

For GitHub-governed repos, run the GitHub App governance preflight before
release orchestration or PR automation:

```bash
policyflow doctor . --github-app-preflight OWNER/REPO
```

The preflight uses GitHub CLI with `GH_TOKEN` or `GITHUB_TOKEN`; set that
environment variable to the GitHub App installation token that release or PR
automation will use. It verifies non-mutating repository access and reports the
governance capabilities that must be available before mutation:

- read metadata
- create branches
- push commits
- create/edit issues
- create/edit pull requests
- apply labels
- assign milestones
- read pull request reviews

When GitHub returns App permission metadata, missing capabilities identify the
likely GitHub permission area, such as `Contents: write`, `Issues: write`, or
`Pull requests: write`.

Create the first real governed workflow:

```bash
policyflow new-workflow feature --id first-feature --risk LOW
policyflow validate ai/workflows/features/first-feature.yml
policyflow status ai/workflows/features/first-feature.yml
policyflow audit ai/workflows
```

Other first workflow shapes:

```bash
policyflow new-workflow bugfix --id parser-fix --risk MEDIUM
policyflow new-workflow architecture-change --id storage-boundary --risk HIGH
policyflow new-workflow low-risk --id docs-update --risk LOW
```

Preview or overwrite generated workflows only when intentional:

```bash
policyflow new-workflow feature --id preview-feature --risk LOW --dry-run
policyflow new-workflow feature --id first-feature --risk LOW --force
```

## Runner Setup

PolicyFlow uses a provider-neutral `type: command` runner contract. Any local
CLI, hosted-adapter wrapper, or internal runner can execute phases if it reads
PolicyFlow input JSON and writes PolicyFlow result JSON.

See [runner-contract.md](runner-contract.md) for the command placeholders,
input/output JSON contract, blocked/completed semantics, and Codex reference
adapter.

After configuring the selected runner, execute an agent-owned phase:

```bash
policyflow run-phase ai/workflows/features/first-feature.yml implementation
```

If the runner cannot execute, PolicyFlow blocks the phase with an actionable
reason instead of leaving workflow state ambiguous.

## First PR Governance

Open the PR with the installed pull request template and fill these sections
from the generated workflow:

- linked issue
- workflow file path
- declared risk level
- confidence summary from `context.confidence`
- evidence references such as `evidence.planning`
- override references when overrides exist
- human approval login and reference when required
- checked workflow governance confirmations

Validate the PR body locally before pushing or while iterating:

```bash
policyflow validate-pr ai/workflows/features/first-feature.yml pr-body.md
```

For GitHub-governed repos, validate review metadata as well:

```bash
policyflow validate-github-approvals ai/workflows/features/first-feature.yml pr-body.md pr-reviews.json
```

The installed GitHub Actions workflow performs the PR body and GitHub approval
checks automatically on pull requests.

If a PolicyFlow PR check fails because the PR body is incomplete, update the PR
body and then rerun the failed PolicyFlow job or push a new commit. In GitHub,
editing a PR body may not trigger a new GitHub Actions run by itself, so the old
failed check can remain visible until the job is rerun.

Treat draft PRs and stacked PRs as explicit governance states:

- draft PRs are planning or preview artifacts unless the author promotes them to
  merge readiness and the PR body, workflow evidence, and required checks all
  support that state
- stacked PRs are dependency-bound and not normal merge candidates until upstream dependencies are merged or otherwise satisfied

For `HIGH` risk workflows with `governance.human_approval_required: true`, keep
the governance declaration and the approval evidence separate:

- `governance.approval_evidence` describes which human approval is required by
  the workflow.
- `evidence.approval` records the concrete approval evidence used by PR
  validation.
- PR approval validation reads the required GitHub login from `evidence.approval.approved_by`
  and expects the PR body to reference
  `Approval evidence: evidence.approval`.

`governance.approval_evidence` does not replace `evidence.approval`; HIGH-risk
approval-gated workflows need the `evidence.approval.approved_by`,
`evidence.approval.reference`, and `evidence.approval.scope_confirmed` fields
for actionable PR approval validation.

## Local-Only Adoption

Use local-only adoption when you want PolicyFlow validation and workflow state
without GitHub enforcement:

```yaml
version: 1

features:
  pr_validation: false
  github_approval_checks: false
  runner_execution: false
  bootstrap_managed_assets: false
```

Local-only repos can still use `validate`, `status`, `audit`, `doctor`, and
`new-workflow`.

## GitHub-Governed Adoption

Use GitHub-governed adoption when PR templates, issue templates, and the
governance workflow should enforce PolicyFlow checks:

```yaml
version: 1

paths:
  workflows: ai/workflows
  prompts: ai/prompts
  agents: ai/agents
  rules: ai/rules
  project_context: ai/project-context.yml
  runner_config: policyflow.runners.yml
  pr_template: .github/PULL_REQUEST_TEMPLATE.md
  issue_templates: .github/ISSUE_TEMPLATE
  governance_workflow: .github/workflows/policyflow-governance.yml

features:
  pr_validation: true
  github_approval_checks: true
  runner_execution: true
  bootstrap_managed_assets: true
```

The generated workflow uses read-only `contents` and `pull-requests`
permissions, fetches live PR body and review metadata, and runs
`policyflow validate-pr` plus `policyflow validate-github-approvals`.

## Confidence And Evidence

Every workflow file must declare confidence in `context.confidence` before
implementation starts:

```yaml
context:
  workflow_file: ai/workflows/features/example.yml
  risk_level: MEDIUM
  confidence:
    planning: Scope, non-goals, and risk are stable enough for implementation.
    implementation: Implementation is bounded by the declared module constraints.
    tests: Direct validation and regression checks are planned.
    residual_uncertainty: Review must confirm no hidden contract impact.
```

The PR `Confidence summary` should summarize these four fields instead of
introducing a separate confidence claim.

## Evaluation Governance

When a workflow needs measurable quality criteria, declare an optional
`evaluation` block with categories, required metrics, thresholds, status, and
evidence references. See
[evaluation-governance.md](evaluation-governance.md) for the full Consumer-Repo
guide. The repository source path is `docs/evaluation-governance.md`. Use
`workflows/examples/evaluation-governance-workflow.yml` as a provider-neutral
example covering tests, coverage, review, security, and performance.

CI, scanners, test tooling, benchmark tools, and human reviewers remain
external. PolicyFlow validates declared evaluation governance metadata; it does
not execute or fetch the underlying checks.

## Loop Governance

When a workflow needs bounded feedback loops, declare an optional
`loop_governance` block with source and target phases, allowed feedback sources,
iteration limits, stop conditions, escalation conditions, status, and evidence
references. See [loop-governance.md](loop-governance.md) for the full
Consumer-Repo guide. The repository source path is `docs/loop-governance.md`.
Use `workflows/examples/loop-governance-workflow.yml` as a provider-neutral
example covering review, QA, security, human arbitration, and
Querypilot-inspired SQL safety loops.

Reviewers, QA systems, scanners, SQL review tools, agent runtimes, and human
owners remain external. PolicyFlow validates declared loop governance metadata;
it does not execute loops, schedule loop execution, route messages, provide
memory, or call provider runtimes.

## Upgrade Managed Assets

Preview managed asset changes after upgrading the PolicyFlow package:

```bash
policyflow sync .
```

Apply safe upstream asset updates when no local modifications block the change:

```bash
policyflow sync . --apply
```

Use `--force` only when the Consumer-Repo intentionally accepts overwriting
locally modified managed assets.

PolicyFlow's golden Consumer-Repo smoke test guards this plug-and-play path by
bootstrapping a temporary repo, running doctor, generating and validating a
workflow, executing one implementation phase through a local fake runner, and
validating a starter PR body without real provider or GitHub network calls.

## Advanced Manual Adoption

Prefer `policyflow init` for normal adoption. Manual copying is only for unusual
repositories that cannot run bootstrap.

If you must install assets manually, copy the same generated layout that
bootstrap would create and then run:

```bash
policyflow config-check policyflow.yml
policyflow doctor .
policyflow validate ai/workflows/features/first-feature.yml
```

## Default Execution Mode

PolicyFlow defaults to strict workflow execution in every consumer repo:

1. create the workflow file before implementation
2. lock scope, non-goals, and risk before code changes
3. declare an `execution` block with canonical phases and states
4. add machine-readable `evidence` blocks as phases complete
5. add matching machine-readable `contracts` blocks as completed agent-owned phases finish
6. add typed `overrides` only for explicit approved exceptions, surface them in the PR when present, and keep their `review_by` or `expires_on` dates current
7. use `runtime` and `handoffs` to persist the current orchestration state as the workflow advances
8. advance phases only when their prerequisite workflow phases are completed
9. execute `planning`, `architecture-check`, `review`, and `qa` as real workflow phases
10. treat the workflow as the steering artifact for the change, not as retrospective documentation
11. keep same-PR workflow edits limited to same-scope clarifications
12. keep the repo-level runner configuration current if you use external agent execution
13. configure the default `type: command` runner to any provider adapter that implements the PolicyFlow runner contract before `policyflow run-phase`

## First Recommended Checks

- confirm protected areas
- confirm risk classifications
- confirm workflow instance paths
- confirm the initial execution phases and states
- confirm which evidence blocks should exist for the first completed phases
- confirm which role contract blocks should exist for the first completed phases
- confirm whether any typed override is truly needed, and if so which override type applies
- confirm which handoffs require concrete input and output artifact lists
- confirm which phase transitions are currently allowed or blocked
- confirm which workflow evidence blocks must be referenced in the PR body
- confirm which workflow overrides must be referenced in the PR body
- confirm whether any declared override is already `expiring` or `revalidation_required`
- confirm human approval expectations
- confirm which GitHub login must appear in `approved_by` and must produce the real PR approval
- confirm how planning, architecture, review, and QA evidence will be made visible in the PR
- confirm which owner agent and output contract each completed phase must carry
- confirm which CLI orchestration commands should be used to advance the workflow state
- confirm which reporting views should be used to check merge readiness and blocked workflows
- confirm which central runner config should execute canonical phases and where its JSON contract output is written
- confirm that `policyflow.runners.yml` points to a valid `type: command` provider adapter
- confirm the selected provider CLI or hosted-adapter wrapper is installed, authenticated, and ready before agent-owned phase execution
