# Release And Upgrade Guidance

PolicyFlow consumers should install a pinned package version so workflow
validation, bootstrap assets, and GitHub checks use the same contract.

```bash
python -m pip install policyflow==0.1.0
```

Use the same version in local developer setup, CI, and Consumer-Repo automation.
Avoid installing from `main` for governed work because validator behavior and
bootstrap assets can change between commits.

## Upgrade Path

1. Pick the target PolicyFlow version from the release notes.
2. Update the local, CI, and GitHub Actions package pin to the same version.
3. Run `policyflow doctor .` in the Consumer-Repo.
4. Preview bootstrap asset changes with `policyflow init . --dry-run`.
5. Review changed governance assets before overwriting existing Consumer-Repo
   files.
6. Use `policyflow init . --force` only when the repo intentionally accepts the
   packaged asset version.
7. Revalidate active workflow files and PR bodies after the upgrade.

PolicyFlow does not currently provide automatic asset sync or migration tooling.
Consumer repos remain responsible for reviewing local overlays before replacing
managed assets.

## Release Notes Expectations

Each PolicyFlow release should call out:

- validator schema changes
- workflow phase, evidence, contract, override, runtime, or handoff changes
- bootstrap asset additions, removals, or behavior changes
- GitHub issue template, PR template, and workflow changes
- runner configuration contract changes
- upgrade steps for Consumer-Repos
- known compatibility limits

## Compatibility Rules

PolicyFlow uses `policyflow.yml` `version: 1` for the current Consumer-Repo
configuration shape. A release that changes the expected config version,
workflow schema, bootstrap metadata, or runner result contract must document the
impact in release notes.

Patch releases should avoid breaking existing Consumer-Repo workflow files.
Minor releases may add optional fields or stricter validation when release notes
include the required Consumer-Repo update path. Breaking schema changes should
use a new config or workflow contract version.
