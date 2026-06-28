# Provider-Neutral Integration Contract

PolicyFlow integrates with external runtimes, CI systems, and agent frameworks
through governance evidence. Those systems are evidence producers. PolicyFlow
validates and reports the declared governance state, but PolicyFlow does not
execute external systems, host agent runtimes, schedule work, route messages,
manage memory, own provider credentials, or require a provider SDK.

## Contract Purpose

The provider-neutral integration contract defines how an external system can
make its work visible to PolicyFlow without coupling PolicyFlow to that system.
The integration boundary is deliberately simple:

- external systems produce evidence, workflow updates, reviews, or artifacts
- Consumer-Repos decide which evidence is required for their governance model
- PolicyFlow validates the workflow file, PR body claims, approval claims, and
  reporting payloads against declared governance rules
- downstream tools read PolicyFlow reports such as `policyflow.audit.v1`

This keeps PolicyFlow useful across local CLIs, hosted model adapters,
repository automation, security scanners, test systems, review tools, and human
approval processes.

## Integration Responsibilities

External runtimes, CI systems, and agent frameworks are responsible for:

- executing their own work
- collecting their own results
- storing artifacts where the Consumer-Repo can reference them
- writing or proposing workflow evidence updates
- producing PR body claims that match the workflow file
- providing GitHub review metadata or organizational approval records when
  human governance requires them

PolicyFlow is responsible for:

- validating canonical workflow structure
- validating PR body claims against the workflow
- validating GitHub approval claims when review metadata is provided
- reporting workflow, loop, evaluation, and human governance status
- preserving a provider-neutral contract that does not import provider SDKs

PolicyFlow validates and reports governance state. PolicyFlow does not execute external systems or host the systems that produce that state.

## Workflow Evidence

Workflow evidence records what happened during governed work. External systems
may produce this evidence directly, or they may propose it for human or agent
review before it lands in the workflow file.

```yaml
context:
  workflow_file: ai/workflows/features/search-hardening.yml
  risk_level: MEDIUM

evidence:
  implementation:
    summary: External agent completed the approved implementation scope.
    changed_files:
      - src/search.py
      - tests/test_search.py
    test_summary:
      - pytest -q tests/test_search.py
    docs_updates:
      - docs/search.md
    limitations:
      - provider latency was measured outside PolicyFlow
```

The evidence can come from any tool. PolicyFlow only needs the workflow YAML and
the referenced PR body or review files for validation.

## Loop Evidence

Loop evidence makes feedback-loop state reviewable. An external agent runtime
may run the loop, a CI workflow may detect a retry condition, or a human review
may send the work back to implementation. PolicyFlow records the declaration and
validates the evidence references; it does not run the loop.

```yaml
loop_governance:
  loops:
    - id: review-feedback
      source_phase: review
      target_phase: implementation
      allowed_feedback_sources:
        - review-findings
        - qa-findings
      max_iterations: 3
      current_iteration: 1
      status: active
      stop_conditions:
        - id: review-findings-resolved
          description: Blocking review findings are resolved.
      escalation_conditions:
        - id: iteration-limit-reached
          trigger: max_iterations_exceeded
          escalate_to: human-arbitration
      evidence_refs:
        - evidence.review
```

External systems own feedback execution. PolicyFlow owns the validation and
reporting shape around the declared loop governance.

## Evaluation Evidence

Evaluation evidence records measurable quality criteria. CI systems, scanners,
benchmark tools, review systems, or domain-specific evaluators can produce the
underlying result. PolicyFlow validates required declarations and reports
compliance state, but it does not calculate all metrics.

```yaml
evaluation:
  compliance_status: pending
  categories:
    - id: tests
      required_metrics:
        - id: tests-passed
          name: Test suite pass status
          category: tests
          source: ci
          required: true
          thresholds:
            operator: equals
            value: passed
          actual_value: pending
          status: pending
          evidence_refs:
            - evidence.qa
          blocks_merge: true
```

Use provider-neutral sources such as `ci`, `security-scan`,
`external-benchmark`, `human-review`, or Consumer-Repo-specific source names
instead of SDK-specific identifiers.

## Human Governance Evidence

Human governance evidence covers approvals, escalation, arbitration, and
overrides. Approval-gated workflows should declare the required evidence path
and provide the actual evidence block.

```yaml
governance:
  human_approval_required: true
  approval_evidence:
    - evidence.approval

evidence:
  approval:
    approved_by: MarcelDankert
    reference: PR approval required before merge
    scope_confirmed: true
```

The workflow evidence is a claim that PolicyFlow can validate. It does not
replace the external approval system. GitHub reviews, organizational approvals,
or compliance records remain external evidence sources.

## Audit And Reporting

Integrations that need machine-readable status should use `policyflow audit`,
`policyflow evaluation-report`, and `policyflow loop-report`.

```bash
policyflow validate ai/workflows/features/search-hardening.yml
policyflow audit ai/workflows --json
```

`policyflow.audit.v1` is the audit reporting contract for downstream systems.
Consumers should read `schema_version`, use documented workflow, loop,
evaluation, and human governance fields, and tolerate additive fields unless a
release note declares a new schema version.

Python integrations should use the supported `policyflow` and `policyflow.api`
imports documented in [public-api.md](public-api.md). Command-based execution
adapters should use the runner shape documented in
[runner-contract.md](runner-contract.md).

## Non-Goals

This contract does not make PolicyFlow any of the following:

- provider SDK wrapper
- hosted runtime
- scheduler
- workflow engine
- message bus
- memory layer
- provider credential manager
- merge bot
- test runner, scanner, benchmark runner, or evaluation executor

Those capabilities belong in Consumer-Repos, external tools, CI systems, or
provider-specific adapters. PolicyFlow stays focused on declarative governance,
validation, and reporting.
