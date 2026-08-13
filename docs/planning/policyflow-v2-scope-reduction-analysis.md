# PolicyFlow 2.0 Scope-Reduction Analysis

## 1. Executive Summary

PolicyFlow has crossed the boundary from governance into runtime and orchestration-adjacent behavior. The strongest evidence is not only naming: `policyflow.agent_execution` launches external runners, `policyflow.codex_runner` shells out to Codex, `policyflow.runtime` mutates phase and handoff state, the public API exports runtime mutation helpers, bootstrap installs `policyflow.runners.yml`, and the README presents PolicyFlow as a "lightweight workflow orchestration framework."

ADR-0002 remains the correct architectural constraint. It allows controlled governance state and external evidence ingestion, but it explicitly rejects hosted agents, independent orchestration, memory, message routing, provider credentials, and provider-specific execution. PolicyFlow 2.0 should therefore be smaller than 1.0.0: a provider-neutral governance validator with PR/GitHub approval checks, human approval and override governance, simple evidence validation, and a small read-only compliance report.

Recommended V2 direction:

- Keep validation, schemas/models, PR validation, GitHub approval evidence checks, exceptions, and a minimal public API.
- Simplify bootstrap, doctor, reporting, consumer config, CLI, workflow templates, and schema shape.
- Move runner execution, Codex adapter, agent/prompt execution assets, phase mutation commands, first-class agent handoffs, and QueryPilot/product-specific examples outside PolicyFlow core.
- Remove duplicated packaged asset mirrors where possible by creating one asset source of truth.
- Cut the target CLI to `init`, `validate`, `validate-pr`, and `doctor`, with any additional read-only reporting gated by clear governance value.

Consumer usability is currently below the target. A fresh user must understand runner configs, managed assets, prompt/agent folders, workflow phases, contracts, handoffs, runtime state, evaluation reports, loop reports, PR body metadata, GitHub approval JSON, and sync semantics. That is not a less-than-ten-minute integration path.

## 2. Current Architecture

### Repository Intent and Constraints

Source-of-truth documents reviewed:

- `README.md`
- `pyproject.toml`
- `docs/adr/0001-strategic-direction-agentic-governance.md`
- `docs/adr/0002-policyflow-is-not-an-agent-runtime.md`
- `docs/adr/0003-loop-and-evaluation-governance.md`
- `docs/public-api.md`
- `docs/getting-started.md`
- `AGENTS.md`

The intended product boundary is clear in ADR-0002: PolicyFlow may define governance rules, validate workflow, loop, evaluation, human approval, and PR governance claims, report compliance, persist controlled governance state, and accept provider-neutral evidence from external systems. It must not own agent hosting, scheduling, independent orchestration, message routing, memory, provider credentials, provider SDK integrations, or merge decisions.

### Python Package Shape

Current modules:

- `policyflow/__init__.py` re-exports public API symbols, including runtime mutation helpers.
- `policyflow/api.py` exposes validation, PR validation, GitHub approval, reporting, audit, and runtime mutation wrappers.
- `policyflow/models.py` defines Pydantic models for workflow metadata, context, governance, execution phases, evidence, role contracts, overrides, runtime status, handoffs, loop governance, and evaluation governance.
- `policyflow/schemas.py` normalizes legacy root-level fields into canonical context/governance/execution fields.
- `policyflow/validator.py` validates workflow structure, risk rules, required phases, evidence, contracts, overrides, runtime/handoff consistency, loop governance, evaluation governance, and PR body content.
- `policyflow/github_approval.py` validates workflow approval claims against GitHub review JSON.
- `policyflow/reporting.py` builds workflow status, audit JSON, evaluation reports, and loop reports.
- `policyflow/bootstrap.py` scaffolds consumer assets, including runner config, agents, prompts, rules, workflow templates, GitHub templates, GitHub Actions workflow, starter workflow, and managed-asset metadata.
- `policyflow/sync.py` previews/applies managed asset updates using bootstrap metadata.
- `policyflow/doctor.py` checks consumer config, bootstrap artifacts, runner config and runner commands, project context, GitHub templates, GitHub CLI, and GitHub App permissions.
- `policyflow/workflow_generator.py` creates workflow instances with phases, evidence, contracts, runtime, and handoffs.
- `policyflow/runtime.py` reads/writes workflow YAML, mutates phases, mutates runtime state, and records handoffs.
- `policyflow/agent_execution.py` runs external commands for agent-owned phases, builds input JSON, reads prompt/agent assets, applies result JSON, blocks phases on failure, and records handoffs.
- `policyflow/codex_runner.py` is a Codex CLI adapter.
- `policyflow/consumer_config.py` validates `policyflow.yml`.
- `policyflow/exceptions.py` defines validation errors.

### CLI Surface

Current CLI commands:

- Governance validation: `validate`, `validate-pr`, `validate-github-approvals`
- Consumer setup: `init`, `config-check`, `doctor`, `sync`
- Workflow creation: `new-workflow`
- Reporting: `status`, `audit`, `evaluation-report`, `loop-report`
- Runtime/execution: `run-phase`, `next-step`, `handoff-status`, `start-phase`, `complete-phase`, `block-phase`, `record-handoff`

This is a broad surface for a governance product. The runtime and setup commands dominate the adoption story more than policy validation.

### Packaged Assets

`pyproject.toml` packages mirrored assets from `policyflow/assets/`:

- `agents/*.md`
- `prompts/*.md`
- `rules/*.md`
- `workflows/templates/*.yml`
- `github/*.md`
- `github/ISSUE_TEMPLATE/*.yml`
- `github/workflows/*.yml`
- `examples/*.yml`
- `docs/*.md`

The repository also has top-level copies under `agents/`, `prompts/`, `rules/`, `workflows/templates/`, `github/`, `examples/`, and `docs/`. Several are identical, several differ.

## 3. Scope Drift Findings

### Runtime and Orchestration Boundary

PolicyFlow has crossed into runtime/orchestration-adjacent responsibilities.

Evidence:

- `policyflow/agent_execution.py` executes configured commands with `subprocess.run`.
- `policyflow/codex_runner.py` shells out to `codex exec`.
- `policyflow/runtime.py` mutates `execution.phases`, `runtime`, and `handoffs`.
- `policyflow/api.py` and `policyflow/__init__.py` expose runtime mutation as stable public API.
- `policyflow/cli.py` includes `run-phase`, `start-phase`, `complete-phase`, `block-phase`, `record-handoff`, `next-step`, and `handoff-status`.
- `policyflow/bootstrap.py` installs `policyflow.runners.yml` by default.
- `docs/getting-started.md` makes runner setup part of the first consumer path.
- `README.md` describes PolicyFlow as a "lightweight workflow orchestration framework."

This does not make PolicyFlow a full runtime, but it creates product pressure in exactly the direction ADR-0002 warns about.

### Consumer Footprint Drift

The current `policyflow init` output is large:

- `policyflow.yml`
- `policyflow.runners.yml`
- `.policyflow/bootstrap.json`
- `ai/project-context.yml`
- `ai/agents/`
- `ai/prompts/`
- `ai/rules/`
- `ai/workflows/templates/`
- `ai/workflows/features/starter-workflow.yml`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `.github/ISSUE_TEMPLATE/`
- `.github/workflows/policyflow-governance.yml`

For V2, this is too much for a ten-minute adoption goal. It teaches users about agent execution, prompts, managed assets, and workflow lifecycle state before they understand the governance contract.

### Schema Drift

The current `WorkflowDocument` contains governance and runtime concepts in one object:

- Governance: `workflow`, `context`, `governance`, `evidence`, `overrides`, PR validation fields.
- Execution lifecycle: `execution.phases`, phase states, transition gates.
- Agent execution concepts: `contracts.owner_agent`, `runtime.active_agent`, prompt/agent paths.
- Orchestration concepts: `runtime.status`, `runtime.current_phase`, `handoffs`.
- Evaluation/metrics: categories, required metrics, thresholds, actual values, blocking metrics.
- Loop state: current iterations, loop statuses, escalation and stop evidence.

Some of this is legitimate declarative governance. Some is runtime behavior and analytics.

### Documentation Drift

Docs repeatedly say PolicyFlow is not a runtime while also documenting runner execution, runtime orchestration helpers, active agents, handoffs, sync, and report variants. New users encounter contradictory framing: "not a runtime" and "run agent-owned phases" in the same quickstart path.

## 4. KEEP / SIMPLIFY / MOVE / REMOVE Matrix

| Subsystem | Paths | Current Responsibility | Dependencies | Classification | Reason | Migration Impact | Breaking-Change Risk |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Core validation | `policyflow/validator.py`, `policyflow/models.py`, `policyflow/schemas.py`, `policyflow/exceptions.py`, `tests/test_validator.py` | Validate workflow schema, risk, reviews, evidence, overrides, phases, loop/evaluation, PR bodies | Pydantic, PyYAML, exceptions, models | SIMPLIFY | Core belongs in PolicyFlow, but validator has absorbed runtime, phase, loop, metric, and PR parser complexity | V2 schema rewrite; fixtures and tests need major pruning | HIGH |
| Public API | `policyflow/api.py`, `policyflow/__init__.py`, `docs/public-api.md`, `tests/test_public_api.py` | Stable imports for validation, reporting, GitHub approval, runtime mutation | validator, reporting, runtime, GitHub approval | SIMPLIFY | Keep validation API, remove runtime mutation from stable API, reconsider audit API version | Consumers importing runtime helpers break | HIGH |
| PR validation | `policyflow/validator.py`, `github/PULL_REQUEST_TEMPLATE.md`, `policyflow/assets/github/PULL_REQUEST_TEMPLATE.md`, `tests/test_pr_validator.py` | Validate PR body claims against workflow file | validator, models, markdown parsing | KEEP | Direct governance enforcement with clear consumer value | Template fields must align to V2 schema | MEDIUM |
| GitHub approval checks | `policyflow/github_approval.py`, `github/workflows/policyflow-governance.yml`, `tests/test_github_approval.py`, `tests/test_consumer_github_workflow.py` | Validate named approvers against GitHub review JSON | validate-pr, JSON review metadata | KEEP | Human approval evidence and PR review enforcement are governance | Keep command or fold into `validate-pr --github-reviews` later | MEDIUM |
| Runtime phase mutation | `policyflow/runtime.py`, runtime CLI commands, `tests/test_runtime_cli.py` | Mutate workflow phases, runtime status, and handoffs | validator, PyYAML | MOVE | Useful for external runtimes, but active phase control is orchestration-adjacent | Remove public API/CLI; external runtimes can emit evidence/state files | HIGH |
| Runtime declarative state | `runtime` block in models/templates/fixtures | Persist status, current phase, active agent, last transition, block reason | models, validator, reporting | SIMPLIFY | `blocked_reason`/compliance state can be governance evidence; active agent/current phase are orchestration | Replace with optional read-only `state`/`evidence` summary | HIGH |
| Handoffs | `handoffs` blocks, `rules/agent-handoff-contracts.md`, templates, tests | Model source/target phase handoffs and required artifacts | models, validator, runtime | MOVE | Artifact references are evidence; first-class handoff state and status are workflow engine concepts | Convert to evidence references or external runtime evidence | HIGH |
| Agent role contracts | `contracts` models, `agents/`, `prompts/`, templates, tests | Require phase owner agents and detailed outputs | models, validator, bootstrap, agent execution | MOVE | Role expectations can exist as external evidence contracts; PolicyFlow should not own agent execution roles | Breaks existing schemas/templates but reduces complexity sharply | HIGH |
| Runner execution | `policyflow/agent_execution.py`, `policyflow.runners.yml`, runner docs, `tests/test_runtime_cli.py` | Run external command adapters and apply results | runtime, subprocess, YAML, prompt/agent assets | MOVE | Directly owns execution dispatch; belongs in Sentinel-AI-Core or consumer tooling | Remove `run-phase`; keep evidence contract docs if useful | HIGH |
| Codex adapter | `policyflow/codex_runner.py`, tests, docs | Provider-specific wrapper for Codex CLI | subprocess, Codex CLI | MOVE | Provider-specific integration conflicts with provider-neutral core | Publish as external adapter or example outside core | MEDIUM |
| Bootstrap | `policyflow/bootstrap.py`, `policyflow/assets/**`, `tests/test_bootstrap.py` | Scaffold full consumer layout and managed assets | package assets, JSON metadata, YAML | SIMPLIFY | `init` belongs, but output is too large and runtime-oriented | V2 init changes generated files | HIGH |
| Asset sync | `policyflow/sync.py`, `.policyflow/bootstrap.json`, `tests/test_asset_sync.py` | Manage upgrades of bootstrapped assets | bootstrap assets, hashes | REMOVE | Managed asset fleet upgrade is productization overhead for a small governance validator | Consumers lose `policyflow sync`; release notes can provide manual migration | MEDIUM |
| Consumer config | `policyflow/consumer_config.py`, examples, tests | Configure paths and feature toggles, including runner execution | Pydantic, YAML | SIMPLIFY | Keep path config; remove runner/prompt/agent/sync feature toggles | V2 `policyflow.yml` becomes smaller | MEDIUM |
| Doctor | `policyflow/doctor.py`, `tests/test_doctor.py` | Check Python, config, bootstrap, runner commands, assets, GitHub CLI/App permissions | consumer config, subprocess, gh | SIMPLIFY | Keep readiness checks for validator/config/GitHub governance; remove runner checks and mutation capability preflight | Fewer checks; less setup burden | MEDIUM |
| Workflow generator | `policyflow/workflow_generator.py`, tests | Generate detailed workflow instances with phases/evidence/contracts/runtime | config, validator, YAML | MOVE | Helpful scaffold, but not in minimal CLI; could become an external template helper | Remove `new-workflow` or replace with `init --starter` sample | MEDIUM |
| Reporting | `policyflow/reporting.py`, docs/audit-reporting.md, tests | Status, audit, evaluation report, loop report | validator, runtime raw load | SIMPLIFY | Read-only compliance reporting is useful, but report variants and analytics-like summaries exceed minimal core | Keep optional `audit` library function or `validate --json`; remove separate CLI reports unless justified | MEDIUM |
| Evaluation governance | `evaluation` models, validator checks, docs, examples, tests | Declare metrics, thresholds, actual values, compliance status | models, validator, reporting | SIMPLIFY | Required quality evidence belongs; threshold evaluation and metric rollups lean analytics | Keep evidence refs and required gates; move metric computation/analytics out | HIGH |
| Loop governance | `loop_governance` models, validator checks, docs, examples, tests | Declare feedback loops, iterations, stop/escalation conditions | models, validator, reporting | SIMPLIFY | Stop/escalation rules are governance; current iteration/status tracking is runtime loop state | Keep only declarative guardrails and evidence refs if material | HIGH |
| GitHub templates/actions | `github/**`, `policyflow/assets/github/**`, `.github/**`, tests | PR and issue templates, governance workflow | validator CLI, GitHub Actions | KEEP | GitHub governance checks are core when kept read-only | V2 template/schema rewrite | MEDIUM |
| Rules assets | `rules/**`, `policyflow/assets/rules/**` | Risk/review/escalation/confidence/QA/handoff rules | bootstrap assets/docs | SIMPLIFY | Risk/review/escalation rules belong; QA/handoff/agent rules should shrink | Consumers get fewer files | MEDIUM |
| Agents and prompts | `agents/**`, `prompts/**`, packaged copies | Role definitions and prompt templates for agents | bootstrap, runner | MOVE | These are execution-layer assets, not governance core | External runtime or consumer repo owns them | MEDIUM |
| Docs | `docs/**`, `policyflow/assets/docs/**`, README | Product docs, ADRs, guides, migration, reporting | tests, packaged assets | SIMPLIFY | Docs must describe smaller product and remove runtime-first onboarding | Large docs rewrite | MEDIUM |
| Reference consumer | `examples/reference-consumer/**` | Demonstrate current full consumer setup including runner config | bootstrap, doctor, validation | SIMPLIFY | Keep one minimal governance reference; remove runner/provider setup | Golden smoke tests change | MEDIUM |
| QueryPilot docs/examples | `docs/querypilot-pilot.md`, `workflows/examples/querypilot-pilot-workflow.yml` | Product-specific pilot governance example | docs/tests | MOVE | Useful as external consumer example, not PolicyFlow core | Move to external repo or non-packaged case study | LOW |
| Release/package metadata | `pyproject.toml`, `tests/test_release_packaging.py` | Package metadata and asset data | setuptools | SIMPLIFY | Keep package; shrink package data to V2 assets | Packaging tests change | MEDIUM |
| Historical workflows | `workflows/features/*.yml` | Repo governance evidence for prior work | validator | REMOVE | Many completed/old planning workflows clutter the framework asset tree; keep current active or archive outside packaged/adoption path | If still validated in CI, update docs/tests | LOW |

## 5. Proposed PolicyFlow 2.0 Responsibility Boundary

PolicyFlow 2.0 should own:

- Risk classification.
- Governance schema validation.
- Human approval requirements and evidence.
- Required review rules.
- Workflow/change schema.
- Evidence reference validation.
- Override/exception governance.
- PR body governance validation.
- GitHub approval metadata validation.
- Minimal consumer bootstrap for governance files.
- Minimal doctor checks for config/schema/GitHub governance readiness.
- Small read-only compliance output where it helps humans and CI.

PolicyFlow 2.0 should not own:

- Agent execution.
- Agent orchestration.
- Codex/Copilot/provider integrations.
- Model/provider execution or routing.
- Advisor execution.
- Scheduling.
- Long-running runtime state.
- Memory.
- Message routing.
- Productivity/engineering analytics.
- PO-agent execution.
- Managed asset fleet sync unless a very small source-of-truth model proves necessary.

External runtimes should produce structured evidence. PolicyFlow should validate that evidence against governance rules.

## 6. Proposed V2 Module Structure

The suggested target is feasible with small adjustments:

```text
policyflow/
    __init__.py
    api.py
    models.py
    schemas.py
    validator.py
    github_approval.py
    reporting.py
    exceptions.py
    cli.py
```

Recommended module stance:

- Keep `exceptions.py`.
- Keep `models.py`, but replace current `WorkflowDocument` with a smaller V2 governance document.
- Keep `schemas.py`, but use it for V2 parsing and explicit V1 compatibility/migration diagnostics, not indefinite root fallback.
- Keep `validator.py`, but split internally or prune to governance-only checks.
- Keep `github_approval.py`.
- Keep `reporting.py` only if it remains read-only and small. Prefer one audit/status payload rather than separate loop/evaluation report CLIs.
- Keep `cli.py`, but shrink commands.
- Keep `api.py` and `__init__.py`, but remove runtime mutation exports.

Modules that should not remain in V2 core:

- `agent_execution.py`: MOVE.
- `codex_runner.py`: MOVE.
- `runtime.py`: MOVE or reduce to read-only helper functions inside validator/reporting. Do not keep phase mutation APIs.
- `bootstrap.py`: SIMPLIFY, not remove.
- `sync.py`: REMOVE from core.
- `doctor.py`: SIMPLIFY.
- `workflow_generator.py`: MOVE or remove from minimal CLI.
- `consumer_config.py`: either SIMPLIFY or fold into `models.py`/`schemas.py`.

## 7. Proposed V2 CLI Surface

Target CLI:

```text
policyflow init
policyflow validate
policyflow validate-pr
policyflow doctor
```

Recommended command decisions:

- `init`: KEEP/SIMPLIFY. Generate minimal governance config and optional GitHub PR governance files.
- `validate`: KEEP. Validate workflow/change governance files. Add `--json` if CI needs machine-readable output.
- `validate-pr`: KEEP. Validate PR body against workflow/change file. Consider an option for GitHub review JSON if that avoids a separate command.
- `doctor`: KEEP/SIMPLIFY. Check config, schema files, PR template/GitHub workflow when enabled, and version.

Commands to remove or move:

- `run-phase`: MOVE to external runtime.
- `start-phase`, `complete-phase`, `block-phase`, `record-handoff`: MOVE to external runtime or replace with external evidence ingestion.
- `next-step`, `handoff-status`: MOVE or remove.
- `new-workflow`: MOVE unless V2 proves that one starter generator materially improves adoption.
- `sync`: REMOVE.
- `config-check`: FOLD into `doctor` or `validate policyflow.yml`.
- `status`, `audit`, `evaluation-report`, `loop-report`: challenge. Keep only if implemented as a single small read-only report path; otherwise remove from CLI and expose as JSON from `validate`.
- `validate-github-approvals`: KEEP as governance, but consider folding into `validate-pr --reviews pr-reviews.json --allow-pending`.

## 8. Proposed V2 Consumer Footprint

Minimum viable `policyflow init` output:

```text
policyflow.yml
ai/policyflow/workflows/starter.yml
.github/PULL_REQUEST_TEMPLATE.md        # only when GitHub governance enabled
.github/workflows/policyflow.yml        # only when GitHub governance enabled
```

Optional, not default:

- `ai/policyflow/rules/risk-classification.md`
- `ai/policyflow/rules/risk-review-matrix.md`
- `ai/policyflow/examples/`

Remove from default init:

- `policyflow.runners.yml`
- `ai/agents/`
- `ai/prompts/`
- large workflow template tree
- issue templates unless the user opts into GitHub issue intake governance
- `.policyflow/bootstrap.json` unless managed assets survive
- starter workflow with runtime/handoff state

V2 `policyflow.yml` should declare only:

```yaml
version: 2
paths:
  workflows: ai/policyflow/workflows
  pr_template: .github/PULL_REQUEST_TEMPLATE.md
  governance_workflow: .github/workflows/policyflow.yml
features:
  pr_validation: true
  github_approval_checks: true
```

## 9. Proposed Schema Reduction

The proposed V2 schema direction is sound and should be made more explicit:

```yaml
version: 2

change:
  id: ...
  type: feature | bugfix | architecture_change | docs | maintenance

risk:
  level: low | medium | high
  protected_areas: []

governance:
  required_reviews: []
  human_approval_required: false

confidence:
  level: low | medium | high
  summary: ...

evidence:
  planning: []
  implementation: []
  review: []
  qa: []
  approval: []

override:
  id: ...
  type: ...
  reason: ...
  approved_by: ...
  review_by: ...
```

Recommended changes:

- Use lowercase enum values in V2 for readability, with V1 migration diagnostics.
- Replace nested `context` with `change`, `risk`, and `confidence`.
- Keep `governance.required_reviews` and `human_approval_required`.
- Keep protected areas under `risk.protected_areas`.
- Keep evidence as external references and compact summaries, not role-contract output schemas.
- Keep overrides, but reduce override types to policy exceptions that affect risk, approval, scope, or evidence.
- Remove `runtime`.
- Remove first-class `handoffs`.
- Remove first-class `contracts.owner_agent`.
- Make optional phase state declarative only when it materially gates governance.

Optional declarative phase state:

```yaml
phases:
  planning: complete
  implementation: complete
  review: pending
```

This may remain if it is used only to validate merge readiness and evidence completeness. It should not include `active_agent`, handoff queues, current phase mutation, or runner status.

## 10. Breaking Changes

Expected breaking changes:

- `policyflow.run-phase` and all phase mutation commands removed from core.
- `policyflow.codex_runner` removed from core package.
- `policyflow.runners.yml` no longer generated.
- `ai/agents` and `ai/prompts` no longer generated.
- `runtime` and `handoffs` removed or ignored in V2 schema.
- `contracts` removed or converted to evidence references.
- `evaluation.required_metrics.actual_value` and threshold computations removed or moved out.
- `loop_governance.current_iteration` and loop statuses removed or moved out.
- Public imports for `start_workflow_phase`, `complete_workflow_phase`, `block_workflow_phase`, and `record_workflow_handoff` removed.
- `audit_workflows` payload may change or be replaced by `validate --json`.
- `policyflow sync` removed.
- `policyflow new-workflow` removed or moved.
- Bootstrap output changed substantially.

Compatibility strategy should not preserve out-of-scope functionality indefinitely. Keep a migration guide and clear failure messages for one major version.

## 11. Migration Strategy

1. Publish a V2 boundary ADR or update ADR-0002 with a scope-reduction addendum.
2. Add V2 schema models and validator path beside V1 temporarily.
3. Add migration diagnostics that classify V1 fields as kept, renamed, moved, or removed.
4. Simplify `init` behind a V2 output path.
5. Remove runtime commands from docs before removing implementation.
6. Move runner/Codex code to an external adapter repository or `Sentinel-AI-Core`.
7. Convert existing examples to one minimal governance example plus optional advanced external examples.
8. Remove duplicate assets or define one package asset source of truth.
9. Cut the public API to validation, PR validation, GitHub approval, and optional read-only audit.
10. Release V2 with explicit breaking-change notes and a short "ten-minute integration" guide.

## 12. Test Impact

Tests likely kept with updates:

- `tests/test_validator.py`: keep core risk, review, approval, override, evidence, PR governance tests; remove runtime/handoff/agent contract/evaluation analytics/loop runtime cases.
- `tests/test_pr_validator.py`: keep and align to V2 PR template.
- `tests/test_github_approval.py`: keep.
- `tests/test_public_api.py`: keep validation/API checks; remove runtime mutation expectations.
- `tests/test_consumer_config.py`: simplify to V2 config.
- `tests/test_bootstrap.py`: rewrite for minimal init.
- `tests/test_doctor.py`: rewrite for V2 doctor.
- `tests/test_consumer_github_workflow.py`: keep GitHub governance workflow checks, update command names/schema.
- `tests/test_release_packaging.py`: keep, update asset package list.
- `tests/test_repository_docs.py`: keep but rewrite assertions around smaller product boundary.

Tests primarily tied to MOVE/REMOVE:

- `tests/test_codex_runner.py`: MOVE with Codex adapter.
- `tests/test_runtime_cli.py`: most tests move/remove. Keep only read-only reporting tests if reporting remains.
- `tests/test_asset_sync.py`: REMOVE if `sync` is removed.
- `tests/test_workflow_generator.py`: MOVE or rewrite only if a tiny generator remains.
- `tests/test_golden_consumer_smoke.py`: rewrite because the current golden path runs init, doctor, new-workflow, fake runner, and PR validation.

Fixtures to prune:

- `tests/fixtures/runtime-*.yml`
- `tests/fixtures/handoff-*.yml`
- most `loop-governance-*` fixtures that represent runtime iteration state
- most `evaluation-*` fixtures that test threshold/metric analytics
- contract owner-agent fixtures where contracts are removed

## 13. Documentation Impact

Docs requiring major rewrite:

- `README.md`: remove "lightweight workflow orchestration framework"; lead with governance validator.
- `docs/getting-started.md`: replace full bootstrap/runner/sync path with ten-minute governance integration.
- `docs/public-api.md`: remove runtime mutation API.
- `docs/runner-contract.md`: move out of core docs or mark external adapter contract.
- `docs/audit-reporting.md`: simplify to read-only compliance output if kept.
- `docs/evaluation-governance.md`: reduce metrics to evidence/gate validation or move analytics details.
- `docs/loop-governance.md`: reduce to declarative guardrails or move loop execution/state details.
- `docs/metric-governance.md`: move analytics/productivity measurement out.
- `docs/querypilot-pilot.md`: move out of core package.
- `docs/schema-compatibility.md`: replace V1 compatibility posture with V2 breaking-change guidance.
- `docs/v2-migration-guide.md`: rewrite around actual scope reduction.
- `docs/provider-neutral-integration-contract.md`: keep as the bridge for external evidence, but remove any implication that PolicyFlow executes adapters.

Docs/assets with duplication risk:

- `docs/**` and `policyflow/assets/docs/**`
- `rules/**` and `policyflow/assets/rules/**`
- `agents/**` and `policyflow/assets/agents/**`
- `github/**` and `policyflow/assets/github/**`
- `workflows/templates/**` and `policyflow/assets/workflows/templates/**`
- `examples/**` and `policyflow/assets/examples/**`

## 14. Risks and Trade-offs

Risks:

- Existing users may rely on runtime mutation helpers and `run-phase`.
- V2 will break the documented public API unless a compatibility shim remains.
- Removing asset sync makes upgrades less automated.
- Simplifying evaluation/loop governance may temporarily reduce reporting richness.
- Externalizing runner execution requires a new home for useful adapter code.

Trade-offs:

- A smaller V2 is easier to adopt, explain, test, and maintain.
- Runtime features provide convenience, but they blur product ownership and grow support burden.
- Rich reports are useful, but analytics pressure can distract from governance validation.
- Backward compatibility has value, but preserving all V1 fields would keep the complexity V2 is meant to remove.

## 15. Recommended V2 Epic

Epic title: Reduce PolicyFlow 2.0 to a provider-neutral governance core.

Epic goal: Remove runtime/orchestration ownership from PolicyFlow core, simplify the consumer footprint, and stabilize a V2 governance schema and CLI that a new repository can adopt in less than ten minutes.

Epic non-goals:

- No model routing.
- No advisor execution.
- No PO-agent execution.
- No Codex/Copilot/provider integration in core.
- No scheduling, memory, message routing, or long-running runtime state.
- No engineering productivity analytics.
- No Model Routing Advisor Impact Baseline in PolicyFlow.

Success criteria:

- New consumer docs fit on one quickstart page.
- `policyflow init` creates only minimal governance assets.
- CLI is four commands unless a fifth read-only report command is explicitly justified.
- V2 schema fits the conceptual shape in this report.
- Public API excludes runtime mutation.
- Runner/Codex code is moved or removed.
- Duplicate asset source-of-truth problem is resolved.

## 16. Proposed GitHub Issues

### Issue 1: Define and freeze the PolicyFlow 2.0 governance boundary

Motivation: V2 needs an explicit architectural decision before code removal begins.

Scope:

- Add or update an ADR that makes scope reduction explicit.
- Declare runtime, runner, Codex adapter, handoff execution, model routing, analytics, and orchestration as out of core.
- Define allowed external evidence ingestion.

Out of scope:

- No implementation changes.
- No schema rewrite.

Affected files/modules:

- `docs/adr/0002-policyflow-is-not-an-agent-runtime.md`
- `docs/roadmap-agentic-governance.md`
- `README.md`

Dependencies: none.

Acceptance criteria:

- ADR states the V2 boundary in governance-only terms.
- ADR identifies moved/removed areas and external homes.
- README no longer positions PolicyFlow as a workflow orchestration framework.

Migration considerations: This prepares users for breaking changes but does not break behavior.

Risk level: LOW.

### Issue 2: Introduce the V2 governance schema and migration diagnostics

Motivation: Current schema mixes governance, execution, runtime, handoffs, contracts, loop state, and analytics.

Scope:

- Add V2 schema model for `change`, `risk`, `governance`, `confidence`, `evidence`, and `override`.
- Validate V2 directly.
- Add diagnostics for V1 fields that are renamed, moved, ignored, or removed.
- Decide whether optional declarative phase state remains.

Out of scope:

- No runtime mutation support.
- No execution adapter support.

Affected files/modules:

- `policyflow/models.py`
- `policyflow/schemas.py`
- `policyflow/validator.py`
- `tests/test_validator.py`
- `docs/schema-compatibility.md`
- `docs/v2-migration-guide.md`

Dependencies:

- Issue 1.

Acceptance criteria:

- Minimal V2 fixture validates.
- V1 runtime/handoff/contract fields produce clear migration diagnostics.
- Risk/review/human approval/protected area/override/evidence rules remain covered.

Migration considerations: High breaking-change visibility required.

Risk level: HIGH.

### Issue 3: Remove runtime mutation and runner execution from PolicyFlow core

Motivation: Runtime mutation and command execution are the clearest boundary violations.

Scope:

- Remove or deprecate `run-phase`, `start-phase`, `complete-phase`, `block-phase`, `record-handoff`, `next-step`, and `handoff-status` from core CLI.
- Remove runtime mutation public API exports.
- Move `policyflow/agent_execution.py` and `policyflow/codex_runner.py` out of core.
- Preserve external evidence contract documentation where useful.

Out of scope:

- No replacement runtime inside PolicyFlow.
- No model/provider adapter in core.

Affected files/modules:

- `policyflow/cli.py`
- `policyflow/api.py`
- `policyflow/__init__.py`
- `policyflow/runtime.py`
- `policyflow/agent_execution.py`
- `policyflow/codex_runner.py`
- `docs/runner-contract.md`
- `tests/test_runtime_cli.py`
- `tests/test_codex_runner.py`
- `tests/test_public_api.py`

Dependencies:

- Issue 1.
- Issue 2 for schema decisions.

Acceptance criteria:

- Core package no longer executes external runner commands.
- Public API no longer exports runtime mutation helpers.
- Tests for moved functionality are removed or relocated.
- Docs point external runtimes to evidence ingestion instead of PolicyFlow execution.

Migration considerations: Provide one release note with suggested external runtime ownership.

Risk level: HIGH.

### Issue 4: Simplify `policyflow init` and consumer config

Motivation: Current init output is too large for ten-minute adoption and installs execution assets by default.

Scope:

- Generate minimal `policyflow.yml`.
- Generate one starter V2 governance file.
- Generate GitHub PR template/workflow only when enabled.
- Remove default runner config, agents, prompts, large template tree, and managed sync metadata.
- Simplify `ConsumerConfig`.

Out of scope:

- No managed asset sync.
- No workflow execution setup.

Affected files/modules:

- `policyflow/bootstrap.py`
- `policyflow/consumer_config.py`
- `policyflow/assets/**`
- `examples/policyflow.minimal.yml`
- `examples/policyflow.github-governed.yml`
- `tests/test_bootstrap.py`
- `tests/test_consumer_config.py`
- `tests/test_golden_consumer_smoke.py`
- `docs/getting-started.md`

Dependencies:

- Issue 2.

Acceptance criteria:

- Fresh init produces the minimum V2 footprint.
- Doctor passes on the minimal footprint.
- Quickstart can be completed without understanding runners or agents.

Migration considerations: Existing bootstrapped repos keep old files but V2 does not manage or require them.

Risk level: HIGH.

### Issue 5: Reduce the CLI to governance commands

Motivation: The CLI surface currently reflects runtime, asset management, report variants, and workflow generation.

Scope:

- Keep `init`, `validate`, `validate-pr`, and `doctor`.
- Fold `validate-github-approvals` into `validate-pr` or keep it only if separation is justified.
- Remove `sync`, `new-workflow`, report variants, and runtime commands unless separately approved.
- Add JSON output only where CI needs it.

Out of scope:

- No new orchestration commands.
- No model routing or advisor commands.

Affected files/modules:

- `policyflow/cli.py`
- `tests/test_*cli*.py`
- `README.md`
- `docs/getting-started.md`
- `.github/workflows/policyflow-governance.yml`
- `github/workflows/policyflow-governance.yml`

Dependencies:

- Issue 2.
- Issue 3.
- Issue 4.

Acceptance criteria:

- `policyflow --help` shows only V2 governance commands.
- GitHub workflow uses V2 commands.
- Removed commands have migration notes.

Migration considerations: Command removal is a major-version break.

Risk level: HIGH.

### Issue 6: Rationalize reporting into a small read-only compliance output

Motivation: Reporting is useful, but separate status/audit/evaluation/loop reports create analytics pressure and extra CLI surface.

Scope:

- Decide whether V2 keeps `reporting.py`.
- If kept, provide one read-only compliance payload focused on validation, approval, overrides, protected areas, and evidence completeness.
- Remove loop/evaluation analytics rollups from core.

Out of scope:

- No productivity measurement.
- No engineering analytics platform.

Affected files/modules:

- `policyflow/reporting.py`
- `policyflow/cli.py`
- `policyflow/api.py`
- `docs/audit-reporting.md`
- `tests/test_runtime_cli.py`
- `tests/test_repository_docs.py`

Dependencies:

- Issue 2.

Acceptance criteria:

- Reporting output is small, read-only, and governance-focused.
- No report command implies execution or analytics ownership.
- Public API docs state compatibility expectations.

Migration considerations: Existing `policyflow.audit.v1` consumers need a V2 contract notice.

Risk level: MEDIUM.

### Issue 7: Collapse duplicated asset sources

Motivation: Top-level assets and `policyflow/assets/` contain overlapping files, with several divergent copies.

Scope:

- Choose one source of truth for packaged assets.
- Remove or generate mirrors.
- Update packaging and tests.
- Resolve known divergences in agents, rules, GitHub issue templates, docs, and examples.

Out of scope:

- No content expansion.
- No runtime asset retention unless explicitly externalized.

Affected files/modules:

- `policyflow/assets/**`
- `agents/**`
- `prompts/**`
- `rules/**`
- `workflows/templates/**`
- `github/**`
- `docs/**`
- `examples/**`
- `pyproject.toml`
- `tests/test_release_packaging.py`
- `tests/test_repository_docs.py`

Dependencies:

- Issue 4.

Acceptance criteria:

- A test proves packaged assets are sourced consistently.
- Divergent duplicate files are resolved or removed.
- V2 package data contains only necessary governance assets.

Migration considerations: Fewer packaged assets may affect consumers using manual copy paths.

Risk level: MEDIUM.

### Issue 8: Rewrite consumer-facing documentation for ten-minute adoption

Motivation: Current docs are accurate for 1.0.0 but too broad and contradictory for V2.

Scope:

- Rewrite README and getting-started around the minimal governance product.
- Rewrite public API, schema compatibility, and migration guide.
- Move runner, Codex, QueryPilot, loop execution, and metrics analytics content out of core docs or mark as external.
- Update repository docs tests.

Out of scope:

- No implementation changes beyond docs/tests.

Affected files/modules:

- `README.md`
- `docs/getting-started.md`
- `docs/public-api.md`
- `docs/schema-compatibility.md`
- `docs/v2-migration-guide.md`
- `docs/runner-contract.md`
- `docs/querypilot-pilot.md`
- `docs/evaluation-governance.md`
- `docs/loop-governance.md`
- `docs/metric-governance.md`
- `tests/test_repository_docs.py`

Dependencies:

- Issues 1-7.

Acceptance criteria:

- A new user can understand install, init, validate, PR validation, and doctor in one short guide.
- Docs no longer describe PolicyFlow as a runtime/orchestrator.
- Docs contain explicit moved/removed functionality notes.

Migration considerations: Docs must identify external homes for moved capabilities.

Risk level: MEDIUM.

