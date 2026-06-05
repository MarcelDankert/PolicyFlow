# Getting Started

## Adopt In A Target Project

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
13. when using the default Codex runner, verify `codex doctor` before `policyflow run-phase`

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
- confirm that `policyflow.runners.yml` points to `python -m policyflow.codex_runner` or another valid command
- confirm Codex CLI is installed, authenticated, and passes `codex doctor` before agent-owned phase execution
