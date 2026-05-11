# Getting Started

## Adopt In A Target Project

1. Copy `github/ISSUE_TEMPLATE/*` into `.github/ISSUE_TEMPLATE/`.
2. Copy `github/PULL_REQUEST_TEMPLATE.md` into `.github/`.
3. Copy `rules/`, `agents/`, `workflows/`, and `prompts/` into `ai/`.
4. Add `ai/project-context.yml` using the example in `examples/project-context.yml`.
5. Add target-project overlays such as `ai/architecture.md` and `ai/rules/project-overrides.md`.

## First Recommended Checks

- confirm protected areas
- confirm risk classifications
- confirm workflow instance paths
- confirm human approval expectations
