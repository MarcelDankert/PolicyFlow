# PolicyFlow v2 Migration Guide

This guide helps Consumer-Repos migrate from early `0.x` workflow shapes to the
stable v2 governance contract. It is an adoption guide, not a runtime upgrade
engine: PolicyFlow does not execute workflows, schedule agents, own provider
credentials, merge pull requests, or replace CI and review systems.

## Migration Scope

The v2 migration covers these governance contracts:

- Workflow Governance: canonical workflow identity, `context`, `governance`,
  phases, evidence, contracts, runtime state, and handoffs.
- Loop Governance: declared feedback-loop rules, bounded iteration state, stop
  conditions, escalation conditions, and evidence references.
- Evaluation And Metric Governance: declared evaluation categories, required
  metrics, thresholds, observed values, status, and merge-blocking intent.
- Human Governance: explicit approval, escalation, override, and arbitration
  evidence for governed work.
- Audit Integration: read-only `policyflow.audit.v1` reporting for workflow,
  loop, evaluation, and human governance summaries.

The migration does not remove `0.x` fallback support by itself. Removing
fallback support requires a separate release decision, release notes, tests, and
consumer-facing migration checklist.

## Deprecated 0.x Fallbacks

The current compatibility window still accepts selected root-level fallback
fields when canonical blocks are missing. New workflow files should not use
these fallback fields:

- `workflow_file`
- `risk_level`
- `confidence`
- `required_reviews`
- `human_approval_required`
- `escalation_required`
- `protected_areas_touched`
- `approval_evidence`

Treat these fields as legacy input compatibility only. New v2 workflow
instances should use canonical `context` and `governance` blocks.

## Workflow Governance Migration

Move workflow identity and risk context into `context`, and move review,
approval, escalation, and protected-area rules into `governance`.

Before:

```yaml
workflow:
  id: consumer-feature
  name: Consumer Feature
  type: feature

workflow_file: ai/workflows/features/consumer-feature.yml
risk_level: MEDIUM
confidence:
  planning: Goal and scope are understood.
  implementation: Existing module boundaries are clear.
  tests: Unit and governance checks are available.
  residual_uncertainty: No known release blocker.
required_reviews:
  - review-agent
human_approval_required: false
escalation_required: false
protected_areas_touched:
  - none
```

After:

```yaml
workflow:
  id: consumer-feature
  name: Consumer Feature
  type: feature

context:
  workflow_file: ai/workflows/features/consumer-feature.yml
  risk_level: MEDIUM
  confidence:
    planning: Goal and scope are understood.
    implementation: Existing module boundaries are clear.
    tests: Unit and governance checks are available.
    residual_uncertainty: No known release blocker.

governance:
  required_reviews:
    - review-agent
  human_approval_required: false
  escalation_required: false
  protected_areas_touched:
    - none
```

Keep `execution`, `evidence`, `contracts`, `overrides`, `runtime`, and
`handoffs` at their canonical top-level locations.

## Loop Governance Migration

Add `loop_governance` when a workflow has governed feedback loops between
phases. PolicyFlow validates and reports declared loop governance; it does not
run the loop or route feedback.

Before:

```yaml
evidence:
  review:
    status: changes_requested
    summary: Review feedback must be resolved before QA.
```

After:

```yaml
loop_governance:
  loops:
    - id: review-feedback
      source_phase: review
      target_phase: implementation
      allowed_feedback_sources:
        - review-findings
        - qa-findings
      max_iterations: 3
      current_iteration: 1
      status: active
      stop_conditions:
        - id: review-findings-resolved
          description: All blocking review findings are resolved.
      escalation_conditions:
        - id: iteration-limit-reached
          trigger: max_iterations_exceeded
          escalate_to: human-arbitration
      evidence_refs:
        - evidence.review
```

Use loop governance when a Consumer-Repo needs explicit limits, stop criteria,
or escalation criteria for repeated agent or reviewer feedback.

## Evaluation And Metric Migration

Add `evaluation` when a workflow declares quality criteria that must be
reported or validated before merge readiness. Consumer-Repos remain responsible
for running tests, scanners, benchmarks, and domain evaluations.

Before:

```yaml
evidence:
  qa:
    tests:
      - pytest -q
```

After:

```yaml
evaluation:
  compliance_status: pending
  categories:
    - id: tests
      required_metrics:
        - id: tests-passed
          name: Test suite pass status
          category: tests
          source: ci
          required: true
          thresholds:
            operator: equals
            value: passed
          actual_value: pending
          status: pending
          evidence_refs:
            - evidence.qa
          blocks_merge: true
```

For HIGH-risk workflows that declare Evaluation Governance, include the
risk-required categories and at least one required metric per required category.
Metric Governance lives inside `evaluation.required_metrics`; PolicyFlow
validates declarations and evidence references, but it does not calculate all
metrics.

## Human Governance Migration

For approval-gated workflows, `governance.approval_evidence is not sufficient`
by itself. It declares which evidence path must exist. The workflow must also
provide the actual `evidence.approval` object and the PR body must reference it.

Before:

```yaml
governance:
  human_approval_required: true
  approval_evidence:
    - evidence.approval
```

After:

```yaml
governance:
  human_approval_required: true
  approval_evidence:
    - evidence.approval

evidence:
  approval:
    approved_by: MarcelDankert
    reference: PR approval required before merge
    scope_confirmed: true
```

Human approval evidence records the declared approval claim. It does not replace
the actual GitHub review or organizational approval rule.

## Audit Integration Migration

Consumers that read audit output should target `policyflow.audit.v1` and read
`schema_version` before interpreting the payload.

```json
{
  "schema_version": "policyflow.audit.v1",
  "summary": {
    "workflow_governance": {},
    "loop_governance": {},
    "evaluation_governance": {},
    "human_governance": {}
  }
}
```

Treat new top-level and per-workflow audit fields as additive unless a future
release note declares a breaking audit contract. Audit JSON remains a reporting
contract: it does not execute workflows, fetch external artifacts, approve PRs,
or manage credentials.

## Validation Checklist

Use this checklist when upgrading a Consumer-Repo:

1. Pin the target package version in local setup, CI, and GitHub Actions.
2. Run `policyflow doctor .` to inspect the Consumer-Repo setup.
3. Run `policyflow sync .` to preview managed asset updates.
4. Move deprecated root-level fallback fields into `context` and `governance`.
5. Add `loop_governance` for declared feedback loops that need stop conditions,
   escalation_conditions, and `evidence_refs`.
6. Add `evaluation` for declared quality gates and required_metrics.
7. Add `evidence.approval` for approval-gated workflows.
8. Run `policyflow validate ai/workflows/features/<workflow>.yml`.
9. Run `policyflow validate-pr ai/workflows/features/<workflow>.yml pr-body.md`
   for active pull requests.
10. Run `policyflow audit ai/workflows --json` for audit integrations.
11. Run `policyflow evaluation-report ai/workflows --json` when downstream
    reporting depends on Evaluation Governance.
12. Run `policyflow loop-report ai/workflows --json` when downstream reporting
    depends on Loop Governance.
13. Review release notes before removing any Consumer-Repo fallback usage.

