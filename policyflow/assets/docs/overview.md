# Overview

PolicyFlow is a reusable governance and lightweight workflow orchestration layer
for agent-assisted software delivery.

Its product core is a machine-readable governance contract between humans,
agents, pull requests, and Consumer-Repos. PolicyFlow makes agentic work more
reviewable, risk-aware, and auditable by requiring explicit scope, risk,
evidence, role contracts, review gates, approval claims, and compliance checks.

It gives a Consumer-Repo:

- a common vocabulary for risk, confidence, evidence, and approval
- role definitions for planning, architecture, implementation, review, and QA
- explicit workflow phase state, runtime state, and handoffs
- typed overrides for approved exceptions
- bootstrap, doctor, sync, and workflow generation commands
- provider-neutral runner execution through a command contract
- GitHub issue, PR, and governance workflow templates
- local and CI validation for workflow files, PR bodies, and GitHub approvals

PolicyFlow is not a hosted scheduler, merge bot, or provider credential manager.
It owns workflow governance and state transitions while Consumer-Repos own their
domain context, implementation, and provider runtime setup.

## Maintained Surfaces

PolicyFlow is intentionally composed from a small Python package and reusable
framework assets:

- governance rules, risk matrices, escalation rules, and review expectations
- workflow templates, examples, generated workflow instances, and feature
  workflows for PolicyFlow's own development
- agent role descriptions and prompts that define expected inputs, outputs,
  stop conditions, and handoffs
- validators for workflows, pull request claims, GitHub approvals, runtime
  state, handoffs, evidence, contracts, and overrides
- bootstrap, doctor, sync, status, audit, and workflow generation commands for
  Consumer-Repo adoption
- GitHub issue templates, pull request templates, and governance workflow
  assets
- documentation for product scope, schema compatibility, public API, runner
  contract, release and upgrade expectations, and strategic direction

These surfaces are part of the framework contract for Consumer-Repos. They
should not be treated as local-only repository maintenance.

## Architecture Principles

PolicyFlow's current architecture follows these principles:

- governance is declarative and reviewable
- workflows are the source of truth for governed changes
- escalation is risk-based and cannot be bypassed by confidence claims
- human approval remains mandatory for high-risk and protected-area work
- evidence and role contracts are required before merge-readiness claims
- provider-neutral integration is preferred over provider-specific runtime
  ownership
- Consumer-Repos own domain context, implementation, credentials, and runtime
  setup
- runtime mutation stays limited to controlled workflow governance fields
- validation and reporting are stronger product boundaries than execution

The strategic direction for these principles is captured in
[Architecture Decision Records](adr/) and the
[Agentic Governance Roadmap](roadmap-agentic-governance.md).
