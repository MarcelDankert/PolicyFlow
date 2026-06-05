# Getting Started

## Adopt In A Target Project

Start with a root `policyflow.yml` so bootstrap, doctor, CI, and local commands
can agree on the same Consumer-Repo paths and enabled features.

Bootstrap a fresh Consumer-Repo:

```bash
policyflow init .
```

Preview the generated files without writing them:

```bash
policyflow init . --dry-run
```

PolicyFlow does not overwrite existing files unless explicitly requested:

```bash
policyflow init . --force
```

The bootstrap command writes the standard consumer layout under `ai/`, GitHub
templates and governance workflow under `.github/`, `policyflow.yml`,
`policyflow.runners.yml`, and
`.policyflow/bootstrap.json` metadata for future sync support. It also creates
`ai/workflows/features/starter-workflow.yml` so the first validation path is
available immediately.

Minimal local-only config:

```yaml
version: 1

features:
  pr_validation: false
  github_approval_checks: false
  runner_execution: false
  bootstrap_managed_assets: false
```

GitHub-governed config:

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

Validate the config before wiring deeper governance:

```bash
policyflow config-check policyflow.yml
```

Run preflight checks before the first governed workflow:

```bash
policyflow doctor .
policyflow doctor . --json
```

Doctor checks the Consumer-Repo config, bootstrap artifacts, runner config,
referenced prompt and agent files, project context, and GitHub governance
templates. Missing local PolicyFlow assets fail readiness. External GitHub
tooling is reported separately so local setup gaps are actionable.

The installed GitHub Actions workflow uses read-only `contents` and
`pull-requests` permissions, fetches the live PR body and review metadata with
the built-in `github.token`, and runs `policyflow validate-pr` plus
`policyflow validate-github-approvals` against the workflow referenced in the PR
body.

Published examples are available at `examples/policyflow.minimal.yml` and
`examples/policyflow.github-governed.yml`.

1. Copy `github/ISSUE_TEMPLATE/*` into `.github/ISSUE_TEMPLATE/`.
2. Copy `github/PULL_REQUEST_TEMPLATE.md` into `.github/`.
3. Copy `rules/`, `agents/`, `workflows/`, and `prompts/` into `ai/`.
4. Add `ai/project-context.yml` using the example in `examples/project-context.yml`.
5. Add target-project overlays such as `ai/architecture.md` and `ai/rules/project-overrides.md`.

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
