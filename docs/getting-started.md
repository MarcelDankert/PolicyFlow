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
6. add typed `overrides` only for explicit approved exceptions, and surface them in the PR when present
7. advance phases only when their prerequisite workflow phases are completed
8. execute `planning`, `architecture-check`, `review`, and `qa` as real workflow phases
9. treat the workflow as the steering artifact for the change, not as retrospective documentation
10. keep same-PR workflow edits limited to same-scope clarifications

## First Recommended Checks

- confirm protected areas
- confirm risk classifications
- confirm workflow instance paths
- confirm the initial execution phases and states
- confirm which evidence blocks should exist for the first completed phases
- confirm which role contract blocks should exist for the first completed phases
- confirm whether any typed override is truly needed, and if so which override type applies
- confirm which phase transitions are currently allowed or blocked
- confirm which workflow evidence blocks must be referenced in the PR body
- confirm which workflow overrides must be referenced in the PR body
- confirm human approval expectations
- confirm how planning, architecture, review, and QA evidence will be made visible in the PR
- confirm which owner agent and output contract each completed phase must carry
