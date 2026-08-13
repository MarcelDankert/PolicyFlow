# PolicyFlow 2.0 Gap Analysis

## Summary

The current repository is more capable than a greenfield PolicyFlow 2.0 should be. It has accumulated runtime, orchestration, provider-adapter, reporting, bootstrap, asset management, workflow generation, and developer utility responsibilities around a governance core.

The greenfield design removes those accumulated responsibilities and rebuilds PolicyFlow as a small validator:

- validate governance documents.
- validate PR claims.
- validate human approval evidence.
- explain merge readiness.
- initialize a minimal repository footprint.

The gap is large, but most complexity clusters in a few removable areas: runner execution, runtime state mutation, first-class handoffs/contracts, asset sync, bloated bootstrap, duplicated assets, and report variants.

## Current vs Greenfield

| Area | Current Repository | Greenfield V2 | Recommendation |
| --- | --- | --- | --- |
| Product positioning | Governance plus lightweight workflow orchestration | Governance-only policy-as-code validator | REBUILD |
| CLI | 17 commands across validation, setup, runtime, reports, sync, generation | 4 commands: `init`, `validate`, `validate-pr`, `doctor` | SIMPLIFY |
| Public API | Validation, reporting, audit, runtime mutation | Governance validation only | REBUILD |
| Schema | `workflow`, `context`, `governance`, `execution`, `evidence`, `contracts`, `runtime`, `handoffs`, `loop_governance`, `evaluation`, `overrides` | `change`, `risk`, `governance`, `confidence`, `evidence`, `overrides` | REBUILD |
| Runtime state | `runtime.status`, `current_phase`, `active_agent`, mutation commands | No runtime state | REMOVE |
| Agent execution | External runner dispatch and result application | External systems emit evidence | MOVE |
| Codex integration | Packaged Codex CLI adapter | External adapter | MOVE |
| Runner config | Default `policyflow.runners.yml` | No runner config | REMOVE |
| Agents/prompts | Packaged and bootstrapped | External runtime/consumer-owned | MOVE |
| Role contracts | First-class agent-owned phase contracts | Evidence references only | MOVE |
| Handoffs | First-class handoff state and validation | External evidence or no core concept | MOVE |
| Loop governance | Declarative plus iteration/status compliance | Outside core unless reduced to simple evidence policy | MOVE |
| Evaluation | Metrics, thresholds, actual values, reports | Evidence type/status/ref only | SIMPLIFY |
| Reporting | Status, audit, evaluation report, loop report | Minimal validation/explain output | SIMPLIFY |
| Bootstrap | Large managed consumer scaffold | Minimal config, example, PR template, GitHub workflow | REBUILD |
| Sync | Managed asset upgrade mechanism | No core sync | REMOVE |
| Workflow generation | Creates detailed workflow files | Example file only | REMOVE |
| Doctor | Checks config, runner, GitHub CLI/App permissions, assets | Checks minimal governance readiness | SIMPLIFY |
| GitHub integration | PR checks plus approval validation and mutation-oriented permission preflight | Read-only PR/review validation | SIMPLIFY |
| Packaged assets | Mirrored top-level assets with drift | Single small source of truth | REBUILD |
| Docs | Broad and sometimes contradictory runtime/non-runtime story | Short governance-first docs | REBUILD |

## Unnecessary Complexity

### Runtime Mutation

Current files:

- `policyflow/runtime.py`
- runtime CLI commands in `policyflow/cli.py`
- runtime public API exports in `policyflow/api.py` and `policyflow/__init__.py`
- runtime fixtures and `tests/test_runtime_cli.py`

Why it is unnecessary in greenfield V2:

Governance can validate declared evidence without owning phase state transitions. External runtimes can record their own state and emit evidence.

Simplification:

- Remove mutation commands.
- Remove runtime from public API.
- Remove `runtime` schema block.
- Keep only evidence status if needed for merge readiness.

Migration risk: HIGH because current docs and tests treat runtime mutation as stable.

### Agent Execution and Runner Abstraction

Current files:

- `policyflow/agent_execution.py`
- `policyflow/codex_runner.py`
- `policyflow.runners.yml`
- runner docs and tests

Why it is unnecessary:

It makes PolicyFlow responsible for how work is performed. That directly conflicts with the execution boundary.

Simplification:

- Move to Sentinel-AI-Core, a provider adapter repo, or consumer tooling.
- PolicyFlow consumes result evidence only.

Migration risk: HIGH for users of `run-phase`.

### Contracts and Handoffs

Current files/concepts:

- `contracts` schema.
- `handoffs` schema.
- `rules/agent-handoff-contracts.md`.
- workflow templates with `handoff_to` and owner agents.

Why it is unnecessary:

The valuable part is evidence transfer. The current design makes agent roles and handoff state part of PolicyFlow's compatibility surface.

Simplification:

- Replace with evidence IDs and required review roles.
- Let external systems manage agent handoffs.

Migration risk: HIGH for existing workflow files.

### Evaluation and Loop Reporting

Current files:

- evaluation/loop models in `policyflow/models.py`.
- validation logic in `policyflow/validator.py`.
- report logic in `policyflow/reporting.py`.
- docs and fixtures.

Why it is too complex:

Some evaluation and loop concepts are governance-adjacent, but current implementation includes statuses, iteration counts, thresholds, actual values, and summary reporting. That drifts toward analytics and runtime loop state.

Simplification:

- Keep evidence references such as "test evidence passed" and "security review pending."
- Move metric calculation, thresholds, loop execution, and dashboards outside core.

Migration risk: MEDIUM to HIGH depending on how many consumers adopted these fields.

### Bootstrap and Sync

Current files:

- `policyflow/bootstrap.py`
- `policyflow/sync.py`
- `policyflow/assets/**`
- `.policyflow/bootstrap.json`

Why it is too complex:

Bootstrap installs enough assets that sync became necessary. A greenfield governance tool should not need managed asset lifecycle machinery.

Simplification:

- Minimal init.
- No sync.
- One source of truth for package assets.

Migration risk: MEDIUM.

### GitHub Mutation Preflight

Current files:

- `policyflow/doctor.py`.
- GitHub App preflight tests.

Why it is too broad:

PolicyFlow V2 should read PR/review data and run checks, not prepare for branch, issue, label, milestone, or PR mutation.

Simplification:

- Keep checks for PR validation wiring.
- Remove mutation capability checks.

Migration risk: LOW to MEDIUM.

## Architectural Drift

The repository drifted through convenience features becoming product concepts:

- A helpful phase-state helper became runtime orchestration.
- A provider-neutral runner contract became execution ownership.
- A Codex reference adapter became provider-specific package surface.
- Richer evidence became metrics, thresholds, and report rollups.
- Handoff visibility became first-class handoff workflow state.
- Bootstrap convenience became managed asset ownership.
- Public API stabilization froze runtime helpers that should have remained external.

## Simplification Opportunities

Highest leverage cuts:

1. Remove runner execution and Codex adapter from core.
2. Remove runtime mutation CLI and public API.
3. Rebuild schema around `change`, `risk`, `governance`, `confidence`, `evidence`, and `overrides`.
4. Replace contracts/handoffs with evidence references.
5. Rebuild bootstrap as a four-file starter.
6. Remove sync.
7. Collapse report commands into JSON validation output or one `explain` command.
8. Remove duplicate packaged assets.
9. Rewrite docs around governance-only adoption.

## Migration Risks

### High Risk

- Existing workflow files using `runtime`, `handoffs`, `contracts`, `loop_governance`, and `evaluation`.
- Users of runtime mutation commands.
- Users of `run-phase` and Codex adapter.
- Consumers importing runtime helpers from `policyflow`.

### Medium Risk

- Users of `policyflow sync`.
- Users relying on bootstrapped agent/prompt/rule trees.
- Users parsing `policyflow.audit.v1`.
- Users relying on `new-workflow`.

### Low Risk

- Documentation repositioning.
- GitHub mutation preflight removal.
- Issue template removal from default init.

## Recommended Migration Approach

1. Declare the greenfield V2 boundary in an ADR.
2. Add V2 schema and diagnostics without preserving runtime fields.
3. Move runner and Codex code to an external location before deleting docs.
4. Remove runtime public API exports.
5. Replace bootstrap with minimal V2 init.
6. Rewrite docs and examples.
7. Remove sync and workflow generation.
8. Publish a breaking V2 release with a concise migration guide.

## Greenfield Target

The maintained five-year version of PolicyFlow should be boring:

- one small schema.
- one validator.
- one PR validation path.
- one GitHub approval evidence check.
- one minimal init.
- one clear product boundary.

That is enough to provide meaningful governance without becoming the system that performs the work.

