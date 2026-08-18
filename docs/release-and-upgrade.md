# Release And Upgrade Guidance

PolicyFlow 2.0 is the governance-core breaking release.

Consumer repositories should install a pinned package version:

```bash
python -m pip install policyflow==2.0.1
```

Release target links: [PyPI](https://pypi.org/project/policyflow/2.0.1/) and
[GitHub Release](https://github.com/MarcelDankert/PolicyFlow/releases/tag/v2.0.1).

## Release Channel

The public Consumer-Repo channel is the PyPI package named `policyflow`.
Consumer-Repos should install from PyPI by version instead of cloning this
repository.

Generated GitHub Actions governance workflows pin the package version through
`POLICYFLOW_VERSION`:

```yaml
env:
  POLICYFLOW_VERSION: "2.0.1"
```

```bash
python -m pip install "policyflow==${POLICYFLOW_VERSION}"
```

## 2.0.1 Release Artifact Checklist

Before publishing 2.0.1:

1. Confirm `pyproject.toml` and `policyflow.__version__` both declare
   `2.0.1`.
2. Build the source distribution and wheel from a clean checkout.
3. Inspect the wheel contents and verify packaged assets contain only:
   `assets/github/*.md`, `assets/github/workflows/*.yml`,
   `assets/examples/*.yml`, and `assets/docs/getting-started.md`.
4. Confirm the wheel excludes agents, prompts, rules, runner assets, provider
   adapters, workflow template trees, GitHub issue templates, managed sync
   metadata, and broad packaged docs.
5. Run the V2 golden consumer smoke test.
6. Run the full test suite.
7. Validate the active release workflow.
8. Publish the package to PyPI.
9. Create the matching GitHub Release `v2.0.1`.

The release artifacts are the PyPI source distribution, PyPI wheel, matching
GitHub Release notes, and the minimal packaged V2 governance assets.

## Breaking Changes

PolicyFlow 2.0 removes:

- `policyflow new-workflow`
- `policyflow sync`
- `policyflow status`
- `policyflow audit`
- `policyflow evaluation-report`
- `policyflow loop-report`
- runtime phase mutation commands
- standalone `validate-github-approvals`
- runtime, runner, Codex adapter, sync, reporting, and workflow generator
  modules
- packaged agents, prompts, rules, workflow templates, GitHub issue templates,
  project context example, and broad packaged docs
- V1 runtime, handoff, loop state, evaluation metric, audit, and managed sync
  ownership from core

External systems own execution, orchestration, runner configuration, prompt
management, provider adapters, model routing, queues, scheduling, memory,
message routing, test execution, security scan execution, metric calculation,
analytics, issue creation, branch creation, PR creation, label and milestone
mutation, approvals, and merges.

## Upgrade Path

1. Read [v2-migration-guide.md](v2-migration-guide.md).
2. Review the full migration matrix:
   [policyflow-v1-v2-migration-matrix.md](planning/policyflow-v1-v2-migration-matrix.md).
3. Update local, CI, and GitHub Actions pins to `policyflow==2.0.1`.
4. Replace V1 workflow files with V2 governance files under `policyflow/`.
5. Move execution, runtime, handoff, loop execution, metric calculation,
   provider, runner, agent, and prompt responsibilities outside PolicyFlow.
6. Run `policyflow doctor .`.
7. Run `policyflow validate policyflow/<change>.yml --json`.
8. Run `policyflow validate-pr policyflow/<change>.yml pr-body.md`.

PolicyFlow 2.0 does not provide managed asset sync. Use ordinary repository
review to adopt changed templates or generated files.

## Release Readiness Evidence

Release readiness evidence remains declarative. It can record release blockers,
blocked issues, issue ordering, external credentials required by release
operators, non-executable checks, and draft PR context. It does not make
PolicyFlow a release orchestrator or scheduler.

Example:

```yaml
evidence:
  release_readiness:
    state: ready_for_release
    state_values:
      - done
      - preparatory
      - blocked
      - ready_for_release
    release_blockers: []
    blocked_issues: []
    issue_ordering:
      - issue: "#150"
        before:
          - v2.0.1
        state: done
    external_credentials_required:
      - name: PYPI_API_TOKEN
        reason: publish release artifact
        owner: release operator
    non_executable_checks: []
    draft_prs: []
```

Use the state values consistently:

- `done`: the issue, check, PR, or release preparation item is complete.
- `preparatory`: work can be prepared, but it is not released yet.
- `blocked`: progress depends on an upstream issue, artifact, credential,
  external approval, or unavailable check.
- `ready for release`: required artifacts, checks, credentials, and dependency
  ordering are satisfied for the declared release scope.

## Release Notes Expectations

2.0.1 release notes must include:

- V2 `validate-pr --github-reviews` approval validation behavior
- V2 GitHub approval evidence convention
- V1 compatibility statement
- package, documentation, and generated workflow pin updates
- test and package build results

2.0.0 breaking release notes must include:

- removed commands
- removed public API symbols
- removed schema fields and V1 field decisions
- removed package assets
- GitHub read-only boundary
- reporting migration from `policyflow.audit.v1` to validation JSON
- external ownership guidance for execution, runners, prompts, agents,
  providers, analytics, and GitHub mutation
- V2 golden consumer smoke test result
- full test suite result

Patch releases after 2.0.1 should preserve V2 governance API compatibility.
Breaking governance schema changes require a new migration note and release
decision.
