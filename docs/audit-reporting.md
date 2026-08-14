# Reporting Boundary

PolicyFlow 2.0 reports governance compliance from validation results. It does
not provide audit dashboards, loop reports, evaluation reports, productivity
analytics, model comparison, team metrics, or forecasting.

## Supported Output

Use validation output when a machine-readable compliance result is required:

```bash
policyflow validate policyflow/change.example.yml --json
policyflow validate-pr policyflow/change.example.yml pr-body.md --json
```

The V2 validation JSON includes:

- `decision`: `PASS`, `WARN`, or `BLOCK`
- `merge_ready`: boolean compatibility flag
- `merge_readiness.ready`: boolean merge-readiness value
- `merge_readiness.explanation`: human-readable compliance explanation
- `merge_readiness.blockers`: blocking findings or pending warnings
- `errors` and `warnings`: structured governance findings

## Removed Output

PolicyFlow 2.0 does not expose these core reporting commands:

- `policyflow status`
- `policyflow audit`
- `policyflow evaluation-report`
- `policyflow loop-report`

Consumers that previously parsed `policyflow.audit.v1` should migrate to V2
validation JSON and read `decision`, `merge_ready`, and `merge_readiness`.

## Runtime Boundary

Reporting explains compliance only. PolicyFlow does not execute workflows, run
loops, run evaluations, calculate metrics, approve pull requests, merge pull
requests, or mutate GitHub state.
