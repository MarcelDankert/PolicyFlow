# Audit Reporting

PolicyFlow audit reporting gives Consumer-Repos a read-only view of declared
governance state across workflow files. It helps reviewers, maintainers, and CI
jobs answer whether workflows, loops, evaluations, and human approvals are
declared, evidenced, and merge-ready.

Audit reporting is read-only. PolicyFlow does not execute workflows, does not
run loops, does not calculate metrics, does not approve pull requests, and does
not fetch external artifacts or provider credentials.

## Local Usage

Use the workflow audit when developing or reviewing a Consumer-Repo locally:

```bash
policyflow audit ai/workflows
policyflow audit ai/workflows --json
```

Use focused reports when a review needs a narrower governance question:

```bash
policyflow evaluation-report ai/workflows
policyflow evaluation-report ai/workflows --json
policyflow loop-report ai/workflows
policyflow loop-report ai/workflows --json
```

Use a single-workflow status view when debugging one workflow instance:

```bash
policyflow status ai/workflows/features/first-feature.yml
policyflow status ai/workflows/features/first-feature.yml --json
```

Local reporting is useful before opening a PR, after changing workflow
evidence, and before claiming that a workflow is merge-ready.

## CI Usage

CI jobs can run the same commands after checkout and package installation:

```bash
python -m pip install policyflow==0.3.0
policyflow audit ai/workflows --json
policyflow evaluation-report ai/workflows --json
policyflow loop-report ai/workflows --json
```

Use JSON output when a downstream job needs a stable machine-readable artifact.
The workflow audit JSON uses `policyflow.audit.v1` with
`report_type: workflow_audit`.

The top-level audit summary groups governance state by:

- `workflow_governance`
- `loop_governance`
- `evaluation_governance`
- `human_governance`

Existing workflow-level audit fields remain available during the `0.x`
compatibility window. Downstream consumers should treat new top-level summary
keys as additive and keep parsers tolerant of additional fields.

## Governance Examples

Workflow governance identifies whether each workflow validates, is blocked, and
is merge-ready. It reflects declared workflow metadata, execution state,
evidence, contracts, overrides, runtime state, and handoff state.

Loop governance identifies declared feedback loops, loop compliance state,
iteration-limit failures, missing stop evidence, missing escalation evidence,
and unresolved escalated loops. See
[docs/loop-governance.md](loop-governance.md) for the loop model and consumer
expectations.

Evaluation governance identifies declared evaluation categories, required
metrics, failing merge-blocking metrics, missing required categories, and
missing evidence references. See
[docs/evaluation-governance.md](evaluation-governance.md) and
[docs/metric-governance.md](metric-governance.md) for the evaluation and metric
models.

Human governance identifies whether human approval is required, whether
approval evidence is present, and whether approval-gated workflows are missing
required approval evidence.

## Runtime Boundary

Audit reporting describes declared governance state. It does not make
PolicyFlow a runtime platform.

PolicyFlow does not execute workflows. Workflow execution remains the
responsibility of the Consumer-Repo, its maintainers, its CI system, and any
external agent runner selected by that repo.

PolicyFlow does not run loops. Feedback-loop work, review cycles, QA cycles,
security follow-up, and human arbitration remain external processes.

PolicyFlow does not calculate metrics. Test results, coverage values, scanner
findings, benchmark outputs, and review decisions must be produced by external
tools or people and then referenced as workflow evidence.

PolicyFlow does not approve pull requests. Human approval remains a GitHub
review and repository governance responsibility. PolicyFlow can validate that
the workflow and PR body point to the expected approval evidence.

PolicyFlow also does not schedule work, route messages, manage memory, host
agent runtimes, manage provider credentials, or replace CI and review systems.

## Related Contracts

- [docs/public-api.md](public-api.md) defines stable imports and the audit API.
- [docs/schema-compatibility.md](schema-compatibility.md) defines the audit JSON
  contract and compatibility policy.
- [docs/evaluation-governance.md](evaluation-governance.md) explains declared
  evaluation criteria and evidence.
- [docs/loop-governance.md](loop-governance.md) explains bounded feedback-loop
  governance.
- [docs/metric-governance.md](metric-governance.md) explains metric declaration,
  metric sources, and metric evidence.
