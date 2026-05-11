# PolicyFlow

PolicyFlow is a reusable governance and workflow framework for agent-assisted software delivery.

It provides policy-as-code style documentation, risk-aware workflow templates, explicit agent handoffs, human approval gates, and GitHub governance patterns that a target project can adopt without building its own process layer from scratch.

## What PolicyFlow Is

- A template repository for agentic SDLC governance
- A set of reusable rules, workflows, prompts, and GitHub intake patterns
- A way to make agent-driven work more reviewable, risk-aware, and auditable

## What PolicyFlow Is Not

- Not a product repository
- Not a runtime orchestration system
- Not a CLI or validator yet
- Not a substitute for target-project architecture, contracts, or domain context

## Why It Exists

Many teams want to use coding agents, review agents, and workflow automation, but they lack a consistent governance layer. PolicyFlow exists to separate reusable process logic from target-project domain logic so teams can adopt agent workflows with less ambiguity and less hidden risk.

## Core Concepts

- Policy-as-code
- Risk-aware workflows
- Confidence governance
- Explicit agent handoffs
- Human-in-the-loop controls
- GitHub governance templates

## Repository Structure

```text
PolicyFlow/
├── docs/
├── rules/
├── agents/
├── workflows/
├── prompts/
├── github/
└── examples/
```

## How To Use It In A Target Project

1. Copy `github/ISSUE_TEMPLATE/*` and `github/PULL_REQUEST_TEMPLATE.md` into the target repo's `.github/`.
2. Copy `rules/`, `agents/`, `workflows/`, and `prompts/` into the target repo's `ai/`.
3. Add `ai/project-context.yml` in the target project using [examples/project-context.yml](examples/project-context.yml) as the starting point.
4. Add target-project overlays such as:
   - `AGENTS.md`
   - `ai/architecture.md`
   - `ai/rules/project-overrides.md`
   - `contracts/` if applicable
5. Create workflow instances for real work under `ai/workflows/features/` or the target project's chosen workflow location.

## Example Installation Approach

- copy `github/` templates into `.github/`
- copy `rules/`, `agents/`, `workflows/`, and `prompts/` into `ai/`
- add `ai/project-context.yml` in the target project

## Current Status

- Template and governance framework
- No runtime agent orchestration yet
- No CLI yet

## Future Roadmap

- Governance validator
- GitHub Action checks
- Prompt renderer
- Workflow generator

## License

See [LICENSE](LICENSE).
