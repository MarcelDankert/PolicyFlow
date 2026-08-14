# Schema Compatibility

PolicyFlow 2.0 introduces a governance-only schema and treats older V1
workflow documents as migration input.

## V2 Governance Schema

```yaml
version: 2

change:
  id: example-change
  type: feature
  summary: Example change.

risk:
  level: medium
  rationale: Governance risk rationale.
  protected_areas: []

governance:
  required_reviews: []
  human_approval_required: false

confidence:
  level: medium
  summary: Confidence summary for the governance decision.

evidence:
  - id: tests
    type: test
    source: ci
    status: passed
    ref: ci://runs/123/tests

overrides: []
```

Field intent:

- `version`: selects the V2 governance schema.
- `change`: identifies the governed software change.
- `risk`: declares risk level, rationale, and protected areas.
- `governance`: declares required reviews and human approval requirements.
- `confidence`: explains confidence in the governance decision.
- `evidence`: records normalized evidence produced outside PolicyFlow.
- `overrides`: records governed exceptions with approval or lifecycle metadata.

Every field must affect a governance decision. Runtime state, active agents,
runner status, provider-specific fields, model-specific fields, handoff state,
current loop iteration state, metric values calculated by PolicyFlow, and
analytics data are not V2 governance input.

## Validation Result

V2 validation returns `policyflow.validation.v2`:

```json
{
  "schema_version": "policyflow.validation.v2",
  "decision": "PASS",
  "merge_ready": true,
  "merge_readiness": {
    "ready": true,
    "explanation": "Governance validation passed with no blocking findings.",
    "blockers": []
  },
  "workflow": {},
  "errors": [],
  "warnings": []
}
```

Decision semantics:

- `PASS`: governance is satisfied and the change is merge-ready from
  PolicyFlow's perspective.
- `WARN`: governance has a pending condition that callers explicitly allowed,
  such as pending human approval.
- `BLOCK`: governance is not satisfied because required evidence, approval, or
  override validity is missing or failed.

Merge readiness is derived from governance policy, normalized evidence, human
approval state, and override lifecycle. It is not derived from runtime state,
agent progress, runner output, loop iteration counters, dashboard metrics, or
provider state.

## Evidence Rules

Required evidence is based on governance:

- every change requires `type: test` evidence.
- required reviews require `type: review` evidence.
- medium and high risk changes require review evidence.
- high risk changes or protected-area changes require security evidence.
- human approval requires `type: approval` evidence.

Evidence is produced by CI, scanners, review systems, humans, or other external
systems. PolicyFlow validates that declared evidence exists and has a
governance-compatible status.

## Override Rules

Overrides remain governance data when they affect a decision. V2 overrides must
declare:

- stable `id`
- `type`
- `reason`
- governance impact
- mitigations
- lifecycle through exactly one of `review_by` or `expires_on`
- approval metadata for risk, approval, or evidence exceptions

Expired overrides block validation. Expiring overrides warn and make merge
readiness false until resolved.

## V1 Migration Diagnostics

V1 files produce bounded migration diagnostics. Diagnostics classify fields as:

- `KEEP`
- `RENAME`
- `MOVE`
- `REMOVE`
- `SIMPLIFY`

Important V1 classifications:

- `workflow`: rename to `change`.
- `context`: rebuild into `change`, `risk`, and `confidence`.
- `governance.required_reviews`: keep.
- `governance.human_approval_required`: keep.
- `governance.protected_areas_touched`: rename to `risk.protected_areas`.
- `governance.approval_evidence`: simplify into an approval evidence item.
- `execution`: remove from PolicyFlow governance input.
- `contracts`: move outside PolicyFlow or represent as external evidence.
- `runtime`: remove.
- `handoffs`: move outside PolicyFlow or represent as external evidence.
- `loop_governance`: move outside PolicyFlow core unless represented as
  normalized evidence.
- `evaluation`: simplify to normalized evidence.
- keyed V1 `evidence`: simplify to V2 `evidence[]`.
- `overrides`: keep as simplified governance exceptions.

See the full matrix in
[docs/planning/policyflow-v1-v2-migration-matrix.md](planning/policyflow-v1-v2-migration-matrix.md).

## Removed V1 Surface

The V2 core removes:

- `policyflow new-workflow`
- `policyflow sync`
- `policyflow status`
- `policyflow audit`
- `policyflow evaluation-report`
- `policyflow loop-report`
- runtime phase mutation commands
- standalone `validate-github-approvals`
- runner configuration
- agent and prompt assets
- workflow template trees
- GitHub issue templates
- managed asset sync metadata

Consumers should use `policyflow init`, `policyflow validate`,
`policyflow validate-pr`, `policyflow doctor`, and external execution systems
that emit normalized evidence.

## Compatibility Policy

PolicyFlow 2.0 is a deliberate breaking release. It does not promise indefinite
backwards compatibility for V1 runtime, handoff, audit, sync, workflow
generation, runner, agent, prompt, provider adapter, loop analytics, or
evaluation metric behavior.

The bounded migration posture is:

1. Document field decisions in the migration matrix.
2. Keep governance validation APIs stable.
3. Provide explicit validation errors and migration diagnostics.
4. Do not preserve removed runtime or analytics architecture in core.
