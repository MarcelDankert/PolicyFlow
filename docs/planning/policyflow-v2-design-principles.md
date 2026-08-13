# PolicyFlow 2.0 Design Principles

## Philosophy

PolicyFlow 2.0 should be a small open-source governance framework that remains useful because it is narrow. Its value is not that it can run an AI-assisted delivery process. Its value is that it can say, consistently and repeatably, whether that process satisfied declared governance rules.

The product should be understandable in less than ten minutes:

- define a change governance file.
- validate it.
- reference it from a pull request.
- validate merge readiness evidence.

Everything else is optional ecosystem work and should remain outside the core unless it directly improves governance validation.

## Non-Negotiable Principles

### 1. Governance Over Execution

PolicyFlow validates what must be true. It does not perform the work required to make it true.

Allowed:

- Validate that test evidence exists.
- Validate that approval is required.
- Validate that a PR names required evidence.

Rejected:

- Run tests.
- Request approval.
- Run an agent.
- Advance workflow state.

### 2. Provider Neutrality

PolicyFlow must not depend on any model provider, agent product, runtime, or hosted platform.

Rejected from core:

- OpenAI SDKs.
- Anthropic SDKs.
- Gemini SDKs.
- Codex adapters.
- Copilot adapters.
- provider credentials.
- provider-specific prompts or result formats.

External systems may produce PolicyFlow evidence.

### 3. Evidence Is External

PolicyFlow should treat evidence as data, not as work to perform.

Evidence may come from:

- CI.
- human review.
- security scanners.
- external agent runtimes.
- QueryPilot.
- consumer-specific tools.

PolicyFlow validates structure, status, and required references.

### 4. The Schema Must Stay Small

Every field must justify itself by affecting a governance decision.

A field should be rejected when it only:

- makes reports nicer.
- preserves historical shape.
- helps one consumer.
- anticipates a future feature.
- duplicates another field.

### 5. CLI Minimalism

The ideal CLI is:

```text
policyflow init
policyflow validate
policyflow validate-pr
policyflow doctor
```

New commands require a high bar. A command belongs only if it answers a governance question that cannot be handled by an existing command or external system.

### 6. Init Is Not a Platform Installer

`policyflow init` should create the minimum useful governance footprint.

It should not install:

- agents.
- prompts.
- runner configs.
- provider adapters.
- large template trees.
- managed asset sync metadata.

### 7. GitHub Is Evidence, Not Control

PolicyFlow may read PR body and review metadata. It may run in GitHub Actions as a check.

It should not:

- create branches.
- create issues.
- create pull requests.
- label issues.
- assign milestones.
- merge PRs.
- wait for approvals.

### 8. Reporting Explains Compliance

Reporting belongs only if it explains validation results and merge readiness.

Reporting should not become:

- productivity analytics.
- model analytics.
- team performance metrics.
- loop performance dashboards.
- delivery forecasting.

### 9. Public API Means Governance API

Stable public imports should expose governance validation only.

Do not expose:

- runtime mutation.
- runner execution.
- sync mechanics.
- provider adapters.
- workflow generation.

### 10. Externalize Attractive Complexity

The most dangerous features are useful features that almost belong.

Move these out by default:

- runner execution.
- Codex/Copilot adapters.
- model routing.
- advisor patterns.
- loop execution.
- evaluation calculation.
- engineering analytics.
- managed asset upgrade systems.

## Design Tests for Future Pull Requests

Every future PR should answer these questions:

1. Does this change directly improve governance validation, evidence validation, or merge readiness?
2. Does this introduce execution ownership?
3. Does this require a provider, runtime, scheduler, queue, credential, or message system?
4. Could the same value be achieved by external evidence plus validation?
5. Does every new schema field affect a validation decision?
6. Can a new developer still understand the product in less than ten minutes?
7. Does this expand the public API beyond governance?
8. Does this add a command that could be an option, JSON output, or external tool?
9. Does this create another source of truth for assets, docs, or policy?
10. Would this be maintainable by a small open-source project for five years?

If any answer is unclear, the default decision is not to add the feature.

## Preferred Product Shape

PolicyFlow should feel like:

- `ruff` for governance policy.
- `mypy` for merge-readiness claims.
- a small CI-friendly validator.

PolicyFlow should not feel like:

- an agent platform.
- a workflow engine.
- an orchestration runtime.
- a dashboard product.
- a provider integration framework.

## Maintenance Posture

Small is a product feature. V2 should optimize for:

- few concepts.
- few commands.
- obvious files.
- strong diagnostics.
- stable validation behavior.
- external interoperability through simple evidence JSON/YAML.

When in doubt, remove the concept.

