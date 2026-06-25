# PolicyFlow Agentic Governance Roadmap

## Vision

PolicyFlow defines governance for agentic software delivery independent of
agent, runtime, provider, or orchestration framework.

## Strategic Positioning

Today: AI-native SDLC Governance.

Target: Agentic Governance Platform.

PolicyFlow remains a governance system. It defines rules, validates rules, and
reports compliance. It does not own agent execution.

Non-goals:

- Agent Runtime
- Workflow Engine
- Scheduler
- Message Bus
- Memory Store
- Provider Credential Manager
- Merge Bot
- LangGraph, CrewAI, or AutoGen replacement

## Pillars

### 1. Workflow Governance

Workflow Governance is the existing PolicyFlow core. It covers risk-based
workflows, canonical phases, phase states, evidence, role contracts, review
gates, typed overrides, human approval requirements, PR validation, GitHub
approval checks, status views, audit views, bootstrap assets, doctor checks, and
managed asset sync.

Scope:

- define workflow governance schemas and templates
- validate risk level, required reviews, required phases, transitions, evidence,
  contracts, overrides, runtime state, handoffs, PR claims, and GitHub approvals
- report workflow status, merge readiness, blocked states, and audit summaries

Non-scope:

- run the project implementation
- own provider credentials
- merge pull requests
- replace target-project architecture or domain context

### 2. Loop Governance

Loop Governance defines feedback-loop rules declaratively. It makes iteration
limits, stop conditions, escalation conditions, required evidence, and allowed
feedback sources explicit.

Scope:

- declare allowed feedback loops between workflow phases
- define `max_iterations`
- define stop conditions and escalation conditions
- identify allowed feedback sources such as review findings, QA findings,
  security scan results, human arbitration, or evaluation failures
- require loop evidence when loops are used or terminated
- validate loop declarations and compliance state

Non-scope:

- execute the feedback loop
- schedule agents
- route messages between agents
- maintain memory of agent conversations
- decide autonomously when agents should retry work

### 3. Evaluation Governance

Evaluation Governance defines measurable quality criteria for agentic delivery.
It connects risk, evidence, and compliance to concrete evaluation signals.

Scope:

- define evaluation categories and required metrics
- model gates such as tests passed, coverage threshold, review score, security
  findings, performance thresholds, and domain-specific checks
- attach evaluation evidence to workflow and loop governance
- validate required evaluation evidence by risk level
- report evaluation compliance and missing evidence

Initial schema direction:

- `evaluation.categories`: groups such as tests, coverage, review, security,
  performance, and domain-specific checks
- `evaluation.categories[].required_metrics`: concrete metric declarations
- `thresholds`: expected values or comparison rules
- `evidence_refs`: links to workflow evidence, CI artifacts, scanner reports,
  review records, benchmark output, or domain-specific evidence
- `compliance_status`: overall evaluation compliance claim backed by external
  evidence

Evaluation Governance is declarative governance metadata. PolicyFlow records,
validates, and reports evaluation requirements and evidence references; it does
not run evaluation tooling, test suites, scanners, benchmarks, agents,
schedulers, provider SDKs, or orchestration frameworks.

Non-scope:

- run test suites
- run scanners
- calculate every score internally
- replace CI, observability, benchmark, or security tooling
- claim quality without external evidence

### 4. Human Governance

Human Governance extends existing Human-in-the-Loop controls from approval only
to escalation, arbitration, override, and approval evidence.

Scope:

- define when human escalation is required
- record human arbitration decisions
- govern human overrides with scope, risk impact, mitigation, approver,
  reference, and lifecycle
- validate approval evidence for high-risk and protected-area work
- report unresolved human governance gaps

Non-scope:

- replace organizational authority
- approve pull requests automatically
- bypass protected branch policies
- own identity provider or credential management

## Milestone Plan

### v1.1 - Evaluation Foundation

Goal: introduce evaluation schema and validation.

Possible issues:

- Define evaluation schema
- Add evaluation model
- Validate evaluation requirements
- Add evaluation examples
- Document evaluation governance

### v1.2 - Loop Governance Foundation

Goal: model loop definitions declaratively.

Possible issues:

- Define loop governance schema
- Add loop model
- Validate `max_iterations`
- Validate stop conditions
- Validate escalation rules
- Add loop governance examples
- Document loop governance

### v1.3 - Metrics & Evidence

Goal: connect metrics and evidence more strongly.

Possible issues:

- Define metrics schema
- Add metric evidence references
- Validate required metrics by risk level
- Add review score and QA metric examples
- Document metric governance

### v1.4 - Audit & Reporting

Goal: make compliance across workflows, loops, and evaluations reportable.

Possible issues:

- Extend `policyflow audit` output
- Add evaluation compliance report
- Add loop compliance report
- Add machine-readable audit JSON
- Document audit reporting

### v2.0 - Agentic Governance Platform

Goal: official positioning and stable governance interfaces.

Possible issues:

- Stabilize workflow, loop, and evaluation schemas
- Publish v2 migration guide
- Document provider-neutral integration contract
- Add reference consumer project
- Add Querypilot pilot documentation

## Querypilot Pilot

Querypilot should be the first reference project for Loop Governance and
Evaluation Governance. Its domain has clear agentic risk boundaries because
natural-language requests can produce SQL, SQL must remain safe, and generated
outputs can be evaluated with concrete checks.

Candidate Querypilot evaluation metrics:

- SQL guardrails passed
- only `SELECT` allowed
- generated SQL executable
- test pass rate
- coverage threshold
- response latency
- review score
- security findings

Candidate Querypilot loop governance scenarios:

- review feedback loop for unsafe SQL generation
- QA feedback loop for failing executable SQL checks
- human arbitration for ambiguous data-access intent
- escalation when generated SQL touches protected tables or violates guardrails

Querypilot should produce evidence that PolicyFlow can validate and report, but
PolicyFlow should not execute Querypilot agents, host its runtime, manage its
credentials, or schedule its feedback loops.

## Open Decisions

- How much runtime mutation remains allowed?
- How are evaluation scores calculated?
- Which metrics are generic enough for PolicyFlow?
- Which parts belong in Consumer-Repos?
- How is backward compatibility for `0.x` schemas handled?
- How should loop governance represent nested or repeated review and QA loops
  without becoming an execution model?
- Which evaluation failures should block validation versus produce warnings?
- How should human arbitration evidence be represented across GitHub-governed
  and local-only Consumer-Repos?

