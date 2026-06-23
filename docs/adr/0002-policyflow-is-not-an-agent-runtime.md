# ADR-0002: PolicyFlow Is Not An Agent Runtime

## Status

Accepted

## Context

PolicyFlow already includes lightweight runtime state mutation commands and a
provider-neutral runner contract. These capabilities make workflow state and
handoffs explicit, but they also create architectural pressure to expand into a
full agent runtime or workflow engine.

The repository documentation already states that PolicyFlow is not a hosted
scheduler, merge bot, provider credential manager, full orchestration platform,
or hosted agent runtime. Future roadmap work must keep that boundary explicit.

## Decision

PolicyFlow will not become an agent runtime, workflow engine, scheduler
platform, memory layer, message bus, merge bot, provider credential manager, or
replacement for LangGraph, CrewAI, AutoGen, or similar orchestration systems.

PolicyFlow may:

- define governance rules for agentic delivery
- validate workflow, loop, evaluation, human approval, and PR governance claims
- report compliance and audit status
- persist controlled governance state in workflow documents
- accept provider-neutral evidence from external runners or consumer systems

PolicyFlow must not:

- host or schedule agents
- independently orchestrate agents
- maintain agent memory
- route messages between agents
- own provider credentials
- execute GitHub merge decisions
- require a specific agent framework or model provider

Runtime expansion is intentionally limited to controlled workflow-field
mutation and validation support.

## Consequences

Provider-neutrality remains a hard architectural constraint. Consumer-Repos and
external orchestration systems remain responsible for runtime setup, execution,
credentials, scheduling, memory, and provider-specific behavior.

PolicyFlow integrations should exchange structured inputs, outputs, evidence,
and compliance state rather than runtime control.

New features that imply ownership of scheduling, queues, memory, message
routing, long-running execution, autonomous coordination, or provider
authentication require an explicit ADR before implementation.

## Alternatives Considered

- Expand `run-phase` into a complete orchestration subsystem. Rejected because
  this would turn PolicyFlow into the runtime it is designed to govern.
- Add first-class provider SDK integrations. Rejected because provider setup
  belongs to Consumer-Repos or adapters.
- Remove all runtime state mutation. Rejected because controlled state mutation
  is useful for governance evidence and handoff visibility when kept bounded.

## Follow-up Actions

- Keep future runner and runtime documentation explicit about non-goals.
- Review roadmap items for accidental runtime, scheduler, message bus, or memory
  ownership.
- Prefer schema, validation, reporting, and evidence ingestion over execution
  features.
- Document provider-neutral integration contracts before expanding integrations.

