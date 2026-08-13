# PolicyFlow 2.0 Epic

## PolicyFlow 2.0 - Return to Governance Core

## Goal

Ship PolicyFlow 2.0 as a small provider-neutral policy-as-code governance validator for AI-assisted software development.

PolicyFlow 2.0 validates declared governance policy and evidence, validates pull request claims, validates GitHub approval evidence, and produces a merge-readiness decision. It does not execute work.

## Why Now

The discovery and greenfield planning work showed that PolicyFlow 1.0.0 has accumulated runtime, runner, Codex adapter, handoff, workflow generation, asset sync, loop state, evaluation metric, and reporting responsibilities around a governance core.

The V2 release is the correct point to remove those responsibilities deliberately instead of preserving them as permanent compatibility obligations.

## Product Boundary

PolicyFlow starts when a repository declares governance policy and evidence for a software change.

PolicyFlow ends when it returns a governance result:

- `PASS`
- `WARN`
- `BLOCK`

PolicyFlow does not create the evidence or perform the work.

## Architecture Summary

Target modules:

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

`reporting.py` is retained only for small read-only compliance formatting. Runtime execution modules are not retained in core.

Target CLI:

```text
policyflow init
policyflow validate
policyflow validate-pr
policyflow doctor
```

Target schema:

```yaml
version: 2
change: ...
risk: ...
governance: ...
confidence: ...
evidence: []
overrides: []
```

## Scope

- Final V2 ADR.
- V2 schema and models.
- V2 validation and migration diagnostics.
- Merge-readiness validation result.
- Governance-only public API.
- Reduced CLI.
- Removal or externalization of runtime, runner, Codex, handoff, and agent execution ownership.
- Minimal `init`.
- Simplified config and doctor.
- Read-only GitHub integration.
- Minimal compliance output.
- Packaged asset cleanup.
- Documentation rewrite and V2 migration guide.
- V2 release readiness.

## Non-goals

- Agent execution.
- Agent orchestration.
- Prompt management.
- Runner configuration.
- Codex/Copilot/provider adapters.
- Provider SDKs or credentials.
- Model routing.
- Advisor execution.
- Scheduling, queues, memory, or message routing.
- Workflow engine behavior.
- Loop execution.
- Test or security scan execution.
- Metric calculation.
- Engineering analytics.
- Productivity measurement.
- PO-agent execution.
- GitHub mutation.
- Managed asset synchronization.
- Indefinite V1 compatibility.

## Success Criteria

- `WorkflowDocumentV2` validates the agreed V2 schema.
- V1 runtime, handoff, contract, loop, and evaluation fields produce explicit migration diagnostics.
- `policyflow --help` exposes only approved V2 commands.
- The package no longer imports or shells out to Codex.
- Core package no longer exposes runtime mutation APIs.
- `policyflow init` does not create runner config, prompts, agents, runtime state, large workflow template trees, provider adapters, or sync metadata.
- GitHub workflow performs read-only validation only.
- A clean consumer repository passes a V2 golden-path smoke test.
- Docs explain install, init, validate, PR validation, and doctor in less than ten minutes.

## Migration Posture

V2 is a breaking release. The implementation should provide bounded migration diagnostics and documentation, not preserve all V1 behavior.

No `policyflow migrate` command is included in the initial plan. It should be reconsidered only if real migration testing shows that diagnostics and docs are insufficient.

## Delivery Strategy

### Phase 1 - Foundation

Goal: establish the new architecture before deleting V1 behavior.

Expected work:

- final ADR.
- V2 schema.
- core models.
- core validation.
- migration diagnostics.

### Phase 2 - Core Cutover

Goal: make governance-only behavior the main product.

Expected work:

- public API cutover.
- CLI reduction.
- remove runtime mutation.
- remove runner execution.
- remove provider-specific code.
- simplify reporting.

### Phase 3 - Consumer Experience

Goal: rebuild adoption around the minimal V2 product.

Expected work:

- minimal init.
- simplified config.
- simplified doctor.
- read-only GitHub integration.
- asset source-of-truth cleanup.
- example cleanup.

### Phase 4 - Release

Goal: ship V2 as a deliberate breaking release.

Expected work:

- documentation rewrite.
- migration guide.
- release notes.
- packaging cleanup.
- final smoke tests.
- V2.0.0 release readiness.

## Dependencies

- ADR-0004 accepted.
- Existing V2 planning documents retained as design background.
- V2 schema must exist before CLI/API cutover.
- V2 validation tests must exist before runtime code is removed.
- Minimal init/config/doctor must exist before V2 docs are finalized.
- Package asset cleanup must happen before release readiness.

## Risks

- Existing V1 users may depend on runtime mutation or `run-phase`.
- Public API removals will break consumers importing runtime helpers.
- `policyflow.audit.v1` consumers need migration guidance.
- Removing asset sync changes upgrade behavior for bootstrapped repositories.
- External ownership for Codex/runner functionality must be resolved before deletion if the code remains valuable.

## Definition of Done

- ADR-0004 exists and is reflected in README and docs.
- V2 schema and validation are implemented and covered by tests.
- V1 migration diagnostics are implemented and documented.
- Runtime, runner, Codex, handoff, and agent execution ownership are removed from core.
- CLI is reduced to approved governance commands.
- Public API exposes governance APIs only.
- Minimal `init`, config, doctor, GitHub workflow, PR template, and examples are implemented.
- Package assets contain only V2 governance assets.
- V2 docs and migration guide are complete.
- Full test suite and V2 golden consumer smoke test pass.
- V2.0.0 release notes identify breaking changes and migration actions.

