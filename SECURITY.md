# Security Policy

PolicyFlow is a public governance framework repository. Please report security
issues responsibly and avoid publishing exploit details before the issue is
triaged.

## Supported Versions

Security fixes target the latest released version and the current `main` branch.
Until the first public package release is published, reports apply to `main`.

## Reporting A Vulnerability

If you find a vulnerability, open a private security advisory on GitHub or
contact the repository owner through GitHub. Include:

- affected version or commit
- impacted command, workflow, or packaged asset
- reproduction steps
- expected impact
- any known mitigation

Do not include tokens, private keys, local machine paths, or secrets in reports.

## Scope

In scope:

- unsafe handling of workflow, PR, review, runner, or bootstrap data
- packaged asset behavior that could mislead Consumer-Repos into unsafe setup
- command behavior that exposes secrets or bypasses governance checks

Out of scope:

- missing provider credentials in a local Consumer-Repo
- intentionally disabled Consumer-Repo governance features
- social engineering or attacks on external providers
