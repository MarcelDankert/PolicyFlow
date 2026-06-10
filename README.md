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
- Not a full orchestration platform
- Not a substitute for target-project architecture, contracts, or domain context

## Why It Exists

Many teams want to use coding agents, review agents, and workflow automation, but they lack a consistent governance layer. PolicyFlow exists to separate reusable process logic from target-project domain logic so teams can adopt agent workflows with less ambiguity and less hidden risk.

## Core Concepts

- Policy-as-code
- Risk-aware workflows
- Workflow execution state
- Phase evidence schema
- Agent role contracts
- Typed workflow overrides
- Runtime workflow orchestration
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

## Repository Agent Guidance

See [AGENTS.md](AGENTS.md) for PolicyFlow repository guidance for Codex and
other coding agents working on this framework.

## How To Use It In A Target Project

1. Copy `github/ISSUE_TEMPLATE/*` and `github/PULL_REQUEST_TEMPLATE.md` into the target repo's `.github/`.
2. Copy `rules/`, `agents/`, `workflows/`, and `prompts/` into the target repo's `ai/`.
3. Add `ai/project-context.yml` in the target project using [examples/project-context.yml](examples/project-context.yml) as the starting point.
4. Add target-project overlays such as:
   - `AGENTS.md`
   - `ai/architecture.md`
   - `ai/rules/project-overrides.md`
   - `contracts/` if applicable
5. Create workflow instances for real work under `ai/workflows/features/` or the target project's chosen workflow location before implementation starts. This is required in every consumer repo.

## Workflow-First Delivery Standard

PolicyFlow treats `workflow-first delivery` as the required default process for all consumer repositories that adopt these templates. The workflow is not retrospective paperwork. It is created first and then used to steer implementation, review, and merge readiness.

Required order for every consumer repo:

1. Create the workflow file first.
2. Lock scope, non-goals, and risk before implementation.
3. Declare the workflow execution state using canonical phases and states.
4. Execute the workflow phases as real work: planning first, then architecture-check as required by risk, then implementation, review, and QA.
5. Record machine-readable role contracts as phases complete so each canonical phase has an explicit owner agent and output contract.
6. Record typed overrides only for explicit approved exceptions, and make them visible in the PR when they exist.
7. Keep the execution state aligned with the current workflow phase, runtime status, and recorded handoffs.
8. Implement inside the declared workflow.
9. Allow small workflow refinements in the same PR when they stay within the same scope and risk posture.
10. Do not silently expand scope, risk, or non-goals.
11. Review the PR body, delivery evidence, declared overrides, and runtime handoffs against the workflow before merge.

Pragmatic-strict transition mode:

- the workflow file is mandatory from the start of the work
- the workflow guides the work from the beginning, not only in the PR write-up
- the workflow declares canonical execution phases with explicit states such as `pending`, `in_progress`, `completed`, and `blocked`
- workflow phases are operational steps, not only descriptive labels
- `planning`, `architecture-check`, `review`, and `qa` should be visible in how the work is executed and evidenced
- completed canonical phases should also carry matching machine-readable role contracts with the expected owner agent
- approved exceptions should be modeled as typed workflow overrides and explicitly confirmed in the PR
- runtime status and handoffs should be persisted as the workflow advances
- small same-scope clarifications in the same PR are allowed
- hidden scope, risk, or non-goal expansion is not allowed
- PolicyFlow documents, templates, and PR checks make the workflow visible and lightly enforceable

## Example Installation Approach

Install a pinned PolicyFlow release in the target project:

```bash
python -m pip install policyflow==0.1.0
```

Then run bootstrap:

```bash
policyflow init .
```

See [docs/release-and-upgrade.md](docs/release-and-upgrade.md) for pinning,
release note, and upgrade guidance.

## Current Status

- Template and governance framework
- Lightweight governance validator
- Workflow execution state schema
- Phase evidence schema
- Transition and gate validator
- PR evidence mapping
- GitHub governance workflow for PolicyFlow itself
- Agent role contract schema for canonical workflow phases
- Typed workflow override schema with PR visibility
- Runtime and handoff orchestration state with CLI mutation support
- Risk-review matrix enforcement
- Approval evidence enforcement for `HIGH` risk
- Protected-area escalation enforcement
- Lightweight runtime workflow orchestration with direct YAML mutation commands

## Validator

PolicyFlow now includes a lightweight governance validator for workflow YAML files.

Consumer install:

```bash
python -m pip install policyflow==0.1.0
```

Developer install from a source checkout:

```bash
python -m pip install -e .[dev]
```

Validate a workflow file:

```bash
policyflow validate workflows/examples/example-feature-workflow.yml
```

Validate a PR body markdown file against a workflow:

```bash
policyflow validate-pr workflows/examples/example-feature-workflow.yml path/to/pull-request.md
```

Validate PR approval logins against GitHub review metadata:

```bash
policyflow validate-github-approvals workflows/examples/example-architecture-change-workflow.yml path/to/pull-request.md path/to/pr-reviews.json
```

Workflow reporting helpers:

```bash
policyflow status workflows/examples/example-feature-workflow.yml
policyflow status workflows/examples/example-feature-workflow.yml --json
policyflow audit workflows/features
policyflow audit workflows/features --json
```

Central runner configuration:

```bash
policyflow run-phase workflows/examples/example-feature-workflow.yml implementation
policyflow run-phase workflows/examples/example-feature-workflow.yml implementation --runner-config policyflow.runners.yml
```

The published `policyflow.runners.yml` uses the packaged Codex wrapper:

```text
python -m policyflow.codex_runner --input <input.json> --output <output.json>
```

The wrapper calls `codex exec` and expects Codex to return a single JSON object as
its final response. Before using `run-phase`, install and authenticate Codex CLI
and verify the local environment with:

```bash
codex doctor
```

In CI, install PolicyFlow and Codex CLI before the governance step, provide the
Codex authentication and configuration expected by your Codex installation, and
run `codex doctor` as a preflight check. If Codex is missing or cannot run,
PolicyFlow blocks the phase with an actionable runtime reason instead of leaving
the workflow in an ambiguous state.

Runner result contract:

- `phase`: must match the requested phase
- `owner_agent`: must match the expected PolicyFlow owner agent
- `status`: `completed` or `blocked`
- `summary`: short result summary
- `blockers`: required when the phase is blocked unless `summary` explains the block
- `evidence_updates`: optional object written into the phase evidence block
- `contract_updates`: optional object written into the phase contract block
- `handoff`: optional object with `to_phase`, `required_inputs`, and `produced_outputs`

Wrapper exit codes:

- `0`: valid PolicyFlow result JSON was written
- `2`: Codex CLI command was not found
- `3`: Codex CLI ran but failed
- `4`: PolicyFlow input/output contract error

Runtime orchestration helpers:

```bash
policyflow next-step workflows/examples/example-feature-workflow.yml
policyflow handoff-status workflows/examples/example-feature-workflow.yml
policyflow start-phase workflows/examples/example-feature-workflow.yml implementation
policyflow complete-phase workflows/examples/example-feature-workflow.yml implementation
policyflow block-phase workflows/examples/example-feature-workflow.yml implementation --reason "runtime contract uncertainty"
policyflow record-handoff workflows/examples/example-feature-workflow.yml --from-phase implementation --to-phase review --required-input implementation_summary --produced-output review_findings
```

Managed asset upgrade helpers:

```bash
policyflow sync .
policyflow sync . --apply
policyflow sync . --apply --force
```

Successful validation prints:

```text
[SUCCESS] Workflow validation passed.
```

Validation failures print a readable error summary and return a non-zero exit code.

Current validator scope:

- requires `workflow` metadata
- requires `context.workflow_file`
- requires `context.risk_level`
- requires `context.confidence` with `planning`, `implementation`, `tests`, and `residual_uncertainty`
- requires `governance.required_reviews`
- requires `execution.mode`
- requires `execution.phases`
- accepts optional `evidence` blocks per workflow phase
- accepts optional `contracts` blocks per canonical workflow phase
- accepts optional typed `overrides` entries for approved exceptions
- accepts optional `runtime` and `handoffs` blocks for lightweight workflow orchestration
- accepts governance fields primarily from `context` + `governance`
- accepts equivalent root-level fields only as a backward-compatible fallback
- allows `LOW`, `MEDIUM`, or `HIGH` risk only
- requires workflow confidence to be explicit before implementation starts and treats PR `Confidence summary` as a summary of `context.confidence`
- requires `governance.required_reviews` to be a non-empty list
- allows execution states `pending`, `in_progress`, `completed`, and `blocked`
- validates canonical evidence blocks when present:
  - `planning`: `summary`, `scope_locked`, `non_goals_locked`, `risk_rationale`
  - `architecture-check`: `decision`, `constraints`, `approval_path`
  - `review`: `outcome`, `findings_summary`, `residual_risk`
  - `qa`: `outcome`, `evidence_summary`, `unresolved_risks`
  - `approval`: `approved_by`, `reference`, `scope_confirmed`
- validates canonical role contracts when present:
  - `planning`: `owner_agent`, `issue_brief`, `acceptance_criteria`, `approved_scope`, `non_goals`, `initial_risk_level`, `protected_areas_touched`, `confidence_summary`, `escalation_flags`
  - `architecture-check`: `owner_agent`, `architecture_assessment`, `approved_scope`, `module_boundaries`, `contract_impact`, `risk_review_decision`, `required_reviews`, `implementation_constraints`
  - `implementation`: `owner_agent`, `implementation_summary`, `changed_files`, `test_summary`, `docs_updates`, `known_limitations`, `unresolved_questions`
  - `review`: `owner_agent`, `review_findings`, `required_fixes`, `severity`, `approval_status`, `review_approval`, `residual_risk`, `qa_focus_areas`, `test_expectations`
  - `qa`: `owner_agent`, `qa_report`, `quality_gate_status`, `unresolved_risks`, `approval_required`, `merge_readiness`
- validates typed overrides when present:
  - shared fields: `id`, `type`, `reason`, `scope_impact`, `risk_impact`, `mitigations`, `approved_by`, `approval_reference`, exactly one of `review_by` or `expires_on`
  - `scope_exception`: `affected_scope_items`
  - `risk_exception`: `original_risk`, `effective_risk`
  - `phase_bypass`: `bypassed_phase`, `compensating_controls`
  - `approval_bypass`: `approval_target`, `compensating_controls`
  - `non_goal_exception`: `affected_non_goals`
  - override lifecycle: `active` until the declared review/expiry window closes, `expiring` during the last 7 days before it closes, `revalidation_required` after it has passed
- validates runtime orchestration when present:
  - `runtime.status`: `idle`, `in_progress`, `handoff_pending`, `blocked`, `completed`
  - `runtime.current_phase`, `runtime.active_agent`, `runtime.last_transition`, `runtime.block_reason`
  - `handoffs`: `from_phase`, `to_phase`, `status`, `required_inputs`, `produced_outputs`, `blockers`, `override_refs`
- enforces the first execution transition gates:
  - `implementation` cannot start before `planning` is completed
  - `MEDIUM`/`HIGH` implementation cannot start before `architecture-check` is completed
  - `review` cannot start before `implementation` is completed
  - `qa` cannot start before `review` is completed
  - `approval` cannot start before `qa` is completed
- requires matching evidence blocks for completed evidence-bearing phases
- requires matching role contract blocks for completed canonical agent-owned phases
- requires approval metadata for `risk_exception` and `approval_bypass`
- emits non-blocking warnings for `expiring` overrides and blocks workflows that reach `revalidation_required`
- requires PR-visible override references for declared workflow overrides
- requires runtime `handoff_pending` states to point to an open pending handoff
- blocks handoffs that still reference overrides requiring revalidation
- requires concrete handoff input and output artifact lists
- requires canonical execution phases by risk:
  - `LOW`: `planning`, `implementation`, `review`
  - `MEDIUM`: `planning`, `architecture-check`, `implementation`, `review`, `qa`
  - `HIGH`: `planning`, `architecture-check`, `implementation`, `review`, `qa`, `approval`
- enforces minimum `required_reviews` from `rules/risk-review-matrix.md`
- requires `governance.human_approval_required: true` for `HIGH` risk workflows
- requires non-empty `governance.approval_evidence` for `HIGH` risk workflows
- requires workflows that touch protected areas to:
  - use `HIGH` risk
  - set `governance.escalation_required: true`
- treats `governance.protected_areas_touched: [none]` as an explicit no-protected-area case
- validates PR body markdown files against the existing PR template with:
  - a non-empty `Linked Issue` section
  - a `Workflow File` entry matching `context.workflow_file`
  - a `Declared risk level` entry matching `context.risk_level`
  - a `Human approval login if required` entry matching `evidence.approval.approved_by` for approval-gated workflows
  - override `Approved by login` entries matching workflow `approved_by` logins when present
  - evidence references that point to existing workflow evidence blocks
  - override references that point to existing typed workflow overrides
  - a checked confirmation that the linked workflow governed the change
  - a checked confirmation that the workflow governed the work from the start, not only as a retrospective reference
  - a checked confirmation that scope, non-goals, and risk were fixed in the workflow before implementation started
  - a checked confirmation that required workflow phases were executed as visible working steps, not only documented after the fact
- validates GitHub PR review metadata against workflow approval claims by requiring `APPROVED` reviews from the declared `approved_by` logins
- exposes workflow reporting views for a single workflow (`status`) and a directory tree (`audit`) with optional JSON output
- supports synchronous external agent execution for canonical agent-owned phases through a central runner config and JSON result contract
- supports dry-run and explicit-apply sync for PolicyFlow-managed Consumer-Repo assets

This runtime layer is intentionally small. It mutates only controlled workflow fields and does not execute agents, schedule work, or orchestrate GitHub runs directly.

PolicyFlow now acts as a lightweight workflow orchestration layer as well as a governance validator, but it is still not a full orchestration platform, scheduler, or agent runtime.

TODO:
- Normalize the workflow schema into a single canonical governance block in a future PR after real usage validates the current field layout.

## Future Roadmap

- workflow schema normalization after more consumer usage
- release publishing automation after packaged release checks are proven
- additional consumer validation beyond AurumEdge once more repos adopt the workflow
- GitHub API-based PR validation as a later target state after the local markdown flow is proven in real usage

## License

See [LICENSE](LICENSE).
