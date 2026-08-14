# Public Python API

PolicyFlow 2.0 exposes a governance-only public API through `policyflow` and
`policyflow.api`.

Internal modules remain outside the compatibility boundary. Runtime mutation,
runner execution, reporting internals, asset synchronization, workflow
generation, prompt management, provider adapters, and GitHub mutation are not
public API.

## Stable Imports

```python
from policyflow import (
    inspect_workflow_v2,
    validate_workflow_v2,
    validate_pr_body,
    validate_github_approvals,
)

result = inspect_workflow_v2("policyflow/change.yml")
workflow = validate_workflow_v2("policyflow/change.yml")
validate_pr_body("policyflow/change.yml", "pr-body.md")
validate_github_approvals(
    "policyflow/change.yml",
    "pr-body.md",
    "pr-reviews.json",
    allow_pending=True,
)
```

The same functions are available from `policyflow.api`.

## Governance API

V2 governance validation:

- `validate_workflow_v2(path)`: validates a V2 governance file and returns
  `WorkflowDocumentV2`.
- `validate_workflow_v2_data(raw_data)`: validates an in-memory V2 governance
  mapping.
- `inspect_workflow_v2(path, allow_pending_human_approval=False)`: returns
  `ValidationResultV2` with `PASS`, `WARN`, or `BLOCK`.
- `inspect_workflow_v2_data(raw_data, allow_pending_human_approval=False)`:
  returns `ValidationResultV2` for in-memory V2 data.

PR governance validation:

- `validate_pr_body(workflow_path, pr_body_path)`: validates PR body governance
  claims against the workflow.
- `validate_github_approvals(workflow_path, pr_body_path, reviews_path,
  allow_pending=False)`: validates declared human approvers against read-only
  GitHub review JSON.

Validation failures raise `WorkflowValidationError`.

## Validation Result

`ValidationResultV2.to_json_dict()` returns the machine-readable
`policyflow.validation.v2` contract:

```json
{
  "schema_version": "policyflow.validation.v2",
  "decision": "PASS",
  "merge_ready": true,
  "merge_readiness": {
    "ready": true,
    "explanation": "Governance validation passed with no blocking findings.",
    "blockers": []
  },
  "workflow": {},
  "errors": [],
  "warnings": []
}
```

`PASS` means governance is satisfied. `WARN` means governance is not
merge-ready but has a pending condition that callers explicitly allowed, such
as pending human approval. `BLOCK` means governance is not satisfied.

Merge readiness is computed from governance policy, normalized evidence,
approval state, and override lifecycle. It does not use runtime state, active
agent state, runner state, handoffs, loop iteration counters, evaluation metric
values, or metric calculation.

## V1 Compatibility Helpers

The package still exposes bounded V1 validation helpers during the 2.0.0
migration window:

- `inspect_workflow(path)`
- `validate_workflow(path)`
- `validate_workflow_data(raw_data)`

These helpers exist to support migration diagnostics and validation of existing
repositories. New integrations should target the V2 governance API.

## Removed Public API

The following V1 public helpers are removed:

- `get_workflow_status`
- `audit_workflows`
- `start_workflow_phase`
- `complete_workflow_phase`
- `block_workflow_phase`
- `record_workflow_handoff`
- runtime runner helpers
- managed asset sync helpers
- workflow generator helpers

Consumers that used runtime mutation helpers should move execution and workflow
state handling to external runtimes or repository tooling. Consumers that used
audit/status helpers should use `policyflow.validation.v2` JSON or external
report aggregation.

## CLI Boundary

The V2 CLI is intentionally small:

```text
policyflow init
policyflow validate
policyflow validate-pr
policyflow doctor
```

`validate-pr --github-reviews pr-reviews.json` is the read-only GitHub approval
validation path. PolicyFlow validates declared approvers; it does not request
reviews, approve PRs, label PRs, merge PRs, or mutate GitHub state.
