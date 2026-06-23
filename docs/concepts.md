# Concepts

## Policy-As-Code

Governance rules should be explicit, reviewable, and eventually automatable.
PolicyFlow treats workflow files, rules, PR claims, evidence, contracts, and
approval records as governance artifacts rather than informal notes.

## Risk-Aware Workflows

Workflow strictness should vary by risk level:
- LOW
- MEDIUM
- HIGH

Risk controls review depth, required phases, human approval expectations, and
protected-area escalation. Confidence cannot downgrade risk.

## Confidence Governance

Confidence is a reporting signal, not an authorization substitute.
It should explain planning confidence, implementation confidence, test
confidence, and residual uncertainty. Low confidence is an escalation signal;
high confidence is not a bypass.

## Explicit Agent Handoffs

Every workflow step should define:
- agent
- inputs
- outputs
- handoff target
- stop conditions
- escalation conditions

Handoffs are governance contracts. They make phase ownership and required
artifacts explicit, but they do not make PolicyFlow an agent runtime or
multi-agent coordinator.

## Human-In-The-Loop

High-risk work must remain subject to explicit human approval.

Human governance also includes escalation, arbitration, override decisions, and
approval evidence. PolicyFlow records and validates these claims; it does not
replace organizational authority.

## Evidence And Role Contracts

Completed governance phases should produce machine-readable evidence and role
contracts. Evidence explains what was decided or verified. Role contracts record
the responsible owner agent and the outputs expected from that phase.

PolicyFlow validates the structure and presence of these artifacts. The
substance still belongs to the reviewer, QA process, human approver, CI system,
or Consumer-Repo evidence source.

## Typed Overrides

Overrides make approved exceptions visible. They should declare scope impact,
risk impact, mitigations, approver, approval reference, and a review or expiry
window.

Overrides are not a hidden bypass. They are governance objects that can expire,
require revalidation, and be surfaced in pull request evidence.
