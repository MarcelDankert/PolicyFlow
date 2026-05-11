# Agent Handoff Contracts

## Purpose

Define explicit handoff expectations between workflow roles.

## Canonical Handoff Chains

LOW-risk fast path:
`planning-agent -> senior-dev-agent -> review-agent -> merge readiness`

Feature:
`planning-agent -> architecture-agent -> senior-dev-agent -> review-agent -> senior-dev-agent fix loop if needed -> qa-agent -> human approval if required -> merge readiness`

Bugfix:
`planning-agent -> architecture-agent -> senior-dev-agent -> review-agent -> senior-dev-agent fix loop if needed -> qa-agent -> human approval if required -> merge readiness`

Architecture change:
`planning-agent -> architecture-agent -> human approval -> senior-dev-agent -> review-agent -> senior-dev-agent fix loop if needed -> qa-agent -> human final approval -> merge readiness`

## Transition Rules

A handoff may proceed only if:
- required artifacts exist
- risk-review requirements are still satisfied
- escalation rules were evaluated
- confidence governance was evaluated
- no blocking findings remain

A handoff must stop and escalate if:
- artifacts are missing
- risk is unclear
- protected areas are touched without approval
- confidence is below threshold
- scope expanded
- tests fail without convergence
