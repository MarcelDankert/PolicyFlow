# PolicyFlow 2.0 Greenfield Architecture

## 1. Product Scope

PolicyFlow 2.0 is a small provider-neutral policy-as-code governance tool for AI-assisted software development. It answers governance questions before merge:

- Is this change allowed under declared repository policy?
- What risk level applies?
- Which reviews are required?
- Is human approval required?
- Is required evidence present?
- Are exceptions explicitly approved?
- Can the pull request be considered merge-ready from a governance perspective?

PolicyFlow 2.0 is not an execution platform. It does not run agents, schedule work, route messages, manage memory, call providers, select models, generate code, or manage developer productivity analytics.

### In Scope

- Governance policy files.
- Change/workflow governance schema.
- Risk classification rules.
- Required review rules.
- Human-in-the-loop requirements.
- Evidence reference validation.
- Override and exception validation.
- Pull request governance validation.
- GitHub review metadata validation for declared approvals.
- Minimal consumer initialization.
- Minimal read-only compliance output for CI and humans.

### Out of Scope

- Agent execution.
- Runner abstraction.
- Provider SDKs or credentials.
- Codex, Copilot, Anthropic, Gemini, or any provider adapter.
- Scheduling, queues, memory, message routing, or orchestration.
- Model routing or advisor execution.
- Workflow generation beyond a minimal starter example.
- Long-running runtime state.
- Engineering analytics and productivity measurement.
- Managed asset fleet synchronization.
- Product-specific integrations such as QueryPilot execution.

## 2. Product Responsibilities

PolicyFlow owns:

- A small governance schema.
- Validation of governance documents.
- Validation of PR claims against governance documents.
- Validation of GitHub approval review data against declared human approval requirements.
- Clear diagnostics that explain why a change is not governance-ready.
- A minimal init path that helps a repository adopt the schema and PR check.
- A stable Python API and CLI for the above.

PolicyFlow explicitly rejects:

- Deciding how work is executed.
- Executing or coordinating agents.
- Producing evidence through test, security, model, or runtime tools.
- Fetching external provider state.
- Becoming a CI platform.
- Becoming a workflow engine.
- Becoming an analytics platform.
- Owning repository-specific policy beyond validating policy files supplied by the repository.

## 3. Public Python API

Expose only governance APIs:

```python
from policyflow import (
    PolicyFlowError,
    ValidationResult,
    validate_change,
    validate_change_data,
    validate_pull_request,
    validate_github_approvals,
    explain_merge_readiness,
)
```

Recommended API:

- `validate_change(path) -> ValidationResult`
  - Validates one governance document from disk.
  - Belongs in PolicyFlow because schema and policy validation are core.

- `validate_change_data(data) -> ValidationResult`
  - Validates in-memory governance data for CI wrappers and external systems.
  - Belongs in PolicyFlow because external runtimes may produce evidence data that PolicyFlow validates.

- `validate_pull_request(change_path, pr_body_path) -> ValidationResult`
  - Validates PR claims against the declared governance document.
  - Belongs in PolicyFlow because merge readiness is a core governance question.

- `validate_github_approvals(change_path, pr_body_path, reviews_path, allow_pending=False) -> ValidationResult`
  - Validates that declared human approvers actually approved the PR.
  - Belongs in PolicyFlow because human approval evidence is governance.

- `explain_merge_readiness(change_path, pr_body_path=None, reviews_path=None) -> MergeReadiness`
  - Produces a read-only decision summary.
  - Belongs only if kept small and derived from validation results.

Do not expose:

- Runtime mutation helpers.
- Runner APIs.
- Provider adapters.
- Workflow generation APIs.
- Sync APIs.
- Analytics APIs.

## 4. CLI

Ideal CLI:

```text
policyflow init
policyflow validate
policyflow validate-pr
policyflow doctor
```

Optional if justified:

```text
policyflow explain
```

### `policyflow init`

Why it exists: creates the smallest useful repository footprint for adoption.

Why it belongs: governance tools need a clear starting layout and config.

Why it should not move elsewhere: without init, every consumer hand-rolls policy file paths and PR template conventions.

Keep it strict: no runner config, no prompts, no agents, no managed sync metadata by default.

### `policyflow validate`

Why it exists: validates governance documents.

Why it belongs: this is the core product.

Why it should not move elsewhere: external systems can produce evidence, but PolicyFlow must be the validator of the policy contract.

### `policyflow validate-pr`

Why it exists: validates PR body claims against governance.

Why it belongs: merge readiness is one of PolicyFlow's central questions.

Why it should not move elsewhere: PR governance needs one stable, provider-neutral rule implementation.

Recommended options:

```text
policyflow validate-pr <change.yml> <pr-body.md>
policyflow validate-pr <change.yml> <pr-body.md> --github-reviews pr-reviews.json
policyflow validate-pr <change.yml> <pr-body.md> --allow-pending-approval
```

This folds approval validation into PR validation without requiring a separate top-level command.

### `policyflow doctor`

Why it exists: checks whether a repository can run the minimal governance path.

Why it belongs: adoption clarity is part of a ten-minute product.

Why it should not move elsewhere: doctor validates PolicyFlow-specific config, file paths, and GitHub governance wiring.

It should check only:

- Python/package availability.
- `policyflow.yml`.
- schema/rule files.
- PR template if PR validation is enabled.
- GitHub Actions workflow if GitHub governance is enabled.

It should not check:

- runner commands.
- provider CLIs.
- credentials.
- agent prompt files.
- execution adapters.

### `policyflow explain` Optional

Why it might exist: a concise human-readable merge readiness explanation is useful locally and in CI logs.

Why it belongs only if tiny: it is derived from validation, not a separate reporting product.

Why it might be omitted: `validate --json` and `validate-pr --json` may be enough.

## 5. Governance Schema

Greenfield schema:

```yaml
version: 2

change:
  id: auth-login-hardening
  type: feature
  summary: Harden login flow validation.

risk:
  level: medium
  rationale: Touches authentication behavior.
  protected_areas:
    - authentication

governance:
  required_reviews:
    - security
    - maintainer
  human_approval_required: true

confidence:
  level: medium
  summary: Scope is bounded, but authentication impact requires review.

evidence:
  - id: tests
    type: test
    source: ci
    status: passed
    ref: https://ci.example/run/123
  - id: security-review
    type: review
    source: human
    status: pending
    ref: PR review pending

overrides: []
```

### Field Justification

- `version`: Required to make breaking schema changes explicit.
- `change.id`: Required stable identifier for PR references and diagnostics.
- `change.type`: Required for policy rules that vary by change category.
- `change.summary`: Required human-readable context.
- `risk.level`: Required because risk drives reviews and human approval.
- `risk.rationale`: Required to prevent unexplained risk choices.
- `risk.protected_areas`: Required because protected areas elevate governance.
- `governance.required_reviews`: Required because review requirements are core.
- `governance.human_approval_required`: Required because human-in-the-loop is core.
- `confidence.level`: Required lightweight signal for uncertainty.
- `confidence.summary`: Required human-readable uncertainty explanation.
- `evidence`: Required as a list because governance depends on evidence.
- `evidence.id`: Required stable reference from PR body and diagnostics.
- `evidence.type`: Required to distinguish tests, reviews, approvals, security scans, and docs.
- `evidence.source`: Required to show who or what produced evidence.
- `evidence.status`: Required for compliance.
- `evidence.ref`: Required pointer to external evidence.
- `overrides`: Optional list for approved policy exceptions.

### Override Shape

```yaml
overrides:
  - id: temporary-risk-exception
    type: risk_exception
    reason: Release patch cannot wait for full review window.
    approved_by: repo-owner
    approval_ref: https://github.com/org/repo/pull/123#issuecomment-...
    expires_on: 2026-09-01
```

Keep override types few:

- `risk_exception`
- `approval_exception`
- `evidence_exception`
- `scope_exception`

Reject:

- `phase_bypass` as a core concept.
- runtime or handoff exceptions.
- provider-specific exception types.

## 6. Module Structure

Recommended package:

```text
policyflow/
    __init__.py
    api.py
    cli.py
    config.py
    exceptions.py
    github.py
    models.py
    rules.py
    validator.py
```

### Module Justification

- `__init__.py`: Re-export stable public API only.
- `api.py`: Public wrappers with stable signatures.
- `cli.py`: Thin CLI layer over public API.
- `config.py`: Load and validate `policyflow.yml`.
- `exceptions.py`: Typed errors and diagnostic objects.
- `github.py`: Pure validation of GitHub PR/review JSON. No mutation.
- `models.py`: Pydantic governance models.
- `rules.py`: Risk/review/protected-area rule evaluation.
- `validator.py`: Orchestrates schema, evidence, PR, and rule validation.

Modules not included:

- `runtime.py`
- `agent_execution.py`
- `codex_runner.py`
- `sync.py`
- `workflow_generator.py`
- large `reporting.py` unless `explain` grows enough to justify a small module

## 7. Bootstrap

Start with zero files. Add only files that reduce adoption ambiguity.

Minimum `policyflow init` output:

```text
policyflow.yml
policyflow/change.example.yml
.github/PULL_REQUEST_TEMPLATE.md
.github/workflows/policyflow.yml
```

### `policyflow.yml`

Required because the tool needs stable paths:

```yaml
version: 2
paths:
  changes: policyflow/changes
features:
  pr_validation: true
  github_actions: true
```

### `policyflow/change.example.yml`

Required because a concrete example is the fastest way to learn the schema.

Do not generate a live workflow that pretends planning or review already happened.

### PR Template

Belongs because PR validation needs stable human-facing fields.

Keep it short:

```markdown
## PolicyFlow

- Change file:
- Risk level:
- Evidence:
- Human approval:

- [ ] The change file was created before implementation.
- [ ] Required evidence is linked.
- [ ] Required approvals are identified.
```

### GitHub Actions Workflow

Belongs only as a read-only governance check:

- Install PolicyFlow.
- Read PR body.
- Validate change file.
- Validate PR body.
- Optionally validate review JSON.

No branch creation, PR creation, issue mutation, labels, milestones, or merge actions.

## 8. Reporting

Reporting belongs only as minimal read-only compliance explanation.

Core reporting should answer:

- valid or invalid.
- merge-ready or not from governance perspective.
- missing required reviews.
- missing or failed evidence.
- missing human approval.
- active/expired overrides.

Recommended implementation:

- `policyflow validate --json`
- `policyflow validate-pr --json`
- optional `policyflow explain`

Do not include:

- evaluation dashboards.
- productivity metrics.
- engineering analytics.
- loop performance.
- agent performance.
- model comparisons.

Those belong in external analytics systems. PolicyFlow can expose neutral validation results for them to consume.

## 9. GitHub Integration

In scope:

- PR body validation.
- GitHub Actions workflow that runs validation.
- GitHub review JSON validation for declared human approvals.
- Minimal PR template.

Out of scope:

- Issue templates by default.
- Creating issues.
- Creating branches.
- Creating pull requests.
- Applying labels.
- Assigning milestones.
- Merge automation.
- GitHub App mutation preflight.
- Long-running approval wait loops.

PolicyFlow should treat GitHub as a source of PR and review evidence, not as a system it controls.

## 10. Consumer Experience

Ideal ten-minute adoption:

1. Install:

   ```bash
   python -m pip install policyflow
   ```

2. Initialize:

   ```bash
   policyflow init
   ```

3. Read the generated example:

   ```text
   policyflow/change.example.yml
   ```

4. Create a change governance file:

   ```bash
   cp policyflow/change.example.yml policyflow/changes/my-change.yml
   ```

5. Validate:

   ```bash
   policyflow validate policyflow/changes/my-change.yml
   ```

6. Open a PR using the template.

7. Validate PR body:

   ```bash
   policyflow validate-pr policyflow/changes/my-change.yml pr-body.md
   ```

A developer should not need to understand agents, prompts, runners, handoffs, sync, phase mutation, loop execution, or provider setup.

## 11. Product Comparison

| Area | Current Repository | Greenfield V2 | Recommendation |
| --- | --- | --- | --- |
| Core validation | Large validator covers governance, runtime, handoffs, loop state, evaluation metrics, PR parsing | Small validator for governance schema, evidence, overrides, PR claims | REBUILD |
| Runtime state | First-class `runtime` block and mutation commands | No runtime state; optional evidence status only | REMOVE |
| Agent execution | `run-phase`, runner contract, external command execution | External systems produce evidence | MOVE |
| Codex integration | Packaged Codex CLI adapter | External adapter outside core | MOVE |
| Runner config | Generated by default | Not generated | REMOVE |
| Agent/prompt assets | Packaged and bootstrapped | External runtime or consumer-owned | MOVE |
| Handoffs | First-class state and validation | Evidence references only | SIMPLIFY |
| Role contracts | Required agent-owned phase output contracts | External evidence schema, no agent ownership | MOVE |
| Evaluation metrics | Thresholds, actual values, report rollups | Evidence type/status/ref only | SIMPLIFY |
| Loop governance | Iteration counts, statuses, reports | External runtime; PolicyFlow may validate declared evidence policy only | MOVE |
| Reporting | Status, audit, loop report, evaluation report | Minimal read-only validation/explain output | SIMPLIFY |
| Bootstrap | Large managed asset scaffold | Four-file minimal scaffold | REBUILD |
| Sync | Managed asset update system | No core sync | REMOVE |
| Workflow generator | Creates detailed workflow state | Example file only | REMOVE |
| GitHub integration | PR validation, approval checks, templates, workflow, mutation-oriented preflight | Read-only PR/review validation and GitHub Actions check | SIMPLIFY |
| Public API | Validation plus runtime mutation and audit | Governance validation only | REBUILD |
| Docs | Broad platform documentation | Short governance-first docs | REBUILD |

## 12. Hidden Complexity

Historical complexity to remove:

- Same concept modeled multiple ways: evidence, contracts, handoffs, runtime status, PR sections.
- `execution.phases` became both governance record and workflow engine state.
- `contracts.owner_agent` makes agent roles part of schema compatibility.
- Runner convenience became a product architecture.
- Codex reference adapter introduced provider-specific gravity.
- Bootstrap became a platform installer instead of a governance starter.
- Sync exists because bootstrap installed too many managed assets.
- Reporting grew from compliance explanation into loop/evaluation summaries.
- Evaluation metrics mix governance evidence with analytics and measurement logic.
- Loop governance mixes policy constraints with runtime iteration state.
- Packaged assets duplicate top-level repository assets and drift.
- GitHub utilities drift toward mutation readiness instead of read-only governance.

## 13. Ten Architectural Principles

1. PolicyFlow validates governance; it does not execute work.
2. Provider neutrality is non-negotiable.
3. Every schema field must change a governance decision or be removed.
4. Evidence is produced outside PolicyFlow and validated inside PolicyFlow.
5. The CLI must stay small enough to explain in one minute.
6. `init` must optimize for adoption, not platform completeness.
7. GitHub integration must be read-only except for normal CI status reporting.
8. Reporting must explain compliance, not measure productivity.
9. Public API compatibility applies only to governance APIs.
10. Attractive runtime or analytics features must be external integrations, not core product growth.

## 14. Future Growth Outside PolicyFlow

- Model routing: belongs in Sentinel-AI-Core, provider adapters, or consumer runtimes.
- Advisor pattern: belongs in agent orchestration systems.
- Engineering analytics: belongs in analytics platforms consuming PolicyFlow validation output.
- Runtime orchestration: belongs in LangGraph, CrewAI, AutoGen, Sentinel-AI-Core, or consumer tooling.
- Execution engines: belong outside PolicyFlow.
- Provider integrations: belong in provider-specific adapters.
- QueryPilot execution: belongs in QueryPilot.
- Codex/Copilot wrappers: belong in external adapters or examples.
- Workflow generation: belongs in project templates or external scaffolding tools unless limited to one example file.

PolicyFlow can support this ecosystem by publishing stable validation result JSON, not by owning the work those systems perform.

