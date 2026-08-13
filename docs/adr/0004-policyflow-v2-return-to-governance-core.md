# ADR-0004: PolicyFlow 2.0 Returns To Governance Core

## Status

Accepted

## Context

PolicyFlow 1.0.0 contains a useful governance validator, but it also contains runtime and orchestration-adjacent responsibilities: phase mutation, handoffs, agent role contracts, external runner execution, a Codex adapter, runner configuration, managed asset synchronization, workflow generation, loop state, evaluation metrics, and broad reporting.

ADR-0002 established that PolicyFlow is not an agent runtime. The PolicyFlow 2.0 planning documents confirm that this boundary must become stricter, not broader. PolicyFlow 2.0 is a small provider-neutral policy-as-code governance validator for AI-assisted software development.

## Problem Statement

The current product surface is too large for the intended governance mission. A new consumer must understand agents, prompts, runners, workflow phases, contracts, handoffs, runtime state, loop and evaluation reports, sync behavior, and GitHub preflight details before reaching the core value.

PolicyFlow 2.0 must remove execution ownership and make governance validation the main product.

## Decision

PolicyFlow 2.0 will return to a governance-only core. It validates declared governance policy and evidence, validates pull request claims, validates declared GitHub approvals, and produces a governance decision.

Target architecture:

```text
External execution systems
        |
        | normalized evidence
        v
+-----------------------------+
|        PolicyFlow 2.0       |
|                             |
| Config                      |
| Governance Schema           |
| Risk Rules                  |
| Evidence Validation         |
| Override Validation         |
| PR Validation               |
| GitHub Approval Validation  |
| Merge Readiness             |
+-----------------------------+
        |
        v
 PASS / WARN / BLOCK
```

There are no execution arrows from PolicyFlow back into external systems.

## Product Boundary

PolicyFlow begins when a repository declares governance policy and evidence for a software change.

PolicyFlow ends when it produces a governance decision:

- `PASS`
- `WARN`
- `BLOCK`

PolicyFlow does not perform the work needed to satisfy governance.

## In Scope

- `policyflow.yml` configuration.
- V2 governance document schema.
- Risk and protected-area validation.
- Required review validation.
- Human approval requirement validation.
- Evidence reference validation.
- Override and exception validation.
- PR body validation.
- GitHub review JSON validation for declared approvals.
- Minimal GitHub Actions validation check.
- Minimal PR template.
- Human-readable validation diagnostics.
- JSON validation results.
- Merge-readiness explanation derived from validation.

## Out of Scope

- Agent execution.
- Agent orchestration.
- Prompt management.
- Runner configuration.
- Codex, Copilot, or provider adapters.
- Provider SDKs or credentials.
- Model routing.
- Advisor execution.
- Scheduling.
- Queues.
- Memory.
- Message routing.
- Workflow engines.
- Loop execution.
- Test execution.
- Security scan execution.
- Metric calculation.
- Engineering analytics.
- Productivity measurement.
- PO-agent execution.
- Issue creation.
- Branch creation.
- Pull request creation.
- Label or milestone mutation.
- Merge automation.
- Managed asset synchronization.

## V2 Core Responsibilities

PolicyFlow 2.0 owns:

- Parsing governance configuration.
- Parsing V2 change governance files.
- Applying risk, protected-area, required-review, approval, evidence, and override rules.
- Validating PR body claims against the change governance file.
- Validating GitHub review JSON against declared human approval requirements.
- Producing merge-readiness diagnostics.
- Providing a minimal init path.
- Providing a small stable governance API and CLI.

## V2 Target Architecture

Target package:

```text
policyflow/
    __init__.py
    api.py
    cli.py
    config.py
    exceptions.py
    github.py
    models.py
    rules.py
    validator.py
    reporting.py
```

`reporting.py` is retained only as a small read-only compliance helper. It must not contain dashboards, loop reports, evaluation reports, productivity analytics, runtime status summaries, or model metrics.

Current module decisions:

| Module | V2 Decision | Reason |
| --- | --- | --- |
| `agent_execution.py` | MOVE | Execution dispatch belongs in Sentinel-AI-Core, consumer tooling, or adapters. |
| `codex_runner.py` | MOVE | Provider-specific adapter does not belong in provider-neutral core. |
| `runtime.py` | REMOVE | Runtime mutation and handoff state are outside the V2 product boundary. |
| `bootstrap.py` | REBUILD | `init` remains, but the generated footprint changes completely. |
| `sync.py` | REMOVE | Managed asset synchronization is outside the small governance core. |
| `doctor.py` | SIMPLIFY | Keep minimal governance readiness checks only. |
| `workflow_generator.py` | REMOVE | V2 ships an example file, not a workflow generation subsystem. |
| `reporting.py` | REBUILD | Keep only minimal read-only validation and merge-readiness explanation. |
| `consumer_config.py` | REBUILD | Replace with a smaller `config.py` for V2 paths and governance features. |
| `github_approval.py` | REBUILD | Replace with `github.py` for read-only PR/review evidence validation. |

## V2 Schema Direction

The V2 schema is:

```yaml
version: 2

change:
  id: example-change
  type: feature
  summary: Example change.

risk:
  level: medium
  rationale: ...
  protected_areas: []

governance:
  required_reviews: []
  human_approval_required: false

confidence:
  level: medium
  summary: ...

evidence:
  - id: tests
    type: test
    source: ci
    status: passed
    ref: ...

overrides: []
```

Rules:

- No runtime state.
- No active agent.
- No runner status.
- No first-class handoff state.
- No provider-specific fields.
- No model-specific fields.
- No analytics values that PolicyFlow calculates.
- No current loop iteration state.
- No fields preserved only because V1 had them.
- No declarative phase state in the core schema unless an implementation issue proves it directly affects merge readiness.

## V2 CLI Direction

Approved V2 CLI:

```text
policyflow init
policyflow validate
policyflow validate-pr
policyflow doctor
```

`policyflow explain` is not approved as a separate command for the initial V2 cutover. Human-readable diagnostics and JSON validation output provide the same value with less CLI surface. It may be reconsidered only if validation output cannot provide a clear merge-readiness explanation.

Current command decisions:

| Command | V2 Decision | New Owner |
| --- | --- | --- |
| `init` | REBUILD | PolicyFlow core |
| `validate` | REBUILD | PolicyFlow core |
| `validate-pr` | REBUILD | PolicyFlow core |
| `doctor` | SIMPLIFY | PolicyFlow core |
| `validate-github-approvals` | FOLD INTO `validate-pr` | PolicyFlow core |
| `config-check` | REMOVE/FOLD INTO `doctor` | PolicyFlow core |
| `status` | REMOVE | Validation JSON output |
| `audit` | REMOVE | Validation JSON output or external analytics |
| `evaluation-report` | REMOVE | External analytics/governance reporting |
| `loop-report` | REMOVE | External runtime/analytics |
| `run-phase` | MOVE | Sentinel-AI-Core, consumer tooling, adapters |
| `next-step` | MOVE | External runtime/workflow tooling |
| `handoff-status` | MOVE | External runtime/workflow tooling |
| `start-phase` | MOVE | External runtime/workflow tooling |
| `complete-phase` | MOVE | External runtime/workflow tooling |
| `block-phase` | MOVE | External runtime/workflow tooling |
| `record-handoff` | MOVE | External runtime/workflow tooling |
| `new-workflow` | REMOVE | Project templates or external scaffolding |
| `sync` | REMOVE | Manual migration/release notes |

## Public API Direction

Stable V2 public API is governance-only:

- `validate_change(path)`
- `validate_change_data(data)`
- `validate_pull_request(change_path, pr_body_path, *, github_reviews_path=None, allow_pending_approval=False)`
- `validate_github_approvals(change, reviews)`
- `explain_merge_readiness(validation_result)`

Remove public runtime mutation symbols:

- `start_workflow_phase`
- `complete_workflow_phase`
- `block_workflow_phase`
- `record_workflow_handoff`

Remove stable audit/runtime payload commitments from the public API.

## GitHub Integration Boundary

PolicyFlow treats GitHub as an evidence source, not a control plane.

In scope:

- PR body validation.
- Reading PR review JSON supplied by GitHub Actions or local tooling.
- Validating declared approvers have `APPROVED` reviews.
- A read-only GitHub Actions workflow using `contents: read` and `pull-requests: read`.
- A minimal PR template.

Out of scope:

- Creating branches, issues, pull requests, labels, or milestones.
- Editing pull requests.
- Waiting for approvals in long-running jobs.
- Merge automation.
- GitHub App mutation permission preflight.

## Evidence Model Boundary

Evidence is produced outside PolicyFlow and validated inside PolicyFlow.

PolicyFlow validates:

- Evidence IDs are unique.
- Evidence has type, source, status, and reference.
- Required evidence is present.
- Blocking evidence is not failed or missing.
- PR body references required evidence.
- Human approval evidence matches GitHub review metadata when supplied.

PolicyFlow does not:

- Run tests.
- Run security scans.
- Calculate metrics.
- Execute loops.
- Fetch provider results.
- Create evidence through agents.

## Reporting Boundary

Reporting remains only as compliance explanation. The V2 default is:

- human-readable validation diagnostics.
- JSON validation result.
- merge-readiness fields in validation output.

`reporting.py` may exist only to format these results. It must not recreate V1 `status`, `audit`, `evaluation-report`, or `loop-report` architecture.

## Migration Strategy

V2 is a deliberate breaking release. The goal is bounded migration, not indefinite backwards compatibility.

Migration strategy:

1. Introduce V2 schema and validation alongside V1 detection.
2. Emit explicit migration diagnostics for V1-only fields.
3. Classify old fields as KEEP, RENAME, MOVE, or REMOVE.
4. Rebuild public API and CLI after V2 validation is covered by tests.
5. Remove execution modules after the governance path is available.
6. Rebuild minimal init, config, doctor, and GitHub workflow.
7. Rewrite docs and release notes.

No `policyflow migrate` command is approved initially. A static migration matrix plus actionable diagnostics is enough for the targeted V2 scope. A migration command may be reconsidered only if diagnostics prove insufficient for real V1 repositories.

## Consequences

PolicyFlow 2.0 becomes smaller and clearer, but it breaks V1 users who adopted runtime, runner, handoff, contract, audit, sync, or workflow-generation features.

## Positive Consequences

- Product is understandable in less than ten minutes.
- Provider neutrality becomes enforceable.
- Runtime ownership is removed from core.
- CLI and public API become much smaller.
- Schema becomes easier to maintain.
- External runtimes can integrate through normalized evidence.
- Packaging and bootstrap become simpler.

## Negative Consequences

- Existing V1 workflow files require migration.
- Runtime command users lose core support.
- Public API consumers using runtime helpers break.
- `policyflow.audit.v1` consumers need a new integration path.
- External homes are needed for runner and Codex adapter code if that functionality remains useful.

## Breaking Changes

- V1 `workflow/context/execution/contracts/runtime/handoffs/loop_governance/evaluation` shape is replaced by V2 `change/risk/governance/confidence/evidence/overrides`.
- Runtime and handoff fields are removed from core schema.
- Agent contracts are removed from core schema.
- Runner configuration is not generated or validated.
- Codex adapter is removed from core package.
- Runtime mutation commands are removed.
- `new-workflow` and `sync` are removed.
- Report commands are removed or replaced by validation JSON output.
- Public runtime mutation API symbols are removed.
- Default `init` output is rebuilt.

## Risks

- High migration cost for consumers using V1 runtime features.
- Tests must be reworked carefully to avoid deleting coverage before V2 coverage exists.
- Docs must avoid preserving old runtime language.
- External adapter ownership must be resolved before removing useful execution code.
- Package asset cleanup may break manual-copy consumers.

## Alternatives Considered

- Keep V1 and add more guardrails. Rejected because it preserves runtime and orchestration surface.
- Preserve runtime mutation as "lightweight governance state." Rejected because V2 removes active phase control and handoff state from the core boundary.
- Keep runner execution as provider-neutral. Rejected because command dispatch is execution ownership even when provider-neutral.
- Keep `explain` as a fifth initial command. Rejected for initial V2 because JSON and human-readable validation can carry merge-readiness explanation.
- Add `policyflow migrate`. Rejected initially because diagnostics and documentation are lower maintenance; reconsider only if needed.

## Follow-up Work

- Implement the V2 schema and migration diagnostics.
- Rebuild validation around policy, evidence, and merge readiness.
- Cut over public API and CLI.
- Move/remove runtime, runner, Codex, handoff, and agent execution code.
- Rebuild minimal init, config, doctor, and read-only GitHub workflow.
- Rebuild reporting as validation output formatting only.
- Collapse packaged assets to one V2 source of truth.
- Rewrite consumer documentation and migration guide.
- Prepare the V2.0.0 breaking release.

