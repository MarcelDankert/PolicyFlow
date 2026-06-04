# PolicyFlow Agent Guidance

## Purpose

PolicyFlow governs AI-assisted software delivery with reusable workflow, risk,
handoff, approval, runner, and GitHub governance assets that Consumer-Repos can
adopt without rebuilding their own process layer.

## Core Rules

- Treat PolicyFlow changes as governed work, not informal repo maintenance.
- Create or update the active workflow before implementation starts.
- Keep scope, non-goals, risk, evidence, and PR claims aligned.
- Do not silently change consumer-facing contracts, schemas, templates, runner
  behavior, or GitHub governance expectations.
- Escalate before changing validator semantics, release compatibility, runner
  contracts, bootstrap behavior, or approval rules.
- Record blocked checks or unresolved productization gaps instead of guessing.

## Repository Identity

All AI-generated GitHub interactions must use the Sentinel-Flow GitHub App
identity.

AI agents must:
- create branches for repository changes
- create pull requests for reviewable work
- use a Sentinel-Flow GitHub App installation token for GitHub operations

AI agents must not:
- merge protected branches
- approve pull requests
- bypass PolicyFlow governance checks

Use the locally configured Sentinel-Flow token helper or secret store for GitHub
CLI operations when acting as Sentinel-Flow. Do not commit machine-local paths,
private-key locations, or token material to this public repository.

## Workflow-First Delivery

Use a workflow under `workflows/features/` as the source of truth for every
PolicyFlow issue implementation.

Risk guidance:
- LOW: bounded docs, examples, or metadata changes without consumer contract
  impact.
- MEDIUM: templates, bootstrap, doctor, config, CI, runner wiring, or docs that
  alter the consumer setup path.
- HIGH: breaking schema behavior, approval semantics, runner contract changes,
  release/upgrade compatibility breaks, or protected governance behavior.

Each workflow should lock:
- issue link and goal
- scope and non-goals
- risk level and rationale
- required phases and reviews
- evidence and role contracts for completed phases

## Framework Asset Boundaries

These directories are PolicyFlow framework assets intended to be copied,
packaged, or bootstrapped into Consumer-Repos:
- `agents/`
- `prompts/`
- `rules/`
- `workflows/`
- `github/`
- `examples/`

Do not treat those files as local-only documentation. Changes can affect
consumer bootstrap, validation, onboarding, and upgrade behavior.

When changing consumer-facing assets, update the matching docs, examples,
fixtures, tests, and workflow evidence in the same PR when they are part of the
same contract.

## Required Validation

Use the narrowest relevant command first, then run the broader governance checks
before completion.

Common checks:

```powershell
pytest -q
policyflow validate workflows/features/<workflow>.yml
policyflow validate workflows/examples/example-feature-workflow.yml
policyflow validate workflows/examples/example-bugfix-workflow.yml
policyflow validate workflows/examples/example-architecture-change-workflow.yml
```

For validator, runtime, runner, PR, or GitHub approval changes, include the
targeted test module and then the full suite:

```powershell
pytest -q tests/test_validator.py tests/test_pr_validator.py tests/test_runtime_cli.py tests/test_github_approval.py
pytest -q
```

For docs-only changes, run the relevant documentation tests and validate the
active workflow.

## Delivery Expectations

- Keep README, docs, templates, fixtures, and examples consistent with CLI and
  validator behavior.
- Prefer explicit consumer defaults over hidden tribal knowledge.
- Preserve backward compatibility unless the active workflow and issue call out
  the breaking change.
- Make productization changes testable through bootstrap, doctor, packaging, or
  golden Consumer-Repo paths where applicable.
- Keep PR bodies tied to the active workflow, evidence, overrides, and approval
  state.
