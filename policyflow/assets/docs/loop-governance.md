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

## Examples

Use `workflows/examples/loop-governance-workflow.yml` as the canonical example.
It includes review, QA, security, human arbitration, and a
Querypilot-inspired SQL safety loop without runtime execution.

Failure fixtures cover the common validation boundaries:

- `tests/fixtures/loop-governance-invalid-max.yml`
- `tests/fixtures/loop-governance-iteration-exceeded.yml`
- `tests/fixtures/loop-governance-missing-stop-conditions.yml`
- `tests/fixtures/loop-governance-missing-escalation-conditions.yml`
