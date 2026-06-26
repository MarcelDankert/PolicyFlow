# Evaluation Governance

Evaluation Governance lets a Consumer-Repo declare measurable quality
expectations for agent-assisted delivery. It connects risk, evidence, and merge
readiness to concrete external signals such as test results, coverage, review
scores, security findings, and performance gates.

PolicyFlow records, validates, and reports declared evaluation governance.
CI, scanners, test tooling, benchmark tools, and human reviewers remain external
and remain responsible for producing the evidence.

## Scope

Evaluation Governance is in scope when a workflow needs reviewable quality
criteria beyond phase evidence alone:

- declare evaluation categories such as `tests`, `coverage`, `review`,
  `qa`, `security`, `performance`, or Consumer-Repo-specific domain categories
- declare required metrics, thresholds, actual values, status, evidence
  references, and merge-blocking intent
- validate declared evaluation metadata for internal consistency
- make evaluation compliance visible to reviewers and future reporting
- model failed, blocked, pending, passed, or waived evaluation states without
  requiring PolicyFlow to execute the underlying check

The `evaluation` block is optional for current `0.x` compatibility. When it is
declared, LOW and MEDIUM risk workflows must include a `tests` category. HIGH
risk workflows must include `tests` and `security` categories. Required
categories must include at least one metric marked `required: true`.

Metric compliance does not replace approval governance. HIGH-risk workflows
still require human approval even when all declared metrics pass.

## Non-Scope

Evaluation Governance does not make PolicyFlow an evaluation runner.

PolicyFlow does not:

- run test suites
- call security scanners
- calculate coverage
- execute benchmark tooling
- assign human review scores
- fetch provider artifacts
- manage provider credentials
- schedule recurring evaluations
- decide domain-specific metric formulas

Consumer-Repos own their tooling, artifact storage, provider configuration, and
domain-specific quality calculations.

## Required Fields

Declare Evaluation Governance as a top-level `evaluation` block:

```yaml
evaluation:
  compliance_status: pending
  categories:
    - id: tests
      required_metrics:
        - id: tests-passed
          name: Test suite pass status
          source: external-test-runner
          required: true
          thresholds:
            operator: equals
            value: passed
          actual_value: pending
          status: pending
          evidence_refs:
            - evidence.qa
            - artifact://test-report
          blocks_merge: true
```

Required fields:

- `evaluation.compliance_status`: overall claim, using `pending`, `passed`,
  `failed`, `blocked`, or `waived`
- `categories[].id`: stable category identifier
- `categories[].required_metrics[]`: one or more metric declarations
- `required_metrics[].id`: stable metric identifier within the category
- `required_metrics[].name`: human-readable metric name
- `required_metrics[].category`: optional metric-level category metadata for
  reusable or domain-specific metrics. If omitted, the parent `categories[].id`
  is the metric category.
- `required_metrics[].source`: external source that produced or will produce the
  value
- `required_metrics[].required`: whether the metric is required for the
  evaluation category
- `required_metrics[].thresholds.operator`: provider-neutral comparison rule
- `required_metrics[].thresholds.value`: expected threshold value
- `required_metrics[].actual_value`: observed value supplied by external
  evidence, CI, review, scanner, benchmark, or domain tooling
- `required_metrics[].status`: metric status, using the same status vocabulary
  as the overall compliance claim
- `required_metrics[].evidence_refs`: references to workflow evidence or
  external artifacts
- `required_metrics[].blocks_merge`: whether a failed or blocked metric should
  prevent merge readiness

Supported simple threshold operators are `equals`, `greater_than_or_equal`, and
`less_than_or_equal`. Unknown operators remain declarative metadata until a
future schema decision defines their behavior.

## Evidence

Evaluation evidence should point to external facts without embedding provider
logic in PolicyFlow.

Use `evidence.*` references when the workflow already records the relevant
phase evidence:

```yaml
evidence_refs:
  - evidence.qa
  - evidence.review
```

Consumer-Repos own the evidence lifecycle. PolicyFlow validates declarations and
references, but it does not create test reports, scanner output, benchmark
results, review scores, or domain-specific measurement artifacts.

For required metrics with a non-`pending` status, references that use the
`evidence.*` form must point to an existing workflow evidence block. For
example, a required metric with `status: passed` and `evidence_refs:
["evidence.qa"]` requires an `evidence.qa` block in the workflow. Pending
metrics may reference future workflow evidence while work is still in progress.

Use provider-neutral artifact references for generated outputs:

```yaml
evidence_refs:
  - artifact://test-report
  - artifact://coverage-report
  - artifact://security-report
  - artifact://performance-report
```

These references are reviewable pointers. PolicyFlow validates that the
references are declared; it does not fetch, execute, or recalculate them.
External artifact identifiers remain provider-neutral and are not fetched or
authenticated by PolicyFlow.

## Examples

The canonical example workflow is
`workflows/examples/evaluation-governance-workflow.yml`.

It demonstrates:

- `tests`: external test result with `equals passed`
- `tests`: external test pass rate with `greater_than_or_equal 95`
- `qa`: QA pass status with `equals passed`
- `qa`: unresolved risk count with `equals 0`
- `coverage`: coverage percentage with `greater_than_or_equal 80`
- `review`: human review score with `greater_than_or_equal 4`
- `security`: critical findings with `equals 0`
- `performance`: p95 latency with `less_than_or_equal 250`

Fixture examples live under `tests/fixtures/`:

- `evaluation-metrics-compliant.yml`: provider-neutral review and QA metrics
  that satisfy their declared thresholds
- `evaluation-metrics-non-compliant.yml`: unresolved QA risk count above the
  declared threshold

- `evaluation-missing-evidence-refs.yml`: required metric evidence is missing
- `evaluation-threshold-mismatch.yml`: a declared passed metric does not satisfy
  its threshold

For schema-level compatibility details, see
`docs/schema-compatibility.md`.
