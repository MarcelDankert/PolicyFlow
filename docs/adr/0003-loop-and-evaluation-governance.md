# ADR-0003: Loop And Evaluation Governance

## Status

Accepted

## Context

PolicyFlow currently governs workflow phases, risk, reviews, human approval,
evidence, contracts, overrides, runtime state, handoffs, PR validation, and
GitHub approval claims. The existing handoff and review concepts imply feedback
loops, but loops are not yet modeled as first-class governance objects.

PolicyFlow also requires confidence and evidence, but it does not yet provide a
generic evaluation governance model for measurable quality criteria such as test
pass status, coverage thresholds, review scores, security findings, performance
gates, or evaluation evidence.

Agentic delivery needs governance for both feedback loops and measurable
evaluation outcomes without requiring PolicyFlow to execute agents or own a
runtime.

## Decision

PolicyFlow will introduce Loop Governance and Evaluation Governance as
strategic extensions.

Loop Governance will define feedback-loop rules declaratively, including:

- source and target phases
- allowed feedback sources
- maximum iterations
- stop conditions
- escalation conditions
- required evidence for loop progress or loop termination

Evaluation Governance will define measurable quality rules declaratively,
including:

- required evaluation categories by risk level
- tests passed or failed
- coverage thresholds
- review scores
- security findings
- performance gates
- evaluation evidence references

Both concepts are governance layers. They define and validate expectations, but
they do not execute loops, schedule agents, calculate all scores internally, or
run test and security tooling directly.

## Consequences

Future schemas can model loop and evaluation requirements as first-class
governance contracts. Validators can check structural completeness, required
fields, risk-based requirements, evidence references, and compliance state.

Consumer-Repos remain responsible for generating evaluation data and executing
feedback loops through their selected tools, CI systems, agent runtimes, or
human processes.

PolicyFlow audit and reporting can grow to summarize compliance across workflow,
loop, evaluation, and human governance without becoming the system that performs
the underlying work.

## Alternatives Considered

- Encode loops only as informal handoff notes. Rejected because iteration limits
  and escalation conditions should be explicit and auditable.
- Build a loop execution engine. Rejected because PolicyFlow must not become a
  workflow engine or agent orchestrator.
- Treat evaluations as free-form evidence only. Rejected because measurable
  quality gates need consistent structure to support validation and reporting.

## Follow-up Actions

- Define an evaluation governance schema and examples.
- Define a loop governance schema and examples.
- Add validators for loop iteration limits, stop conditions, escalation rules,
  and evaluation evidence references.
- Extend audit reporting after schemas stabilize.
- Use Querypilot as a reference pilot for SQL guardrails, test, coverage,
  latency, review, and security evaluation governance.

