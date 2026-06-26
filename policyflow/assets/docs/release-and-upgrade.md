# Release And Upgrade Guidance

PolicyFlow consumers should install a pinned package version so workflow
validation, bootstrap assets, and GitHub checks use the same contract.

```bash
python -m pip install policyflow==0.4.0
```

Release links: [PyPI](https://pypi.org/project/policyflow/0.4.0/) and
[GitHub Release](https://github.com/MarcelDankert/PolicyFlow/releases/tag/v0.4.0).
Consumer-Repo automation should use the pinned package version.

Use the same version in local developer setup, CI, and Consumer-Repo automation.
Avoid installing from `main` for governed work because validator behavior and
bootstrap assets can change between commits.

## Release Channel

The public Consumer-Repo channel is the PyPI package named `policyflow`. The
current recommended pin is `policyflow==0.4.0`; each published package version
should have a matching GitHub Release named with the same tag, for example
`v0.4.0`.

Consumer-Repos should install from PyPI by version instead of cloning this
repository. The generated GitHub Actions governance workflow pins the same
package version through `POLICYFLOW_VERSION`:

```yaml
env:
  POLICYFLOW_VERSION: "0.4.0"
```

```bash
python -m pip install "policyflow==${POLICYFLOW_VERSION}"
```

Update this value in Consumer-Repo automation when adopting a newer PolicyFlow
release.

## Release Artifact Checklist

Before publishing release artifacts:

1. Confirm `pyproject.toml` and `policyflow.__version__` declare the same
   version.
2. Build the source distribution and wheel from a clean checkout.
3. Inspect the wheel contents and verify packaged assets include bootstrap,
   doctor, runner config, GitHub templates, workflow templates, prompts, rules,
   agents, examples, and docs.
4. Run release packaging tests and the full test suite.
5. Publish the package to PyPI.
6. Create the matching GitHub Release with release notes and the source
   distribution plus wheel attached or linked.
7. Document whether Consumer-Repos need to run `policyflow sync .`, update
   workflow files, or change schema/config versions.

The release artifacts are the PyPI source distribution, PyPI wheel, matching
GitHub Release notes, and the packaged managed assets contained in that wheel.

## Release Readiness Evidence

Use `evidence.release_readiness` when a release train needs an explicit,
reviewable status artifact before release execution. This artifact is
declarative governance evidence: it records ordering, blockers, missing
credentials, checks that could not run, and draft PR context. It does not make
PolicyFlow a release orchestrator or scheduler.

This design does not make PolicyFlow a release orchestrator or scheduler.

Recommended shape:

```yaml
evidence:
  release_readiness:
    state: preparatory
    state_values:
      - done
      - preparatory
      - blocked
      - ready_for_release
    release_blockers:
      - issue: "#42"
        reason: release artifact is not published yet
        state: blocked
    blocked_issues:
      - issue: "#43"
        blocked_by:
          - "#42"
        state: blocked
        reason: consumer validation requires the published artifact
    issue_ordering:
      - issue: "#42"
        before:
          - "#43"
        state: preparatory
    external_credentials_required:
      - name: PYPI_API_TOKEN
        reason: publish release artifact
        owner: release operator
    non_executable_checks:
      - check: consumer validation
        reason: package artifact is not available yet
        fallback: record as blocked until release artifact exists
    draft_prs:
      - pr: "#44"
        reason: stacked preview awaiting release artifact
        state: preparatory
```

Use the state values consistently:

- `done`: the issue, check, PR, or release preparation item is complete
- `preparatory`: work can be prepared, but it should not be treated as released
  or fully validated yet
- `blocked`: progress depends on an upstream issue, artifact, credential,
  external approval, or unavailable check
- `ready for release`: required artifacts, checks, credentials, and dependency
  ordering are satisfied for the declared release scope

Release readiness evidence should be updated by the release owner or workflow
author before claiming merge or release readiness. PolicyFlow can validate the
workflow structure around this evidence, but release execution, publication,
credential handling, and scheduling remain outside PolicyFlow.

## Upgrade Path

1. Pick the target PolicyFlow version from the release notes.
2. Update the local, CI, and GitHub Actions package pin to the same version.
3. Run `policyflow doctor .` in the Consumer-Repo.
4. Preview managed asset changes with `policyflow sync .`.
5. Review changed governance assets before overwriting existing Consumer-Repo
   files.
6. Use `policyflow sync . --apply` for safe managed asset updates.
7. Use `policyflow sync . --apply --force` only when the repo intentionally accepts
   overwriting locally modified managed assets with the packaged asset version.
8. Use `policyflow init . --force` only when the repo intentionally runs bootstrap
   again with the packaged asset version.
9. Revalidate active workflow files and PR bodies after the upgrade.

For v2 governance adoption, follow the dedicated migration guide at
[v2-migration-guide.md](v2-migration-guide.md). Source path:
`docs/v2-migration-guide.md`.

Recommended validation after changing the version pin:

```bash
policyflow validate ai/workflows/features/<workflow>.yml
policyflow validate-pr ai/workflows/features/<workflow>.yml pr-body.md
```

PolicyFlow sync reports unchanged, added, changed, locally modified, and removed
managed assets. It does not merge project-specific customizations. Consumer
repos remain responsible for reviewing local overlays before replacing managed
assets.

## Release Notes Expectations

Each PolicyFlow release should call out:

- validator schema changes
- workflow phase, evidence, contract, override, runtime, or handoff changes
- bootstrap asset additions, removals, or behavior changes
- GitHub issue template, PR template, and workflow changes
- runner configuration contract changes
- upgrade steps for Consumer-Repos
- known compatibility limits

Release notes must also state one of:

- no managed asset changes; no `policyflow sync .` action required
- managed asset changes available; run `policyflow sync .` to preview and
  `policyflow sync . --apply` to accept safe updates
- workflow/schema changes require explicit Consumer-Repo migration before
  adopting the release

## Compatibility Rules

PolicyFlow uses `policyflow.yml` `version: 1` for the current Consumer-Repo
configuration shape. A release that changes the expected config version,
workflow schema, bootstrap metadata, or runner result contract must document the
impact in release notes.

Workflow schema compatibility is defined in
[schema-compatibility.md](schema-compatibility.md). During the `0.x`
compatibility window, root-level fallback fields remain accepted by
`policyflow validate`, but new generated workflows and templates use the
canonical `context` and `governance` blocks. Release notes must call out any
schema compatibility change before stricter validation is introduced.

Patch releases should avoid breaking existing Consumer-Repo workflow files.
Minor releases may add optional fields or stricter validation when release notes
include the required Consumer-Repo update path. Breaking schema changes should
use a new config or workflow contract version.
