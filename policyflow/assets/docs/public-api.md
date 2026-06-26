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

### Audit JSON Contract

`audit_workflows` and `policyflow audit --json` return the machine-readable
audit contract `policyflow.audit.v1` with `report_type: workflow_audit`.

The top-level payload includes:

- `schema_version`: currently `policyflow.audit.v1`
- `report_type`: currently `workflow_audit`
- `compatibility`: compatibility notes for downstream consumers
- `summary`: aggregate `workflow_governance`, `loop_governance`,
  `evaluation_governance`, and `human_governance` status counts
- `workflows`: per-workflow audit entries

The existing workflow audit fields remain present in each `workflows[]` entry,
including `path`, `workflow_id`, `risk_level`, `current_phase`,
`runtime_status`, `valid`, `merge_ready`, `loop_governance`, and `evaluation`.
Downstream consumers should treat new top-level keys as additive and continue
reading existing workflow-level fields during the `0.x` compatibility window.

New machine-readable per-workflow status groups are additive:

- `workflow_governance`: validation, merge-readiness, blocked state, and
  workflow-level errors
- `loop_governance`: declared loop count, loop status counts, and loop
  compliance errors
- `evaluation`: declared evaluation categories, metric counts, failed metrics,
  and evaluation errors
- `human_governance`: human approval requirement, approval evidence presence,
  missing approval evidence, and approval-related errors

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

## v2 Public API Expectations

PolicyFlow 2.x consumers should continue to use `policyflow` and `policyflow.api`
for supported integration code. Internal modules remain outside the compatibility boundary. They may change when implementation details move.

`WorkflowDocument` remains the normalized governance document returned by
validation helpers. It represents the canonical workflow, context, governance,
execution, evidence, contracts, overrides, runtime, handoff, loop governance,
and evaluation governance shape after compatibility normalization.

`validate_workflow`, `inspect_workflow`, and `validate_workflow_data` remain the
public validation entry points. `validate_pr_body` and
`validate_github_approvals` remain the public PR governance entry points.

`audit_workflows` remains the reporting entry point for `policyflow.audit.v1`.
Consumers that parse audit JSON should read `schema_version`, use documented
workflow, loop, evaluation, and human governance fields, and tolerate additive
fields unless a future release note declares a new schema version.

Runtime mutation helpers remain lightweight workflow-state helpers for
PolicyFlow-owned YAML fields. PolicyFlow validates and reports governance; it does not execute external systems, host runtimes, schedule agents, route messages, manage memory, manage provider credentials, approve pull requests, or replace Consumer-Repo CI and review systems.
