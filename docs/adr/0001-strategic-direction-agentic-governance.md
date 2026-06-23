# ADR-0001: Strategic Direction Toward Agentic Governance

## Status

Accepted

## Context

PolicyFlow currently provides AI-native SDLC governance for agent-assisted
software delivery. Its existing core includes risk-based workflow definitions,
human approval, evidence, review gates, PR validation, GitHub approval checks,
bootstrap assets, doctor checks, managed asset sync, and lightweight workflow
state mutation.

The next strategic step is to evolve PolicyFlow into an Agentic Governance
Platform. This evolution must preserve the current product core: PolicyFlow
governs agentic delivery, but it does not become the agent runtime, workflow
engine, scheduler, message bus, memory layer, merge bot, provider credential
manager, or replacement for orchestration frameworks such as LangGraph, CrewAI,
or AutoGen.

## Decision

PolicyFlow will evolve from AI-native SDLC Governance toward an Agentic
Governance Platform with four pillars:

- Workflow Governance: the existing core of risk-based workflows, evidence,
  review gates, human approval, and PR validation.
- Loop Governance: declarative governance for feedback loops between workflow
  phases, including iteration limits, stop conditions, escalation conditions,
  and allowed feedback sources.
- Evaluation Governance: declarative quality criteria, metrics, gates, and
  evaluation evidence for agentic delivery.
- Human Governance: expanded human-in-the-loop governance covering escalation,
  arbitration, override, and approval evidence.

PolicyFlow will define governance rules, validate those rules, and report
compliance. It will remain provider-neutral and framework-neutral.

## Consequences

PolicyFlow's roadmap can include new schemas, documentation, examples,
validators, audit views, and compliance reports for loops, evaluations, and
human governance.

PolicyFlow must continue to draw a bright line between governance and execution.
It may describe what a compliant agentic workflow must prove, but it must not
own how agents are hosted, scheduled, coordinated, prompted at runtime, or given
memory.

Strategic features should be evaluated by whether they strengthen governance
clarity, validation, auditability, and compliance reporting.

## Alternatives Considered

- Build a full agent orchestration platform. Rejected because it would dilute
  PolicyFlow's governance focus and duplicate existing runtime frameworks.
- Keep PolicyFlow limited to workflow validation only. Rejected because loops,
  evaluations, and human arbitration are already natural governance extensions.
- Bind PolicyFlow to a specific provider or agent framework. Rejected because
  provider-neutrality is a core product principle.

## Follow-up Actions

- Add a roadmap for Agentic Governance Platform evolution.
- Define future Loop Governance and Evaluation Governance schemas as
  declarative governance contracts.
- Keep runtime expansion explicitly bounded in future ADRs and release notes.
- Use a reference consumer project to validate that the platform direction stays
  practical without becoming an execution system.

