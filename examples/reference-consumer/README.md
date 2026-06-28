# PolicyFlow Reference Consumer

This reference Consumer-Repo demonstrates the v2 governance adoption path
without a hosted runtime, provider SDK, or provider credentials.

Use it as a maintained example for:

- bootstrap layout expectations
- doctor readiness checks
- workflow validation
- loop governance declarations
- evaluation governance declarations
- audit reporting

No hosted runtime is required. No provider credentials are required. The runner
configuration uses a provider-neutral command shape and keeps actual execution
outside this reference path.

## Validation Path

From this directory, the reference path is intended to pass:

```bash
policyflow config-check policyflow.yml
policyflow doctor . --json
policyflow validate ai/workflows/features/v2-reference-governance.yml
policyflow audit ai/workflows --json
policyflow evaluation-report ai/workflows --json
policyflow loop-report ai/workflows --json
```

## Boundary

The example models governance state only. Consumer-Repos, CI systems, agent
frameworks, scanners, SQL guardrails, benchmark tools, and human reviewers
remain responsible for producing evidence. PolicyFlow validates and reports the
declared governance state.

