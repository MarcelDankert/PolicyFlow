# Getting Started

## Consumer Quickstart

Use this path for a fresh Consumer-Repo. PolicyFlow 2.0 bootstraps a minimal
governance validator footprint: configuration, one V2 change example, and
optional read-only GitHub PR validation assets.

Install and pin PolicyFlow:

```bash
python -m pip install policyflow==2.0.1
```

Release links: [PyPI](https://pypi.org/project/policyflow/2.0.1/) and
[GitHub Release](https://github.com/MarcelDankert/PolicyFlow/releases/tag/v2.0.1).

Bootstrap with GitHub governance enabled:

```bash
policyflow init .
```

Bootstrap writes:

- `policyflow.yml`
- `policyflow/change.example.yml`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `.github/workflows/policyflow.yml`

Bootstrap without GitHub assets:

```bash
policyflow init . --no-github
```

The non-GitHub path writes only:

- `policyflow.yml`
- `policyflow/change.example.yml`

Preview or force bootstrap only when needed:

```bash
policyflow init . --dry-run
policyflow init . --force
```

Validate readiness:

```bash
policyflow doctor .
policyflow doctor . --json
```

Validate the example V2 change:

```bash
policyflow validate policyflow/change.example.yml
policyflow validate policyflow/change.example.yml --json
```

## Configuration

Default `policyflow.yml`:

```yaml
version: 2

paths:
  changes: policyflow
  pr_template: .github/PULL_REQUEST_TEMPLATE.md
  governance_workflow: .github/workflows/policyflow.yml

github:
  enabled: true
```

Local-only configuration:

```yaml
version: 2

github:
  enabled: false
```

## Change Schema

The generated `policyflow/change.example.yml` uses the V2 governance schema.
External systems execute implementation work, tests, scans, reviews, and release
steps. PolicyFlow starts after those systems publish governance evidence and
returns a validation decision.

## GitHub Governance

When `github.enabled: true`, the generated GitHub workflow uses read-only
`contents` and `pull-requests` permissions, fetches live PR body and review
metadata, and runs:

```bash
policyflow validate-pr "$workflow_path" pr-body.md --github-reviews pr-reviews.json --allow-pending
```

The workflow runs on `pull_request` and `pull_request_review` activity.

With `--allow-pending`, missing required human approval is reported as pending approval instead of a failed governance check; strict local or CI runs can omit `--allow-pending`.

Use GitHub required approving review rules to block merge while approval is pending.

For high-risk changes, set `governance.human_approval_required: true` and include approval evidence from the external review system in the V2 `evidence` list. PolicyFlow validates after external systems publish governance evidence.

For GitHub-backed V2 human approval evidence, use:

```yaml
evidence:
  - id: approval
    type: approval
    source: github-review:arch-board
    status: passed
    ref: https://github.com/example/repo/pull/1#pullrequestreview-99
```

`source` identifies the required approving GitHub login after
`github-review:`. `ref` must match the latest `APPROVED` review for that login
by GitHub review `id`, `url`, `html_url`, `node_id`, or `pull_request_url` in
the supplied `pr-reviews.json`. Pending approvals can use `status: pending` and
the pull request URL as `ref` until the approval review exists.

PolicyFlow does not create branches, create issues, mutate labels, assign milestones, approve pull requests, merge pull requests, or check credentials.

For a maintained static reference project, see `examples/reference-consumer`.
It demonstrates the minimal V2 layout, `policyflow doctor`, and V2 governance
schema validation without a hosted runtime, provider SDK, or provider
credentials.
