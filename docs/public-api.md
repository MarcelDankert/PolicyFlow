# Public Python API

PolicyFlow 2.0 exposes a governance-only public API through `policyflow` and
`policyflow.api`.

Internal modules remain outside the compatibility boundary. In particular,
runtime mutation, runner execution, reporting internals, asset synchronization,
workflow generation, and provider adapters are not public API.

For the provider-neutral evidence boundary used by external runtimes, CI
systems, and evidence producers, see
[provider-neutral-integration-contract.md](provider-neutral-integration-contract.md).
Source path: `docs/provider-neutral-integration-contract.md`.

## Stable Imports

Package root imports are supported:

```python
from policyflow import inspect_workflow_v2, validate_pr_body

result = inspect_workflow_v2("policyflow/change.yml")
validate_pr_body("workflows/features/change.yml", "pr-body.md")
```

The same functions are available from `policyflow.api`.

## Governance API

V1 compatibility validation:

- `inspect_workflow(path)`: returns `(WorkflowDocument, warnings)`.
- `validate_workflow(path)`: returns a validated `WorkflowDocument`.
- `validate_workflow_data(raw_data)`: validates an in-memory V1 workflow mapping.

V2 governance validation:

- `validate_workflow_v2(path)`: returns a validated `WorkflowDocumentV2`.
- `validate_workflow_v2_data(raw_data)`: validates an in-memory V2 governance
  mapping.
- `inspect_workflow_v2(path, allow_pending_human_approval=False)`: returns a
  `ValidationResultV2` with `PASS`, `WARN`, or `BLOCK`.
- `inspect_workflow_v2_data(raw_data, allow_pending_human_approval=False)`:
  returns a `ValidationResultV2` for an in-memory V2 mapping.

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
  "workflow": {},
  "errors": [],
  "warnings": []
}
```

`PASS` means governance is satisfied. `WARN` means the change is not merge-ready
but has a non-blocking governance condition, such as pending approval when that
state is explicitly allowed. `BLOCK` means governance is not satisfied.

Merge readiness is computed from governance policy, normalized evidence, and
override lifecycle only. It does not use runtime state, active agent state,
runner state, handoffs, loop iteration counters, evaluation metric values, or
metric calculation.

## Removed Public API

The following V1 helpers are removed from the public API:

- `get_workflow_status`
- `audit_workflows`
- `start_workflow_phase`
- `complete_workflow_phase`
- `block_workflow_phase`
- `record_workflow_handoff`

Consumers that used runtime mutation helpers should move execution and workflow
state handling to external runtimes or repository tooling.

runtime mutation helpers should move execution and workflow state handling to external runtimes.

Those systems may emit normalized evidence for PolicyFlow to validate.

Consumers that used audit/status helpers should use validation JSON output as
the V2 governance integration point.

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

## Compatibility Boundary

The public API follows the schemas described in
[schema-compatibility.md](schema-compatibility.md). Existing V1 workflow
validation remains available during this cutover, but new integrations should
target V2 governance validation and `policyflow.validation.v2`.
