# Metric Governance

Metric Governance explains how measurable quality signals support workflow,
loop, and evaluation governance without making PolicyFlow the system that
produces those signals.

PolicyFlow treats metrics as declarative governance claims. A Consumer-Repo can
declare which metric is expected, where the value comes from, which evidence
backs the value, and how PolicyFlow should validate the declaration. External
tools, reviewers, CI jobs, scanners, benchmarks, and domain systems remain
responsible for producing the underlying facts.

## Metric Governance Model

Metric Governance separates four concerns that should stay explicit in every
workflow:

- Metric declaration: the stable metric identifier, name, category, threshold,
  required flag, merge-blocking intent, and expected compliance status declared
  in the workflow.
- Metric source: the external system, reviewer, CI job, scanner, benchmark,
  domain service, or Consumer-Repo process that produced or will produce the
  metric value.
- Metric evidence: workflow evidence or provider-neutral artifact references
  that let a reviewer trace the metric value back to a concrete fact.
- PolicyFlow validation: structural and governance validation that checks the
  declaration, threshold comparison, required categories, evidence references,
  and risk-based requirements that PolicyFlow owns.

These concepts are related, but they are not interchangeable. A metric
declaration names the governance expectation. A metric source produces the
value. Metric evidence makes the value reviewable. PolicyFlow validation checks
whether the workflow's claims are internally consistent and aligned with the
declared risk path.

## PolicyFlow Responsibility

PolicyFlow validates metric governance metadata. It can check that:

- required metric fields exist
- required evaluation categories are present for the workflow risk level
- required metrics have evidence references
- non-pending `evidence.*` references point to existing workflow evidence
- simple thresholds such as `equals`, `greater_than_or_equal`, and
  `less_than_or_equal` are satisfied by declared values
- a passed evaluation does not hide failed required or merge-blocking metrics

PolicyFlow does not calculate all metrics. It does not run test suites,
coverage tools, SQL guardrails, security scanners, benchmark jobs, review
systems, or provider SDKs. Consumer-Repos own metric collection, artifact
storage, credential handling, provider configuration, and domain-specific
quality formulas.

## Evidence Relationship

Metric evidence should point to reviewable facts without embedding provider
logic in PolicyFlow.

Use workflow evidence references when the metric value is summarized in the
workflow:

```yaml
evidence_refs:
  - evidence.qa
  - evidence.review
```

Use provider-neutral artifact references when the value is backed by generated
output:

```yaml
evidence_refs:
  - artifact://test-report
  - artifact://coverage-report
  - artifact://querypilot-sql-guardrail-report
```

The evidence reference should help a reviewer answer: which external fact backs
this metric value, and which workflow phase accepted that evidence?

## Risk Relationship

Metrics strengthen risk governance when they make quality gates explicit before
implementation starts. LOW and MEDIUM risk workflows can use metrics to make
test, review, QA, or coverage expectations visible. HIGH risk workflows still
need the required human approval path; passing metrics do not replace approval
evidence.

Metric governance should be stricter when:

- a metric blocks merge readiness
- a metric is required by the risk level
- a metric represents protected-area, security, compliance, or release
  readiness evidence
- unresolved risks are declared as zero or waived

## Querypilot Metric Examples

Querypilot metric examples are described in
`docs/roadmap-agentic-governance.md` under the Querypilot pilot section.
Querypilot is a useful reference because natural-language requests can produce
SQL, and SQL output can be checked with concrete, provider-neutral signals.

Candidate Querypilot metric examples include:

- SQL guardrails passed
- only `SELECT` allowed
- generated SQL executable
- test pass rate
- coverage threshold
- response latency
- review score
- security findings

PolicyFlow should validate how those metrics are declared, referenced, and
reported. Querypilot or its Consumer-Repo automation should produce the metric
values and artifacts.

## Related Docs

- `docs/evaluation-governance.md`: evaluation schema, required metrics,
  thresholds, evidence references, and compliance status
- `docs/loop-governance.md`: feedback-loop declarations and evidence
  expectations
- `docs/roadmap-agentic-governance.md`: strategic positioning, v1.3 Metrics &
  Evidence milestone, and Querypilot pilot examples
