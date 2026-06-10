# Governance Enforcement Roadmap

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

Schema compatibility and the root-level fallback migration path are now
documented in [schema-compatibility.md](schema-compatibility.md). Future
roadmap work can tighten validation only after release notes and migration steps
make the change explicit.
