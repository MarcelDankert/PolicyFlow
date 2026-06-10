# Public Python API

Consumer-Repos and integrations should import PolicyFlow through `policyflow`
or `policyflow.api`. Modules such as `policyflow.validator`,
`policyflow.runtime`, and `policyflow.reporting` remain internal implementation details and may change as long as the public API keeps its documented behavior.

## Stable Imports

Package root imports are supported:

```python
from policyflow import validate_workflow, get_workflow_status

workflow = validate_workflow("ai/workflows/features/first-feature.yml")
status = get_workflow_status("ai/workflows/features/first-feature.yml")
```

The same functions are available from `policyflow.api`:

```python
from policyflow.api import validate_pr_body, validate_github_approvals

validate_pr_body("ai/workflows/features/first-feature.yml", "pr-body.md")
validate_github_approvals(
    "ai/workflows/features/first-feature.yml",
    "pr-body.md",
    "pr-reviews.json",
)
```

## Validation API

- `inspect_workflow(path)`: returns `(WorkflowDocument, warnings)`
- `validate_workflow(path)`: returns a validated `WorkflowDocument`
- `validate_workflow_data(raw_data)`: validates an in-memory workflow mapping
- `validate_pr_body(workflow_path, pr_body_path)`: validates PR body governance
- `validate_github_approvals(workflow_path, pr_body_path, reviews_path)`: checks
  required GitHub approvals

Validation failures raise `WorkflowValidationError`.

## Reporting API

```python
from policyflow import audit_workflows, get_workflow_status

status = get_workflow_status("ai/workflows/features/first-feature.yml")
audit = audit_workflows("ai/workflows")
```

`get_workflow_status` returns the same status payload used by `policyflow
status --json`. `audit_workflows` returns the same audit payload used by
`policyflow audit --json`.

## Runtime Mutation API

```python
from policyflow import start_workflow_phase, record_workflow_handoff

start_workflow_phase("ai/workflows/features/first-feature.yml", "implementation")
record_workflow_handoff(
    "ai/workflows/features/first-feature.yml",
    "implementation",
    "review",
    required_inputs=["implementation_summary"],
    produced_outputs=["review_findings"],
)
```

Stable runtime helpers:

- `start_workflow_phase(path, phase)`
- `complete_workflow_phase(path, phase)`
- `block_workflow_phase(path, phase, reason)`
- `record_workflow_handoff(path, from_phase, to_phase, required_inputs,
  produced_outputs, blockers=None, override_refs=None)`

These helpers persist the workflow file after applying the same validation rules
as the CLI.

## Compatibility Boundary

The public API follows the canonical workflow schema described in
[schema-compatibility.md](schema-compatibility.md). Existing CLI commands keep
using the same service behavior as these public wrappers. Internal modules can
remain importable for tests and local development, but Consumer-Repos should not
treat internal module paths as the compatibility contract.
