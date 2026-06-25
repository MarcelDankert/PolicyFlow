# Changelog

All notable PolicyFlow changes are tracked here. Release notes should call out
validator, workflow schema, bootstrap, runner, GitHub governance, and managed
asset compatibility changes.

## Unreleased

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
