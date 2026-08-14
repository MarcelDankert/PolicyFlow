# PolicyFlow V2 Migration Guide

PolicyFlow 2.0 is a deliberate breaking release. It returns the product to a
small provider-neutral governance validator.

Use this guide with the full migration matrix:

- [policyflow-v1-v2-migration-matrix.md](planning/policyflow-v1-v2-migration-matrix.md)

## Migration Scope

V2 keeps:

- governance configuration
- risk rules
- required review validation
- human approval validation
- normalized evidence validation
- override validation
- PR body validation
- read-only GitHub review validation
- merge-readiness decisions

V2 removes PolicyFlow ownership of execution, orchestration, providers,
analytics, and managed asset synchronization.

## V1 To V2 Field Map

| V1 Field | V2 Decision | V2 Representation |
| --- | --- | --- |
| `context` | REBUILD | `change`, `risk`, `confidence` |
| `workflow` | RENAME | `change` |
| `governance.required_reviews` | KEEP | `governance.required_reviews` |
| `governance.human_approval_required` | KEEP | `governance.human_approval_required` |
| `governance.protected_areas_touched` | RENAME | `risk.protected_areas` |
| `governance.approval_evidence` | SIMPLIFY | `evidence[]` item with `type: approval` |
| `execution` | REMOVE | external workflow tooling |
| `contracts` | MOVE | external evidence or review system |
| `runtime` | REMOVE | external runtime state |
| `handoffs` | MOVE | external runtime or evidence system |
| `loop_governance` | REMOVE/MOVE | external loop governance or normalized evidence |
| `evaluation` | SIMPLIFY | normalized evidence |
| keyed V1 `evidence` | SIMPLIFY | V2 `evidence[]` |
| `overrides` | KEEP/SIMPLIFY | V2 `overrides[]` |

## V2 Target Shape

```yaml
version: 2

change:
  id: consumer-feature
  type: feature
  summary: Consumer-facing feature change.

risk:
  level: medium
  rationale: Changes user-visible behavior.
  protected_areas: []

governance:
  required_reviews:
    - review
  human_approval_required: false

confidence:
  level: medium
  summary: CI and review evidence are available.

evidence:
  - id: tests
    type: test
    source: ci
    status: passed
    ref: ci://runs/123
  - id: review
    type: review
    source: pull-request
    status: passed
    ref: pr://123/review

overrides: []
```

## Migration Steps

1. Upgrade local and CI pins to `policyflow==2.0.0`.
2. Run `policyflow init . --no-github` or `policyflow init .` in a clean branch
   to inspect the V2 consumer footprint.
3. Create or update `policyflow.yml` with `version: 2`.
4. Replace V1 workflow documents with V2 governance files under `policyflow/`.
5. Move risk and protected-area declarations into `risk`.
6. Move required reviews and human approval requirements into `governance`.
7. Convert test, review, security, approval, and exception artifacts into
   normalized `evidence[]` entries.
8. Convert valid governance exceptions into V2 `overrides[]`.
9. Move execution, runtime, handoff, loop execution, metric calculation,
   provider, runner, agent, and prompt responsibilities outside PolicyFlow.
10. Run `policyflow doctor .`.
11. Run `policyflow validate policyflow/<change>.yml --json`.
12. Run `policyflow validate-pr policyflow/<change>.yml pr-body.md`.

## Removed CLI Commands

Remove these commands from local scripts and CI:

- `policyflow new-workflow`
- `policyflow sync`
- `policyflow status`
- `policyflow audit`
- `policyflow evaluation-report`
- `policyflow loop-report`
- `policyflow run-phase`
- `policyflow start-phase`
- `policyflow complete-phase`
- `policyflow block-phase`
- `policyflow next-step`
- `policyflow handoff-status`
- `policyflow record-handoff`
- `policyflow validate-github-approvals`

New owners:

- scaffolding: repository templates or external project tooling
- execution: CI, local scripts, agent runtimes, or provider tools
- reporting aggregation: external compliance/reporting systems using validation
  JSON
- managed asset upgrades: release notes and normal repository review

## Removed Public API

Remove imports for:

- `get_workflow_status`
- `audit_workflows`
- phase mutation helpers
- handoff mutation helpers
- runner helpers
- sync helpers
- workflow generator helpers

Use `inspect_workflow_v2`, `validate_workflow_v2`, `validate_pr_body`, and
`validate_github_approvals`.

## Bootstrapped Consumer Repositories

Existing V1 bootstrapped repositories may contain:

- `ai/`
- `.policyflow/bootstrap.json`
- `policyflow.runners.yml`
- prompt assets
- agent assets
- rule assets
- workflow template trees
- GitHub issue templates

PolicyFlow 2.0 no longer manages or requires those files. Keep, migrate, or
delete them according to the consumer repository's own process. They are not
part of the V2 package asset source of truth.

## GitHub Migration

The generated V2 GitHub workflow is read-only. It reads the PR body and PR
reviews, then runs `policyflow validate-pr`.

PolicyFlow does not check GitHub mutation permissions and does not create
branches, issues, labels, milestones, PRs, approvals, or merges.

## Reporting Migration

Consumers parsing `policyflow.audit.v1` should move to
`policyflow.validation.v2` JSON:

```bash
policyflow validate policyflow/<change>.yml --json
policyflow validate-pr policyflow/<change>.yml pr-body.md --json
```

Read:

- `decision`
- `merge_ready`
- `merge_readiness.ready`
- `merge_readiness.explanation`
- `merge_readiness.blockers`
- `errors`
- `warnings`

PolicyFlow no longer owns audit dashboards, evaluation dashboards, loop
reports, productivity metrics, model comparison, team performance metrics, or
engineering forecasting.

## Migration Command

PolicyFlow 2.0 does not add `policyflow migrate`. The migration surface is
bounded documentation, diagnostics, and tests. A migration command should be
considered only if a future issue proves enough repeated migration work to
justify the maintenance cost.
