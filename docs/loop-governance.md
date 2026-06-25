# Loop Governance

PolicyFlow records, validates, and reports declared Loop Governance.
PolicyFlow does not execute loops, schedule loop execution, route messages,
provide memory, or call provider runtimes.

## Scope

Loop Governance is for Consumer-Repos that need explicit feedback-loop rules
between workflow phases. A loop declaration can name review, QA, security, human
arbitration, or Querypilot-inspired SQL safety feedback without turning
PolicyFlow into the system that performs that work.

## Non-Scope

PolicyFlow should not execute loop work. Agent runtimes, CI systems, SQL review
tools, human reviewers, and Consumer-Repo processes remain responsible for the
actual feedback, fixes, approvals, and reruns.

## Required Fields

Declare loops in `loop_governance.loops` with:

- `id`
- `source_phase`
- `target_phase`
- `allowed_feedback_sources`
- `max_iterations`
- `current_iteration`
- `status`
- `stop_conditions`
- `escalation_conditions`
- `evidence_refs`

`max_iterations` must be positive. `current_iteration` cannot exceed
`max_iterations`. Stop and escalation condition lists must be non-empty.

## Evidence

Evidence references point to workflow evidence or external artifacts. Completed
or terminated loops reference a declared stop condition with
`stop_conditions.<id>`. Escalated loops reference a declared escalation condition
with `escalation_conditions.<id>`.

## Escalation Expectations

Every governed loop declares at least one `escalation_conditions` entry.
Escalation conditions describe when normal feedback handling is no longer
enough and where the decision should go next, such as a security agent, QA lead,
human owner, or data owner.

PolicyFlow validates escalation declarations and evidence references. It does
not decide that an escalation should happen, execute escalation work, assign a
person, open a ticket, send a message, rerun an agent, or call a provider API.

High-risk or protected-area workflows must not hide escalation requirements in
free text. When a loop is marked `escalated`, `evidence_refs` should include a
condition-specific reference such as
`escalation_conditions.security-critical-findings` plus any external artifact
that supports the escalation.

## Consumer Usage

Use Loop Governance when a workflow needs reviewable feedback-loop boundaries:

- review feedback that returns to implementation
- QA regression findings that require bounded rework
- security findings that may require escalation
- human arbitration for unresolved scope or risk disputes
- Querypilot-inspired SQL safety checks where query plans, rollback evidence,
  or data-owner arbitration remain external

Add the optional `loop_governance` block to the workflow before implementation
starts. Keep loop status, iteration count, stop conditions, escalation
conditions, and evidence references aligned as the Consumer-Repo process
progresses. The loop declaration documents governance expectations; the
Consumer-Repo still owns the actual reviews, tests, scans, SQL analysis,
approvals, and remediation.

## Examples

Use `workflows/examples/loop-governance-workflow.yml` as the canonical example.
It includes review, QA, security, human arbitration, and a
Querypilot-inspired SQL safety loop without runtime execution.

Failure fixtures cover the common validation boundaries:

- `tests/fixtures/loop-governance-invalid-max.yml`
- `tests/fixtures/loop-governance-iteration-exceeded.yml`
- `tests/fixtures/loop-governance-missing-stop-conditions.yml`
- `tests/fixtures/loop-governance-missing-escalation-conditions.yml`
