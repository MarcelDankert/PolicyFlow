# PolicyFlow Reference Consumer

This reference Consumer-Repo demonstrates the v2 governance adoption path
without a hosted runtime, provider SDK, or provider credentials.

Use it as a maintained example for:

- bootstrap layout expectations
- doctor readiness checks
- V2 governance schema validation

No hosted runtime is required. No provider credentials are required. Execution
systems stay outside PolicyFlow and publish normalized evidence for validation.

## Validation Path

From this directory, the reference path is intended to pass:

```bash
policyflow doctor . --json
policyflow validate policyflow/change.example.yml
```

## Boundary

The example models governance policy and evidence only. Consumer-Repos, CI
systems, agent frameworks, scanners, SQL guardrails, benchmark tools, and human
reviewers remain responsible for producing evidence. PolicyFlow validates the
declared governance state.

