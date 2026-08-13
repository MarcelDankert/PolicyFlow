# PolicyFlow 2.0 Issue Plan

Implementation order is dependency-driven. The plan avoids deleting runtime functionality before the V2 validation path is available and covered by tests.

## Issue 1: Finalize and enforce the V2 governance boundary

Delivery Phase: Phase 1 - Foundation

Motivation: V2 needs an accepted architecture boundary before schema, CLI, API, and removal work begins.

Scope:

- Add ADR-0004 as the authoritative V2 architecture decision.
- Add tests or docs checks that prevent runtime/provider/analytics language from returning to core positioning.
- Update planning references to point to ADR-0004 as the final decision.

Out of Scope:

- No Python behavior changes.
- No schema cutover.
- No command removal.

Affected Files / Modules:

- `docs/adr/0004-policyflow-v2-return-to-governance-core.md`
- `README.md`
- `docs/roadmap-agentic-governance.md`
- `tests/test_repository_docs.py`

Dependencies: none.

Acceptance Criteria:

- ADR-0004 exists and declares PolicyFlow 2.0 as governance-only.
- Repository docs no longer present runtime execution as a V2 core responsibility.
- Tests fail if README reintroduces "workflow orchestration framework" as V2 positioning.
- ADR-0002 and ADR-0004 are not contradictory.

Tests:

- `pytest -q tests/test_repository_docs.py`
- `policyflow validate workflows/features/<active-v2-boundary-workflow>.yml`

Documentation Impact:

- README and roadmap point to ADR-0004 as the V2 decision.

Migration Impact:

- No behavior changes yet; sets expectations for breaking V2 migration.

Risk Level: LOW

Suggested Labels:

- `v2`
- `architecture`
- `documentation`

## Issue 2: Introduce the V2 governance schema and migration diagnostics

Delivery Phase: Phase 1 - Foundation

Motivation: V2 requires a small schema before any public API or CLI cutover can happen.

Scope:

- Add V2 models for `version`, `change`, `risk`, `governance`, `confidence`, `evidence`, and `overrides`.
- Add V2 parser/normalizer path.
- Add migration diagnostics for V1 fields classified as KEEP, RENAME, MOVE, or REMOVE.
- Detect `runtime`, `handoffs`, `contracts`, `loop_governance`, `evaluation`, and `execution` as V1-only unless a specific field maps to V2.
- Add fixtures for valid V2, missing required V2 fields, and V1 migration diagnostics.

Out of Scope:

- No runtime command removal.
- No public API cutover.
- No `policyflow migrate` command.

Affected Files / Modules:

- `policyflow/models.py`
- `policyflow/schemas.py`
- `policyflow/exceptions.py`
- `tests/test_validator.py`
- `tests/fixtures/`
- `docs/planning/policyflow-v1-v2-migration-matrix.md`
- `docs/schema-compatibility.md`

Dependencies:

- Issue 1.

Acceptance Criteria:

- `WorkflowDocumentV2` validates the agreed V2 schema.
- `runtime`, `handoffs`, and `contracts` produce explicit V1 migration diagnostics.
- `loop_governance` and `evaluation` produce diagnostics that point to external evidence representation.
- V2 schema rejects provider-specific fields and active agent/runner state.
- Every V2 field is covered by a test showing its governance purpose.

Tests:

- `pytest -q tests/test_validator.py`
- targeted V2 fixture tests.

Documentation Impact:

- Schema compatibility docs introduce V2 and classify V1 fields.

Migration Impact:

- Establishes the diagnostics users will see before V1 behavior is removed.

Risk Level: HIGH

Suggested Labels:

- `v2`
- `schema`
- `migration`
- `breaking-change`

## Issue 3: Rebuild core validation around Policy / Evidence / Merge Readiness

Delivery Phase: Phase 1 - Foundation

Motivation: V2 validation must center on governance decisions, not phase orchestration.

Scope:

- Rebuild validation rules around risk, protected areas, required reviews, human approval, evidence status, override validity, and merge readiness.
- Add `PASS`, `WARN`, and `BLOCK` validation result semantics.
- Add JSON validation result output shape.
- Validate evidence IDs, types, sources, statuses, and refs.
- Validate override lifecycle and required approval metadata.
- Validate merge readiness without phase state unless a tested governance need is proven.

Out of Scope:

- No test execution.
- No metric calculation.
- No loop execution.
- No GitHub mutation.
- No runtime state mutation.

Affected Files / Modules:

- `policyflow/validator.py`
- `policyflow/rules.py`
- `policyflow/models.py`
- `policyflow/reporting.py`
- `tests/test_validator.py`
- `tests/fixtures/`

Dependencies:

- Issue 2.

Acceptance Criteria:

- Valid V2 changes return `PASS` when governance is satisfied.
- Missing required evidence returns `BLOCK`.
- Missing human approval returns `BLOCK` or pending state according to documented `allow_pending` behavior.
- Expiring but still valid overrides return `WARN`.
- Expired overrides return `BLOCK`.
- Merge readiness is computed without runtime, active agent, runner, handoff, loop iteration, or metric calculation fields.

Tests:

- `pytest -q tests/test_validator.py`
- focused merge-readiness result tests.

Documentation Impact:

- Validation result contract documented for CI and external evidence producers.

Migration Impact:

- V1 workflows still receive diagnostics, but V2 validation becomes the target behavior.

Risk Level: HIGH

Suggested Labels:

- `v2`
- `validator`
- `merge-readiness`
- `evidence`

## Issue 4: Cut over the public API and CLI to governance-only behavior

Delivery Phase: Phase 2 - Core Cutover

Motivation: Users should interact with PolicyFlow through a small governance-only interface.

Scope:

- Replace public API with governance-only functions.
- Reduce CLI to `init`, `validate`, `validate-pr`, and `doctor`.
- Fold GitHub approval review validation into `validate-pr --github-reviews`.
- Add `--json` output to validation commands where needed.
- Remove runtime mutation symbols from `policyflow.api` and package root exports.

Out of Scope:

- No runtime module deletion in this issue unless covered by Issue 5.
- No migration command.
- No separate `explain` command.

Affected Files / Modules:

- `policyflow/api.py`
- `policyflow/__init__.py`
- `policyflow/cli.py`
- `policyflow/github.py`
- `tests/test_public_api.py`
- CLI tests currently in `tests/test_runtime_cli.py`
- `docs/public-api.md`

Dependencies:

- Issue 2.
- Issue 3.

Acceptance Criteria:

- `policyflow --help` exposes only `init`, `validate`, `validate-pr`, and `doctor`.
- `validate-pr --github-reviews pr-reviews.json` validates declared approvers.
- Package root no longer exports runtime mutation helpers.
- Importing PolicyFlow does not import runtime execution modules.
- Public API docs list governance APIs only.

Tests:

- `pytest -q tests/test_public_api.py`
- targeted CLI help tests.
- PR validation tests.

Documentation Impact:

- Public API docs rewritten around governance-only API.

Migration Impact:

- Runtime public API symbols are removed with explicit migration notes.

Risk Level: HIGH

Suggested Labels:

- `v2`
- `cli`
- `public-api`
- `breaking-change`

## Issue 5: Remove runtime, runner execution, provider adapters, handoffs, and agent execution ownership

Delivery Phase: Phase 2 - Core Cutover

Motivation: The execution boundary must be enforced in code, imports, package data, tests, and docs.

Scope:

- Remove or externalize `policyflow/agent_execution.py`.
- Remove or externalize `policyflow/codex_runner.py`.
- Remove `policyflow/runtime.py` mutation behavior from core.
- Remove runtime, handoff, and agent contract models from V2 core.
- Remove runner config handling from core validation and bootstrap paths.
- Remove tests that exist only for runner/Codex/runtime mutation behavior.
- Preserve only migration diagnostics for old fields.

Out of Scope:

- No replacement runtime.
- No provider adapter.
- No model routing.
- No agent prompt management.

Affected Files / Modules:

- `policyflow/agent_execution.py`
- `policyflow/codex_runner.py`
- `policyflow/runtime.py`
- `policyflow/models.py`
- `policyflow/validator.py`
- `policyflow/cli.py`
- `tests/test_runtime_cli.py`
- `tests/test_codex_runner.py`
- runtime and handoff fixtures.
- `docs/runner-contract.md`

Dependencies:

- Issue 2.
- Issue 3.
- Issue 4.

Acceptance Criteria:

- The package no longer imports or shells out to Codex.
- No core module executes external runner commands.
- No V2 model contains `active_agent`, `runner`, `runtime.status`, or first-class `handoffs`.
- Runtime and handoff V1 files produce migration diagnostics instead of V2 validation success.
- Tests for moved functionality are removed or relocated outside core.

Tests:

- `pytest -q`
- import smoke test proving `policyflow` does not import execution modules.
- package data test proving runner/Codex assets are not packaged.

Documentation Impact:

- Runner contract docs are removed from core docs or marked as external/moved.

Migration Impact:

- High. Users must move execution to Sentinel-AI-Core, consumer tooling, or provider adapters.

Risk Level: HIGH

Suggested Labels:

- `v2`
- `runtime-removal`
- `provider-neutral`
- `breaking-change`

## Issue 6: Rebuild minimal consumer init, config, and doctor

Delivery Phase: Phase 3 - Consumer Experience

Motivation: The V2 adoption path must be understandable in less than ten minutes.

Scope:

- Rebuild `policyflow init` to generate the approved minimal footprint.
- Replace `consumer_config.py` with smaller `config.py`.
- Simplify doctor to config/schema/PR template/GitHub workflow readiness checks.
- Remove runner, prompt, agent, sync metadata, large template tree, and provider checks from init and doctor.
- Add a V2 golden consumer smoke test.

Out of Scope:

- No managed asset sync.
- No workflow generator.
- No runner setup.
- No GitHub mutation preflight.

Affected Files / Modules:

- `policyflow/bootstrap.py`
- `policyflow/consumer_config.py`
- `policyflow/config.py`
- `policyflow/doctor.py`
- `policyflow/assets/**`
- `tests/test_bootstrap.py`
- `tests/test_consumer_config.py`
- `tests/test_doctor.py`
- `tests/test_golden_consumer_smoke.py`
- `examples/`

Dependencies:

- Issue 2.
- Issue 3.
- Issue 4.

Acceptance Criteria:

- `policyflow init` creates only `policyflow.yml`, `policyflow/change.example.yml`, and conditional GitHub PR/workflow files.
- `policyflow init` does not create `policyflow.runners.yml`, prompts, agents, runtime state, `.policyflow/bootstrap.json`, or large workflow templates.
- `policyflow doctor` passes on a clean V2 initialized repository.
- Doctor does not check provider CLIs, runner commands, credentials, issue mutation, branch mutation, label mutation, milestone mutation, or merge permissions.
- Clean consumer V2 golden-path smoke test passes.

Tests:

- `pytest -q tests/test_bootstrap.py tests/test_consumer_config.py tests/test_doctor.py tests/test_golden_consumer_smoke.py`

Documentation Impact:

- Getting Started updated after implementation.

Migration Impact:

- Existing bootstrapped repos retain old files but V2 no longer manages or requires them.

Risk Level: HIGH

Suggested Labels:

- `v2`
- `consumer-experience`
- `init`
- `doctor`
- `breaking-change`

## Issue 7: Simplify GitHub integration, reporting, and packaged assets

Delivery Phase: Phase 3 - Consumer Experience

Motivation: GitHub must remain read-only, reporting must explain compliance only, and packaged assets need one small source of truth.

Scope:

- Rebuild GitHub validation around PR body and review JSON only.
- Ensure generated GitHub Actions workflow uses read-only permissions.
- Rebuild `reporting.py` as minimal validation result formatting or remove it if redundant.
- Remove `status`, `audit`, `evaluation-report`, and `loop-report` command architecture.
- Remove duplicate or obsolete packaged assets.
- Update package data to V2 governance assets only.

Out of Scope:

- No GitHub mutation.
- No analytics dashboards.
- No model or productivity metrics.
- No managed asset sync.

Affected Files / Modules:

- `policyflow/github_approval.py`
- `policyflow/github.py`
- `policyflow/reporting.py`
- `github/**`
- `.github/**`
- `policyflow/assets/**`
- `pyproject.toml`
- `tests/test_github_approval.py`
- `tests/test_consumer_github_workflow.py`
- `tests/test_release_packaging.py`
- `tests/test_repository_docs.py`

Dependencies:

- Issue 3.
- Issue 4.
- Issue 6.

Acceptance Criteria:

- GitHub workflow performs read-only validation only.
- No GitHub code checks mutation capabilities for branch, issue, PR creation, labels, milestones, or merges.
- Validation JSON includes merge-readiness explanation.
- No core command exposes loop/evaluation dashboards or productivity analytics.
- Package data excludes agents, prompts, runners, provider adapters, and obsolete templates.
- Asset source-of-truth drift is eliminated or tested.

Tests:

- `pytest -q tests/test_github_approval.py tests/test_consumer_github_workflow.py tests/test_release_packaging.py tests/test_repository_docs.py`

Documentation Impact:

- GitHub and reporting docs rewritten around read-only governance.

Migration Impact:

- Consumers parsing `policyflow.audit.v1` need migration notes.
- Manual-copy asset consumers need V2 package asset guidance.

Risk Level: MEDIUM

Suggested Labels:

- `v2`
- `github`
- `reporting`
- `packaging`
- `breaking-change`

## Issue 8: Rewrite docs, migration guide, and prepare V2 release

Delivery Phase: Phase 4 - Release

Motivation: V2 is a deliberate breaking release and needs clear adoption and migration documentation.

Scope:

- Rewrite README around governance-only V2.
- Rewrite Getting Started for ten-minute adoption.
- Rewrite public API docs.
- Rewrite schema compatibility and V2 migration guide.
- Update release notes and packaging metadata for V2.0.0.
- Update examples to the minimal V2 consumer path.
- Run final release readiness and smoke tests.

Out of Scope:

- No new product features.
- No migration command unless separately approved after migration testing.
- No runtime or analytics docs as core product docs.

Affected Files / Modules:

- `README.md`
- `docs/getting-started.md`
- `docs/public-api.md`
- `docs/schema-compatibility.md`
- `docs/v2-migration-guide.md`
- `docs/release-and-upgrade.md`
- `CHANGELOG.md`
- `examples/**`
- `pyproject.toml`
- `tests/test_repository_docs.py`
- release workflows/tests.

Dependencies:

- Issues 1-7.

Acceptance Criteria:

- README explains PolicyFlow 2.0 in governance-only terms.
- Getting Started covers install, init, validate, validate-pr, and doctor in one concise path.
- Migration guide references the V1 to V2 migration matrix.
- Release notes list removed commands, removed public API symbols, removed fields, and external ownership guidance.
- Full test suite passes.
- V2 golden consumer smoke test passes.

Tests:

- `pytest -q`
- `policyflow validate workflows/features/<v2-release-workflow>.yml`
- V2 golden consumer smoke test.

Documentation Impact:

- Complete V2 docs cutover.

Migration Impact:

- Final migration documentation delivered for V1 users.

Risk Level: MEDIUM

Suggested Labels:

- `v2`
- `documentation`
- `release`
- `migration`

