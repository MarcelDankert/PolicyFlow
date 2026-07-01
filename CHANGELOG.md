# Changelog

All notable PolicyFlow changes are tracked here. Release notes should call out
validator, workflow schema, bootstrap, runner, GitHub governance, and managed
asset compatibility changes.

## Unreleased

## 1.0.0

Released: 2026-07-01

Agentic Governance Platform release.

- Stabilized the Agentic Governance Platform baseline across workflow,
  loop, evaluation, metric, human, audit, and reporting governance.
- Added v2 migration guidance, schema compatibility boundaries,
  provider-neutral integration expectations, and public API guidance for
  Consumer-Repos adopting the stable governance contract.
- Added maintained reference-consumer and Querypilot pilot documentation that
  demonstrate PolicyFlow as a governance layer without making it a runtime,
  scheduler, memory layer, provider SDK, or workflow engine.
- Kept existing 0.x root-level workflow fallback compatibility while making
  canonical `context` and `governance` fields the stable generated-workflow
  path.
- Updated README, release guidance, getting started docs, packaged docs, and
  Consumer-Repo GitHub governance workflow pins for `policyflow==1.0.0`.
- Validated the release through packaging checks, managed asset parity, example
  workflow validation, and the full test suite.

## 0.4.0

Released: 2026-06-26

Metrics, Evidence, Audit, and Reporting release.

- Added Metric Governance documentation for metric declarations, sources,
  evidence, validation boundaries, Querypilot-inspired examples, and
  Consumer-Repo ownership of metric collection.
- Added review and QA metric examples that show how Consumer-Repos can declare
  review score, test, coverage, security, performance, and domain metrics
  without making PolicyFlow calculate those metrics.
- Added audit governance summaries for workflow, loop, evaluation, and human
  governance across workflow directories.
- Added read-only evaluation compliance reporting with text and JSON output.
- Added read-only loop compliance reporting with text and JSON output.
- Stabilized the machine-readable audit JSON contract as
  `policyflow.audit.v1` with `workflow_governance`, `loop_governance`,
  `evaluation_governance`, and `human_governance` summary groups.
- Documented audit reporting usage for local and CI workflows, including the
  boundary that PolicyFlow reports declared governance state but does not
  execute workflows, run loops, calculate metrics, approve pull requests, host
  runtimes, schedule work, manage memory, or own provider credentials.
- Updated packaged managed docs and Consumer-Repo governance workflow pins so
  Consumer-Repos can adopt Metrics, Evidence, Audit, and Reporting through the
  PyPI package.

## 0.3.0

Released: 2026-06-25

Loop Governance Foundation release.

- Added optional top-level `loop_governance` workflow governance for declared
  feedback loops between workflow phases.
- Added typed Loop Governance models for loop identity, source and target
  phases, allowed feedback sources, iteration fields, stop conditions,
  escalation conditions, evidence references, and status.
- Added validator checks for positive `max_iterations`, current iteration
  limits, non-empty stop and escalation conditions, completed or terminated
  stop-condition evidence, and escalated loop evidence.
- Added provider-neutral Loop Governance examples covering review feedback, QA
  regression, security review, human arbitration, and Querypilot-inspired SQL
  safety loops.
- Documented Consumer-Repo Loop Governance usage, scope, non-scope, required
  fields, evidence, escalation expectations, examples, and runtime boundaries.
- Updated packaged managed docs, rules, workflow templates, and Consumer-Repo
  governance workflow pins so Consumer-Repos can adopt the Loop Governance
  Foundation through the PyPI package.

## 0.2.0

Released: 2026-06-25

Evaluation Governance Foundation release.

- Added optional top-level `evaluation` workflow governance for declared
  quality criteria, categories, required metrics, thresholds, evidence refs,
  and compliance status.
- Added typed Evaluation Governance models and schema normalization support.
- Added validator checks for risk-based evaluation categories, required metric
  consistency, blocking failures, duplicate IDs, and simple declared threshold
  comparisons.
- Added provider-neutral Evaluation Governance examples covering tests,
  coverage, review score, security findings, and performance gates.
- Added invalid evaluation fixtures for missing evidence refs and threshold
  mismatches.
- Documented Consumer-Repo Evaluation Governance usage, scope, non-scope,
  required fields, evidence, and examples.
- Updated packaged managed docs and workflow templates so Consumer-Repos can
  adopt the Evaluation Governance Foundation through the PyPI package.

## 0.1.1

Released: 2026-06-25

Consumer Governance Hardening release.

- Improved HIGH-risk approval diagnostics so missing `evidence.approval`
  fields produce actionable validation messages.
- Added GitHub App governance preflight support through `policyflow doctor`.
- Clarified approval evidence expectations in PR templates, README, and
  Consumer-Repo docs.
- Documented PR body rerun behavior plus draft and stacked PR merge-readiness
  semantics.
- Added optional `evidence.release_readiness` guidance for release blockers,
  blocked issues, issue ordering, external credentials, non-executable checks,
  and draft PR reasons.
- Updated packaged managed assets for Consumer-Repo adoption of the hardening
  release.

- Added public repository polish files for contributing, security reporting, and
  release history.
- Clarified that `policyflow==0.1.0` install commands are release-ready once the
  package is published.
- Added public package metadata for index and portfolio presentation.

## 0.1.0

Released: 2026-06-10

Initial public release.

- Bootstrap command for Consumer-Repos.
- Doctor readiness checks.
- Workflow generation, validation, status, audit, and PR governance validation.
- GitHub approval validation.
- Provider-neutral command runner contract and Codex reference adapter.
- Managed asset sync.
- Public Python API.
- Canonical workflow schema compatibility guidance.
