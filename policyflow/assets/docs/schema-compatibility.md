# Workflow Schema Compatibility

PolicyFlow workflows have one canonical schema for new Consumer-Repo workflow
files. Validators still accept a small set of root-level fallback fields during
the `0.x` compatibility window so existing early adopters can upgrade without a
breaking migration. This is the 0.x compatibility window for legacy workflow
instances.

## Canonical Workflow Schema

New generated workflows must use the canonical schema:

- `workflow`: workflow identity and type metadata
- `context.workflow_file`: path to the workflow file referenced by PR checks
- `context.risk_level`: `LOW`, `MEDIUM`, or `HIGH`
- `context.confidence`: planning, implementation, tests, and residual
  uncertainty summary
- `governance.required_reviews`: review roles required by risk
- `governance.human_approval_required`: whether approval evidence is required
- `governance.escalation_required`: whether protected-area escalation is required
- `governance.protected_areas_touched`: protected areas or `[none]`
- `governance.approval_evidence`: required for approval-gated workflows
- `execution`: strict phase list and current phase states
- `evidence`: machine-readable phase evidence
- `contracts`: machine-readable role contracts for completed canonical phases
- `evaluation`: optional declarative evaluation governance criteria
- `overrides`: typed approved exceptions
- `runtime`: current orchestration state
- `handoffs`: concrete phase handoffs

## Evaluation Governance Schema

Evaluation Governance is an optional top-level workflow block that declares
measurable quality criteria and the evidence that supports them. PolicyFlow does not run evaluation tooling, execute tests, call scanners, calculate benchmark
scores, or own provider credentials. Consumer-Repos, CI systems, review tools,
security scanners, benchmark tools, and human reviewers remain responsible for
producing the evidence.

Initial schema shape:

```yaml
evaluation:
  compliance_status: pending
  categories:
    - id: tests
      required_metrics:
        - id: tests-passed
          name: Test suite pass status
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
    - id: coverage
      required_metrics:
        - id: coverage-percent
          name: Coverage percentage
          source: ci
          required: false
          thresholds:
            operator: greater_than_or_equal
            value: "80"
          actual_value: pending
          status: pending
          evidence_refs:
            - ci://coverage/report
          blocks_merge: false
```

Field intent:

- `evaluation.compliance_status`: overall evaluation state such as `pending`,
  `passed`, `failed`, `blocked`, or `waived`
- `categories`: evaluation groups such as `tests`, `coverage`, `review`,
  `security`, `performance`, or Consumer-Repo-specific domain categories
- `required_metrics`: concrete measured checks required for that category
- `thresholds`: expected value or comparison rule for a metric
- `evidence_refs`: references to workflow evidence, CI artifacts, review
  records, scanner reports, benchmark output, or domain-specific evidence
- `blocks_merge`: whether the metric is intended to block merge readiness when
  not compliant

Validation behavior:

- The `evaluation` block is optional for current 0.x compatibility.
- When `evaluation` is declared, MEDIUM risk workflows must include a `tests`
  category and HIGH risk workflows must include `tests` and `security`
  categories. Each required category must contain at least one metric marked
  `required: true`.
- Category IDs and metric IDs within a category must be unique.
- `compliance_status: passed` requires all metrics marked `required: true` to
  have `status: passed` or `status: waived`, and cannot include failed or
  blocked metrics with `blocks_merge: true`.
- Metrics with `status: passed` and a declared `actual_value` must satisfy
  simple provider-neutral thresholds for `equals`, `greater_than_or_equal`, and
  `less_than_or_equal`.
- `failed`, `blocked`, `pending`, and `waived` can be modeled as declared
  governance states without implying that PolicyFlow executed the underlying
  check.

PolicyFlow should not execute evaluation tooling. This schema only records the
required criteria, thresholds, evidence references, and compliance status so
later validation and reporting can reason about evaluation governance.

`policyflow new-workflow`, workflow templates, bootstrap-managed templates, PR
validation, status, audit, sync, and the future `policyflow.api` compatibility
boundary all treat this canonical shape as the stable integration target.

## Legacy Root-Level Fallbacks

The validator currently accepts these root-level fallback fields when the
canonical `context` or `governance` blocks do not provide them:

- `workflow_file`
- `risk_level`
- `confidence`
- `required_reviews`
- `human_approval_required`
- `escalation_required`
- `protected_areas_touched`
- `approval_evidence`

These root-level fallback fields are legacy compatibility only: new generated workflows must use the canonical schema. Consumer-Repos should migrate fallback
workflows by moving those fields into `context` and `governance` while leaving
`execution`, `evidence`, `contracts`, `overrides`, `runtime`, and `handoffs` at
their canonical top-level locations.

## Compatibility Policy

During the `0.x` compatibility window:

- `policyflow validate` accepts canonical workflows and root-level fallback
  workflows.
- `policyflow new-workflow` emits canonical workflows only.
- Bootstrapped workflow templates use canonical `context`, `governance`,
  `execution`, `evidence`, `contracts`, `overrides`, `runtime`, and `handoffs`
  blocks.
- `policyflow validate-pr` compares PR claims against canonical fields after
  normalization.
- `policyflow sync .` may deliver canonical template updates, but it does not
  rewrite Consumer-Repo workflow instances.
- Public integrations should target the canonical schema contract through the
  stable imports documented in [public-api.md](public-api.md).

Removing root-level fallback support requires a release note, a migration
checklist, and tests that prove the planned failure messages before the release
can ship.

## Migration Steps

For each legacy workflow:

1. Run `policyflow validate <workflow.yml>` to confirm the current file is still
   accepted.
2. Move `workflow_file`, `risk_level`, and `confidence` under `context`.
3. Move `required_reviews`, `human_approval_required`, `escalation_required`,
   `protected_areas_touched`, and `approval_evidence` under `governance`.
4. Leave `execution`, `evidence`, `contracts`, `overrides`, `runtime`, and
   `handoffs` in their canonical top-level blocks.
5. Run `policyflow validate <workflow.yml>` again.
6. Run `policyflow validate-pr <workflow.yml> pr-body.md` for active PRs.
7. Preview managed template updates with `policyflow sync .`.

## Component Expectations

- Validators normalize legacy fallback fields before building the workflow
  document.
- Templates and `policyflow new-workflow` emit canonical schema only.
- Bootstrap copies canonical templates and does not create legacy fallback
  workflow instances.
- PR validation, GitHub approval validation, status, audit, runtime mutation, and
  runner execution consume the normalized workflow document.
- Release notes must call out schema compatibility changes and any required
  Consumer-Repo migration before stricter validation is introduced.
