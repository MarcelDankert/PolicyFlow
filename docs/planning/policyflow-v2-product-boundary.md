# PolicyFlow 2.0 Product Boundary

## One-Sentence Boundary

PolicyFlow validates provider-neutral governance evidence for AI-assisted software changes so repositories can decide whether a pull request is merge-ready.

## Starts Here

PolicyFlow begins when a repository declares governance policy for a change:

- change identity.
- risk level.
- protected areas.
- required reviews.
- human approval requirement.
- confidence statement.
- evidence references.
- approved exceptions.

PolicyFlow reads that declaration and validates it.

## Ends Here

PolicyFlow ends after producing a governance decision:

- valid or invalid.
- merge-ready or not merge-ready.
- missing evidence.
- missing approval.
- missing review.
- invalid exception.
- invalid PR claim.

PolicyFlow does not perform the work needed to satisfy the decision.

## In Scope

- `policyflow.yml` configuration.
- V2 governance document schema.
- Risk and protected-area validation.
- Required review validation.
- Human approval requirement validation.
- Evidence reference validation.
- Override/exception validation.
- PR body validation.
- GitHub review JSON validation for declared approvals.
- Minimal GitHub Actions check.
- Minimal PR template.
- Minimal read-only validation summary.

## Out of Scope

- Agent execution.
- Agent role orchestration.
- Prompt management.
- Runner configuration.
- Codex/Copilot/provider adapters.
- Provider SDKs and credentials.
- Model routing.
- Advisor execution.
- Scheduling.
- Queues.
- Memory.
- Message routing.
- Workflow engines.
- Loop execution.
- Test execution.
- Security scan execution.
- Metric calculation.
- Engineering analytics.
- Productivity measurement.
- Issue creation.
- Branch creation.
- Pull request creation.
- Label or milestone mutation.
- Merge automation.
- Managed asset synchronization.

## Accepted Inputs

PolicyFlow may consume:

- governance YAML.
- repository policy config.
- pull request body markdown.
- GitHub PR review JSON.
- structured evidence references from external systems.

PolicyFlow should not fetch or create execution evidence itself.

## Produced Outputs

PolicyFlow may produce:

- human-readable validation diagnostics.
- JSON validation results.
- merge-readiness summary.
- CI exit code.

PolicyFlow should not produce:

- executed agent outputs.
- generated code.
- scheduled jobs.
- provider calls.
- runtime state transitions.
- analytics dashboards.

## External System Boundary

External systems own execution:

| Capability | Owner |
| --- | --- |
| Agent runtime | Sentinel-AI-Core, LangGraph, CrewAI, AutoGen, consumer tools |
| Provider execution | Codex, Copilot, provider CLIs, provider SDK wrappers |
| Model routing | Sentinel-AI-Core or dedicated routing service |
| QueryPilot execution | QueryPilot |
| Tests and scans | CI and security tools |
| Engineering analytics | analytics platform consuming PolicyFlow results |
| GitHub mutation | repository automation outside PolicyFlow |

PolicyFlow may validate evidence emitted by these systems.

## Boundary Rule

If a proposed feature needs to know how work is executed, it is outside PolicyFlow.

If a proposed feature only needs to know whether required governance evidence exists and is valid, it may belong in PolicyFlow.

