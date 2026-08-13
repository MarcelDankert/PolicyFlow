# Runner Contract

PolicyFlow 2.0 does not own runner execution, provider adapters, prompt
management, or runtime state mutation.

External systems may still run agents, tools, tests, scans, and release jobs.
Those systems are responsible for their own runner configuration and output
contracts. PolicyFlow validates only the normalized governance evidence that
those systems publish into a repository workflow, PR body, or review metadata.

The previous in-core runner contract and Codex reference adapter were moved out
of PolicyFlow core. Do not depend on `policyflow run-phase`,
`policyflow.runners.yml`, or `python -m policyflow.codex_runner` in V2.

See [provider-neutral-integration-contract.md](provider-neutral-integration-contract.md)
for the evidence boundary external execution systems should satisfy.
Source path: `docs/provider-neutral-integration-contract.md`.
