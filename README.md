# PolicyFlow

[![PolicyFlow Governance](https://github.com/MarcelDankert/PolicyFlow/actions/workflows/policyflow-governance.yml/badge.svg)](https://github.com/MarcelDankert/PolicyFlow/actions/workflows/policyflow-governance.yml)
[![PyPI](https://img.shields.io/pypi/v/policyflow.svg)](https://pypi.org/project/policyflow/)
[![Python](https://img.shields.io/pypi/pyversions/policyflow.svg)](https://pypi.org/project/policyflow/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Typed](https://img.shields.io/badge/typed-yes-brightgreen.svg)](pyproject.toml)

PolicyFlow 2.0 is a small provider-neutral policy-as-code governance validator
for AI-assisted software development.

PolicyFlow starts when a repository declares governance policy and evidence for
a software change. PolicyFlow ends when it returns a governance decision:
`PASS`, `WARN`, or `BLOCK`.

PolicyFlow validates governance. It does not execute work.

## Product Boundary

PolicyFlow answers governance questions:

- Is this change valid under repository governance policy?
- What risk level applies?
- Which reviews are required?
- Is human approval required?
- Is required evidence present?
- Are exceptions valid?
- Is the PR governance-ready?
- Is the change merge-ready from a governance perspective?

PolicyFlow does not own agent execution, runner configuration, prompt
management, provider adapters, model routing, scheduling, queues, memory,
workflow engines, test execution, security scan execution, metric calculation,
productivity analytics, issue creation, branch creation, PR creation, label or
milestone mutation, merge automation, or managed asset synchronization.

The final V2 boundary is defined in
[ADR-0004: PolicyFlow 2.0 Returns To Governance Core](docs/adr/0004-policyflow-v2-return-to-governance-core.md).

## Install

```bash
python -m pip install policyflow==2.0.0
```

Release target links: [PyPI](https://pypi.org/project/policyflow/2.0.0/) and
[GitHub Release](https://github.com/MarcelDankert/PolicyFlow/releases/tag/v2.0.0).

Developer install from a source checkout:

```bash
python -m pip install -e .[dev]
```

## CLI

The V2 CLI is intentionally small:

```bash
policyflow init .
policyflow validate policyflow/change.example.yml
policyflow validate-pr policyflow/change.example.yml pr-body.md
policyflow doctor .
```

Useful JSON paths:

```bash
policyflow validate policyflow/change.example.yml --json
policyflow validate-pr policyflow/change.example.yml pr-body.md --json
policyflow doctor . --json
```

Read-only GitHub review validation uses review JSON produced outside
PolicyFlow:

```bash
policyflow validate-pr policyflow/change.example.yml pr-body.md --github-reviews pr-reviews.json --allow-pending
```

Removed V1 commands include `new-workflow`, `sync`, `status`, `audit`,
`evaluation-report`, `loop-report`, runtime phase mutation commands, and the
standalone `validate-github-approvals` command.

## V2 Schema

New governance files use:

```yaml
version: 2

change:
  id: example-change
  type: feature
  summary: Example change.

risk:
  level: medium
  rationale: Example risk rationale.
  protected_areas: []

governance:
  required_reviews: []
  human_approval_required: false

confidence:
  level: medium
  summary: Example confidence summary.

evidence:
  - id: tests
    type: test
    source: ci
    status: passed
    ref: ci://example/tests

overrides: []
```

Every schema field must affect a governance decision. Runtime state, active
agents, runner status, handoff state, provider-specific fields, model-specific
fields, loop iteration state, and analytics values are not V2 governance input.

## Consumer Footprint

`policyflow init .` creates only:

- `policyflow.yml`
- `policyflow/change.example.yml`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `.github/workflows/policyflow.yml`

Use `policyflow init . --no-github` for local-only validation. That creates only
`policyflow.yml` and `policyflow/change.example.yml`.

PolicyFlow does not generate agents, prompts, runner configs, runtime state,
managed sync metadata, large workflow template trees, provider adapters, or
product-specific examples.

## GitHub Boundary

GitHub is an evidence source, not a PolicyFlow control plane.

The generated GitHub workflow uses read-only `contents` and `pull-requests`
permissions. It reads the PR body and review metadata, then runs
`policyflow validate-pr`.

PolicyFlow does not create branches, create issues, request reviews, approve
pull requests, mutate labels, assign milestones, merge pull requests, or check
provider credentials.

## Reporting

Reporting is validation output:

- human-readable diagnostics
- `policyflow.validation.v2` JSON
- `merge_ready`
- `merge_readiness.ready`
- `merge_readiness.explanation`
- `merge_readiness.blockers`

PolicyFlow does not provide productivity analytics, evaluation dashboards, loop
performance reports, model comparison, team performance metrics, or engineering
forecasting. See [docs/audit-reporting.md](docs/audit-reporting.md).

## Public API

Stable imports are documented in [docs/public-api.md](docs/public-api.md).
The public API is governance-only: V2 validation, PR body validation, and
read-only GitHub approval validation.

## Migration

V2 is a deliberate breaking release. Migration guidance:

- [docs/schema-compatibility.md](docs/schema-compatibility.md)
- [docs/v2-migration-guide.md](docs/v2-migration-guide.md)
- [docs/planning/policyflow-v1-v2-migration-matrix.md](docs/planning/policyflow-v1-v2-migration-matrix.md)
- [docs/release-and-upgrade.md](docs/release-and-upgrade.md)

V1 runtime, handoff, contract, loop, evaluation, audit, sync, workflow
generation, runner, agent, prompt, and provider-adapter responsibilities move
outside PolicyFlow core. External systems may produce normalized evidence that
PolicyFlow validates.

## Repository Guidance

See [AGENTS.md](AGENTS.md) for PolicyFlow repository guidance for Codex and
other coding agents working on this repository.

## Project Status

PolicyFlow `2.0.0` is prepared as the governance-core release target. Use
`python -m pip install policyflow==2.0.0` after the release is published.

## License

See [LICENSE](LICENSE).
