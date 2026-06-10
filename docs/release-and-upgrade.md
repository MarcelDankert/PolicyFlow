# Release And Upgrade Guidance

PolicyFlow consumers should install a pinned package version so workflow
validation, bootstrap assets, and GitHub checks use the same contract.

```bash
python -m pip install policyflow==0.1.0
```

Use this command once `policyflow==0.1.0` is published. Until then, install from
the PolicyFlow checkout for local evaluation and keep Consumer-Repo automation
pointed at the pinned release path only after publication.

Use the same version in local developer setup, CI, and Consumer-Repo automation.
Avoid installing from `main` for governed work because validator behavior and
bootstrap assets can change between commits.

## Release Channel

The initial public Consumer-Repo channel is the PyPI package named
`policyflow`, starting with `policyflow==0.1.0`. Each published package version
should have a matching GitHub Release named with the same tag, for example
`v0.1.0`.

Consumer-Repos should install from PyPI by version instead of cloning this
repository. The generated GitHub Actions governance workflow pins the same
package version through `POLICYFLOW_VERSION`:

```yaml
env:
  POLICYFLOW_VERSION: "0.1.0"
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
