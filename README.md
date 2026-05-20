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
5. Create workflow instances for real work under `ai/workflows/features/` or the target project's chosen workflow location before implementation starts. This is required in every consumer repo.

## Workflow-First Delivery Standard

PolicyFlow treats `workflow-first delivery` as the required default process for all consumer repositories that adopt these templates. The workflow is not retrospective paperwork. It is created first and then used to steer implementation, review, and merge readiness.

Required order for every consumer repo:

1. Create the workflow file first.
2. Lock scope, non-goals, and risk before implementation.
3. Declare the workflow execution state using canonical phases and states.
4. Execute the workflow phases as real work: planning first, then architecture-check as required by risk, then implementation, review, and QA.
5. Record machine-readable role contracts as phases complete so each canonical phase has an explicit owner agent and output contract.
6. Keep the execution state aligned with the current workflow phase.
7. Implement inside the declared workflow.
8. Allow small workflow refinements in the same PR when they stay within the same scope and risk posture.
9. Do not silently expand scope, risk, or non-goals.
10. Review the PR body and delivery evidence against the workflow before merge.

Pragmatic-strict transition mode:

- the workflow file is mandatory from the start of the work
- the workflow guides the work from the beginning, not only in the PR write-up
- the workflow declares canonical execution phases with explicit states such as `pending`, `in_progress`, `completed`, and `blocked`
- workflow phases are operational steps, not only descriptive labels
- `planning`, `architecture-check`, `review`, and `qa` should be visible in how the work is executed and evidenced
- completed canonical phases should also carry matching machine-readable role contracts with the expected owner agent
- small same-scope clarifications in the same PR are allowed
- hidden scope, risk, or non-goal expansion is not allowed
- PolicyFlow documents, templates, and PR checks make the workflow visible and lightly enforceable

## Example Installation Approach

- copy `github/` templates into `.github/`
- copy `rules/`, `agents/`, `workflows/`, and `prompts/` into `ai/`
- add `ai/project-context.yml` in the target project

## Current Status

- Template and governance framework
- Lightweight governance validator
- Workflow execution state schema
- Phase evidence schema
- Transition and gate validator
- PR evidence mapping
- GitHub governance workflow for PolicyFlow itself
- Agent role contract schema for canonical workflow phases
- Risk-review matrix enforcement
- Approval evidence enforcement for `HIGH` risk
- Protected-area escalation enforcement
- No runtime agent orchestration

## Validator

PolicyFlow now includes a lightweight governance validator for workflow YAML files.

Install locally:

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

Successful validation prints:

```text
[SUCCESS] Workflow validation passed.
```

Validation failures print a readable error summary and return a non-zero exit code.

Current validator scope:

- requires `workflow` metadata
- requires `context.workflow_file`
- requires `context.risk_level`
- requires `governance.required_reviews`
- requires `execution.mode`
- requires `execution.phases`
- accepts optional `evidence` blocks per workflow phase
- accepts optional `contracts` blocks per canonical workflow phase
- accepts governance fields primarily from `context` + `governance`
- accepts equivalent root-level fields only as a backward-compatible fallback
- allows `LOW`, `MEDIUM`, or `HIGH` risk only
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
- enforces the first execution transition gates:
  - `implementation` cannot start before `planning` is completed
  - `MEDIUM`/`HIGH` implementation cannot start before `architecture-check` is completed
  - `review` cannot start before `implementation` is completed
  - `qa` cannot start before `review` is completed
  - `approval` cannot start before `qa` is completed
- requires matching evidence blocks for completed evidence-bearing phases
- requires matching role contract blocks for completed canonical agent-owned phases
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
  - evidence references that point to existing workflow evidence blocks
  - a checked confirmation that the linked workflow governed the change
  - a checked confirmation that the workflow governed the work from the start, not only as a retrospective reference
  - a checked confirmation that scope, non-goals, and risk were fixed in the workflow before implementation started
  - a checked confirmation that required workflow phases were executed as visible working steps, not only documented after the fact

This is intentionally a lightweight governance validator, not a workflow engine, orchestration runtime, or GitHub integration layer. The new role contracts make phase ownership and outputs machine-checkable without introducing a runtime scheduler.

TODO:
- Normalize the workflow schema into a single canonical governance block in a future PR after real usage validates the current field layout.

## Future Roadmap

- workflow schema normalization after more consumer usage
- packaged releases instead of `git+https` installation from `main`
- additional consumer validation beyond AurumEdge once more repos adopt the workflow
- GitHub API-based PR validation as a later target state after the local markdown flow is proven in real usage

## License

See [LICENSE](LICENSE).
