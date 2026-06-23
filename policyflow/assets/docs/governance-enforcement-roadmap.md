# Governance Enforcement Roadmap

This document describes the current enforcement boundary and near-term
governance direction. Strategic platform direction is tracked separately in
[roadmap-agentic-governance.md](roadmap-agentic-governance.md), and accepted
architecture decisions are tracked in [adr/](adr/).

## Current Product Boundary

PolicyFlow's strongest current capabilities are local validation, workflow
generation, Consumer-Repo bootstrap, doctor checks, PR body validation, GitHub
approval metadata validation, managed asset sync, status reporting, and audit
reporting.

Its more experimental boundaries are agent-owned phase execution through the
provider-neutral command runner, lightweight runtime state mutation, and
handoff-based coordination. These features exist to support governance evidence
and phase visibility. They should not expand into hosted scheduling, autonomous
agent orchestration, message routing, memory, or provider credential ownership.

PolicyFlow validates governance structure and compliance claims. It does not
prove the semantic truth of all evidence, review findings, confidence claims,
or quality metrics. External tools, reviewers, approvers, CI systems, and
Consumer-Repos remain responsible for producing trustworthy evidence.

Current draft and stacked PR semantics are documentation-only guidance. Draft
PRs are treated as planning or preview artifacts until explicitly promoted to
merge readiness. Stacked PRs are dependency-bound and should not be considered
normal merge candidates until upstream dependencies are merged or otherwise
satisfied. PolicyFlow documents this distinction today without adding validation
behavior, scheduling, or release orchestration.

## Current Enforcement

- workflow YAML validation
- `workflow` metadata validation
- `context.workflow_file` validation
- `context.risk_level` validation
- `context.confidence` validation
- `governance.required_reviews` validation
- risk-review matrix validation
- canonical execution phase validation by risk level
- completed phase evidence and role contract validation
- typed workflow override validation and lifecycle checks
- runtime state and handoff validation
- `HIGH` human approval validation
- `HIGH` approval evidence validation
- protected-area escalation validation
- Consumer-Repo config validation with `policyflow config-check`
- Consumer-Repo readiness checks with `policyflow doctor`
- workflow instance generation with `policyflow new-workflow`
- PR body completeness validation with `policyflow validate-pr`
- GitHub approval metadata validation with `policyflow validate-github-approvals`
- status and audit views with `policyflow status` and `policyflow audit`
- synchronous provider-neutral runner execution with `policyflow run-phase`
- managed asset drift preview and update with `policyflow sync`

## Current Fail Conditions

- missing workflow metadata, workflow file path, risk level, confidence, execution, or required reviews
- invalid risk level
- weaker-than-matrix review requirements
- missing required canonical phases for the declared risk level
- completed phases without required evidence or role contracts
- implementation, review, QA, or approval phase transitions before prerequisites are complete
- HIGH risk without human approval
- HIGH risk without approval evidence
- protected area touched without escalation
- protected area touched outside `HIGH` risk
- malformed, expired, or unreferenced required overrides
- runtime `handoff_pending` without an open pending handoff
- handoffs without concrete input and output artifact lists
- PR body missing linked issue, workflow file, risk level, confidence, evidence references, override references, or workflow governance confirmations
- PR body workflow path, declared risk, approval login, override type, or override approver mismatches the workflow
- GitHub review metadata missing required `APPROVED` reviews from declared approvers
- Consumer-Repo readiness gaps detected by doctor
- runner command failures or invalid runner output during `run-phase`

## Remaining Roadmap

- public Python API stability boundary
- release publishing and pinned consumer governance workflow installation
- broader docs cleanup and compatibility guidance as more Consumer-Repos adopt PolicyFlow
- declarative Loop Governance and Evaluation Governance as described in the
  Agentic Governance Roadmap
- stronger links between metrics, evidence, review gates, and audit reports

Schema compatibility and the root-level fallback migration path are now
documented in [schema-compatibility.md](schema-compatibility.md). Future
roadmap work can tighten validation only after release notes and migration steps
make the change explicit.
