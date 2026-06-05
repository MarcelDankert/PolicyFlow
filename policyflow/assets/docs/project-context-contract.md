# Project Context Contract

## Purpose

PolicyFlow provides reusable governance.
The target project provides domain-specific context.

Agents must load target-project context before planning, implementing, reviewing, or validating changes.

## Recommended Minimum Files

- `/AGENTS.md`
- `/ai/project-context.yml`
- `/ai/architecture.md`
- `/ai/rules/project-overrides.md`
- `/contracts/` if applicable

## Required Division Of Responsibility

### PolicyFlow Provides
- reusable governance terminology
- workflows
- agent role patterns
- escalation and approval rules
- GitHub governance patterns

### Target Project Provides
- domain boundaries
- protected business logic definitions
- external system boundaries
- contract ownership
- runtime and deployment constraints
- any repo-local overrides

## Agent Requirement

Before acting, an agent should load:
- `AGENTS.md`
- `ai/project-context.yml`
- relevant target-project architecture docs
- relevant project overrides
- contracts when applicable
