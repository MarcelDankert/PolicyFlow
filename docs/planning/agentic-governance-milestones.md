# Agentic Governance Milestones And Proposed Issues

This document prepares GitHub milestones and issues for review. It does not
create issues directly.

## Milestones

| Milestone | Goal | Primary Outcome |
| --- | --- | --- |
| v1.1 - Evaluation Foundation | Introduce evaluation schema and validation. | PolicyFlow can model and validate evaluation requirements. |
| v1.2 - Loop Governance Foundation | Model loop definitions declaratively. | PolicyFlow can govern feedback loops without executing them. |
| v1.3 - Metrics & Evidence | Connect metrics and evidence more strongly. | PolicyFlow can link measurable quality signals to governance evidence. |
| v1.4 - Audit & Reporting | Report compliance across workflows, loops, and evaluations. | Audit output summarizes broader governance compliance. |
| v2.0 - Agentic Governance Platform | Stabilize positioning and public governance interfaces. | PolicyFlow has stable schemas and reference adoption guidance. |

## v1.1 - Evaluation Foundation

### Define evaluation schema

- Goal: Define the declarative evaluation governance shape for workflow files.
- Acceptance criteria:
  - Evaluation schema fields are documented before implementation.
  - Schema covers categories, required metrics, thresholds, evidence references,
    and compliance status.
  - Schema explicitly states that PolicyFlow does not run evaluation tooling.
- Affected files:
  - `docs/roadmap-agentic-governance.md`
  - `docs/schema-compatibility.md`
  - `workflows/templates/*.yml`
- Risk level: MEDIUM
- Dependencies:
  - ADR-0003 accepted.
- Suggested labels:
  - `governance`
  - `schema`
  - `evaluation`

### Add evaluation model

- Goal: Add typed models for evaluation governance.
- Acceptance criteria:
  - Evaluation model supports metric name, source, threshold, actual value or
    status, evidence reference, and blocking state.
  - Models remain provider-neutral and runtime-neutral.
  - Public compatibility expectations are documented.
- Affected files:
  - `policyflow/models.py`
  - `policyflow/schemas.py`
  - `tests/test_validator.py`
- Risk level: MEDIUM
- Dependencies:
  - Define evaluation schema.
- Suggested labels:
  - `governance`
  - `schema`
  - `validation`

### Validate evaluation requirements

- Goal: Validate required evaluation governance fields.
- Acceptance criteria:
  - Missing required evaluation fields produce clear errors.
  - Risk-based evaluation requirements are enforced where defined.
  - Evaluation failures can be modeled without implying PolicyFlow executed the
    underlying checks.
- Affected files:
  - `policyflow/validator.py`
  - `tests/test_validator.py`
  - `tests/fixtures/`
- Risk level: MEDIUM
- Dependencies:
  - Add evaluation model.
- Suggested labels:
  - `governance`
  - `validation`
  - `evaluation`

### Add evaluation examples

- Goal: Add valid and invalid evaluation governance examples.
- Acceptance criteria:
  - Example workflows demonstrate tests, coverage, review score, security
    findings, and performance gates.
  - Invalid fixtures cover missing evidence and threshold mismatches.
  - Examples avoid provider-specific assumptions.
- Affected files:
  - `workflows/examples/`
  - `workflows/templates/`
  - `tests/fixtures/`
- Risk level: MEDIUM
- Dependencies:
  - Validate evaluation requirements.
- Suggested labels:
  - `examples`
  - `evaluation`
  - `docs`

### Document evaluation governance

- Goal: Document how Consumer-Repos should use Evaluation Governance.
- Acceptance criteria:
  - Documentation explains scope, non-scope, required fields, evidence, and
    examples.
  - Documentation states that CI, scanners, and test tooling remain external.
  - Getting-started guidance links to the evaluation documentation when
    evaluation schemas ship.
- Affected files:
  - `docs/evaluation-governance.md`
  - `docs/getting-started.md`
  - `README.md`
- Risk level: LOW
- Dependencies:
  - Add evaluation examples.
- Suggested labels:
  - `docs`
  - `evaluation`

## v1.2 - Loop Governance Foundation

### Define loop governance schema

- Goal: Define declarative feedback-loop governance.
- Acceptance criteria:
  - Schema covers source phase, target phase, allowed feedback sources,
    `max_iterations`, stop conditions, escalation conditions, and evidence.
  - Schema explicitly excludes loop execution, scheduling, message routing, and
    memory.
  - Schema compatibility impact is documented.
- Affected files:
  - `docs/roadmap-agentic-governance.md`
  - `docs/schema-compatibility.md`
  - `workflows/templates/*.yml`
- Risk level: MEDIUM
- Dependencies:
  - ADR-0003 accepted.
- Suggested labels:
  - `governance`
  - `schema`
  - `loops`

### Add loop model

- Goal: Add typed models for Loop Governance.
- Acceptance criteria:
  - Model supports loop identity, phases, feedback sources, iteration limits,
    stop conditions, escalation conditions, evidence references, and status.
  - Model remains separate from runtime execution concerns.
  - Tests cover valid and invalid loop declarations.
- Affected files:
  - `policyflow/models.py`
  - `policyflow/schemas.py`
  - `tests/test_validator.py`
- Risk level: MEDIUM
- Dependencies:
  - Define loop governance schema.
- Suggested labels:
  - `governance`
  - `schema`
  - `loops`

### Validate max_iterations

- Goal: Enforce loop iteration limits structurally.
- Acceptance criteria:
  - `max_iterations` must be a positive integer.
  - Current iteration count cannot exceed `max_iterations`.
  - Validation messages distinguish declaration errors from compliance failures.
- Affected files:
  - `policyflow/validator.py`
  - `tests/test_validator.py`
  - `tests/fixtures/`
- Risk level: MEDIUM
- Dependencies:
  - Add loop model.
- Suggested labels:
  - `validation`
  - `loops`

### Validate stop_conditions

- Goal: Require explicit stop conditions for governed loops.
- Acceptance criteria:
  - Each loop declares non-empty stop conditions.
  - Completed or terminated loop evidence references at least one stop condition.
  - Missing stop conditions produce clear validator errors.
- Affected files:
  - `policyflow/validator.py`
  - `tests/test_validator.py`
  - `tests/fixtures/`
- Risk level: MEDIUM
- Dependencies:
  - Add loop model.
- Suggested labels:
  - `validation`
  - `loops`

### Validate escalation rules

- Goal: Require explicit escalation rules for governed loops.
- Acceptance criteria:
  - Each loop declares escalation conditions.
  - Escalated loop states require escalation evidence.
  - Protected-area or high-risk loops cannot hide escalation requirements.
- Affected files:
  - `policyflow/validator.py`
  - `rules/escalation-rules.md`
  - `tests/test_validator.py`
- Risk level: MEDIUM
- Dependencies:
  - Validate stop_conditions.
- Suggested labels:
  - `validation`
  - `loops`
  - `human-governance`

### Add loop governance examples

- Goal: Add examples for review, QA, security, and human arbitration loops.
- Acceptance criteria:
  - Examples show loop declarations without runtime execution.
  - Fixtures cover max iteration, stop condition, and escalation failures.
  - Examples include Querypilot-inspired SQL safety loops.
- Affected files:
  - `workflows/examples/`
  - `tests/fixtures/`
  - `docs/loop-governance.md`
- Risk level: MEDIUM
- Dependencies:
  - Validate escalation rules.
- Suggested labels:
  - `examples`
  - `loops`
  - `docs`

### Document loop governance

- Goal: Document Loop Governance usage and boundaries.
- Acceptance criteria:
  - Documentation explains scope, non-scope, loop fields, evidence, and
    escalation expectations.
  - Documentation explicitly states that PolicyFlow does not execute loops.
  - README or getting-started docs link to Loop Governance after the schema
    ships.
- Affected files:
  - `docs/loop-governance.md`
  - `docs/getting-started.md`
  - `README.md`
- Risk level: LOW
- Dependencies:
  - Add loop governance examples.
- Suggested labels:
  - `docs`
  - `loops`

## v1.3 - Metrics & Evidence

### Define metrics schema

- Goal: Define a reusable metric representation for Evaluation Governance.
- Acceptance criteria:
  - Schema supports metric name, category, source, expected threshold, observed
    value, status, and evidence reference.
  - Schema supports domain-specific metrics without making them globally
    mandatory.
  - Backward compatibility considerations are documented.
- Affected files:
  - `docs/schema-compatibility.md`
  - `policyflow/models.py`
  - `tests/test_validator.py`
- Risk level: MEDIUM
- Dependencies:
  - v1.1 Evaluation Foundation.
- Suggested labels:
  - `metrics`
  - `schema`
  - `evaluation`

### Add metric evidence references

- Goal: Link metrics to concrete evidence blocks or external artifacts.
- Acceptance criteria:
  - Metrics can reference workflow evidence or external evidence identifiers.
  - Validator detects missing required metric evidence references.
  - Documentation explains expected Consumer-Repo evidence ownership.
- Affected files:
  - `policyflow/validator.py`
  - `docs/evaluation-governance.md`
  - `tests/fixtures/`
- Risk level: MEDIUM
- Dependencies:
  - Define metrics schema.
- Suggested labels:
  - `metrics`
  - `evidence`
  - `validation`

### Validate required metrics by risk level

- Goal: Define which metric categories are required by risk level.
- Acceptance criteria:
  - LOW, MEDIUM, and HIGH expectations are documented.
  - Validator enforces required metric categories when enabled by schema.
  - HIGH-risk requirements preserve human approval as mandatory.
- Affected files:
  - `rules/risk-review-matrix.md`
  - `policyflow/validator.py`
  - `tests/test_validator.py`
- Risk level: HIGH
- Dependencies:
  - Add metric evidence references.
- Suggested labels:
  - `metrics`
  - `risk-governance`
  - `validation`

### Add review score and QA metric examples

- Goal: Demonstrate practical metrics for review and QA governance.
- Acceptance criteria:
  - Examples include review score, QA pass status, test pass rate, coverage, and
    unresolved risk metrics.
  - Examples remain provider-neutral.
  - Fixtures include both compliant and non-compliant cases.
- Affected files:
  - `workflows/examples/`
  - `tests/fixtures/`
  - `docs/evaluation-governance.md`
- Risk level: MEDIUM
- Dependencies:
  - Validate required metrics by risk level.
- Suggested labels:
  - `examples`
  - `metrics`
  - `qa`

### Document metric governance

- Goal: Explain how metrics relate to evidence and risk.
- Acceptance criteria:
  - Documentation distinguishes metric declaration, metric source, metric
    evidence, and PolicyFlow validation.
  - Documentation clarifies that PolicyFlow does not calculate all metrics.
  - Querypilot metric examples are linked.
- Affected files:
  - `docs/metric-governance.md`
  - `docs/roadmap-agentic-governance.md`
- Risk level: LOW
- Dependencies:
  - Add review score and QA metric examples.
- Suggested labels:
  - `docs`
  - `metrics`

## v1.4 - Audit & Reporting

### Extend policyflow audit output

- Goal: Include loop and evaluation governance summaries in audit output.
- Acceptance criteria:
  - Existing workflow audit output remains backward compatible.
  - Audit output summarizes missing or failing loop and evaluation governance.
  - JSON output includes machine-readable compliance fields.
- Affected files:
  - `policyflow/reporting.py`
  - `policyflow/cli.py`
  - `tests/test_repository_docs.py`
  - `tests/test_validator.py`
- Risk level: MEDIUM
- Dependencies:
  - v1.2 Loop Governance Foundation.
  - v1.3 Metrics & Evidence.
- Suggested labels:
  - `audit`
  - `reporting`
  - `governance`

### Add evaluation compliance report

- Goal: Report evaluation governance compliance across workflow files.
- Acceptance criteria:
  - Report identifies missing required evaluations, failing gates, and missing
    evidence references.
  - Report is available through CLI and JSON output.
  - Tests cover compliant and non-compliant directories.
- Affected files:
  - `policyflow/reporting.py`
  - `policyflow/cli.py`
  - `tests/test_runtime_cli.py`
- Risk level: MEDIUM
- Dependencies:
  - Extend policyflow audit output.
- Suggested labels:
  - `audit`
  - `evaluation`
  - `reporting`

### Add loop compliance report

- Goal: Report loop governance compliance across workflow files.
- Acceptance criteria:
  - Report identifies exceeded iterations, missing stop evidence, missing
    escalation evidence, and unresolved blocked loops.
  - Report is available through CLI and JSON output.
  - Tests cover review-loop and QA-loop examples.
- Affected files:
  - `policyflow/reporting.py`
  - `policyflow/cli.py`
  - `tests/test_runtime_cli.py`
- Risk level: MEDIUM
- Dependencies:
  - Extend policyflow audit output.
- Suggested labels:
  - `audit`
  - `loops`
  - `reporting`

### Add machine-readable audit JSON

- Goal: Stabilize machine-readable audit fields for downstream reporting.
- Acceptance criteria:
  - JSON shape is documented.
  - Existing workflow audit consumers remain compatible or receive migration
    guidance.
  - Output covers workflow, loop, evaluation, and human governance statuses.
- Affected files:
  - `docs/public-api.md`
  - `docs/schema-compatibility.md`
  - `policyflow/reporting.py`
- Risk level: MEDIUM
- Dependencies:
  - Add evaluation compliance report.
  - Add loop compliance report.
- Suggested labels:
  - `audit`
  - `api`
  - `compatibility`

### Document audit reporting

- Goal: Document audit and reporting usage for Agentic Governance.
- Acceptance criteria:
  - Documentation explains local and CI usage.
  - Documentation includes workflow, loop, evaluation, and human governance
    examples.
  - Documentation distinguishes audit reporting from runtime execution.
- Affected files:
  - `docs/audit-reporting.md`
  - `docs/getting-started.md`
  - `README.md`
- Risk level: LOW
- Dependencies:
  - Add machine-readable audit JSON.
- Suggested labels:
  - `docs`
  - `audit`

## v2.0 - Agentic Governance Platform

### Stabilize workflow, loop, and evaluation schemas

- Goal: Declare stable governance schema boundaries for v2.
- Acceptance criteria:
  - Workflow, loop, evaluation, and human governance schemas are documented.
  - Breaking changes from `0.x` are listed with migration steps.
  - Public API expectations are updated.
- Affected files:
  - `docs/schema-compatibility.md`
  - `docs/public-api.md`
  - `policyflow/models.py`
- Risk level: HIGH
- Dependencies:
  - v1.4 Audit & Reporting.
- Suggested labels:
  - `v2`
  - `schema`
  - `compatibility`

### Publish v2 migration guide

- Goal: Guide Consumer-Repos from `0.x` schemas to stable v2 governance.
- Acceptance criteria:
  - Migration guide covers workflow, loop, evaluation, metric, and audit changes.
  - Guide includes before and after examples.
  - Guide identifies deprecated fallback behavior.
- Affected files:
  - `docs/v2-migration-guide.md`
  - `docs/release-and-upgrade.md`
- Risk level: HIGH
- Dependencies:
  - Stabilize workflow, loop, and evaluation schemas.
- Suggested labels:
  - `v2`
  - `docs`
  - `migration`

### Document provider-neutral integration contract

- Goal: Define how external runtimes, CI systems, and agent frameworks provide
  governance evidence to PolicyFlow.
- Acceptance criteria:
  - Contract covers workflow evidence, loop evidence, evaluation evidence, and
    human governance evidence.
  - Contract avoids provider SDK requirements.
  - Contract clarifies that PolicyFlow validates and reports but does not
    execute external systems.
- Affected files:
  - `docs/provider-neutral-integration-contract.md`
  - `docs/runner-contract.md`
  - `docs/public-api.md`
- Risk level: MEDIUM
- Dependencies:
  - Stabilize workflow, loop, and evaluation schemas.
- Suggested labels:
  - `integration`
  - `provider-neutral`
  - `docs`

### Add reference consumer project

- Goal: Provide a maintained reference Consumer-Repo path for v2 governance.
- Acceptance criteria:
  - Reference path demonstrates bootstrap, doctor, workflow validation, loop
    governance, evaluation governance, and audit reporting.
  - Reference does not require a hosted runtime or provider credentials.
  - Golden smoke tests cover the reference path.
- Affected files:
  - `examples/`
  - `tests/test_golden_consumer_smoke.py`
  - `docs/getting-started.md`
- Risk level: MEDIUM
- Dependencies:
  - Document provider-neutral integration contract.
- Suggested labels:
  - `examples`
  - `consumer-repo`
  - `v2`

### Add Querypilot pilot documentation

- Goal: Document Querypilot as the first pilot for Loop and Evaluation
  Governance.
- Acceptance criteria:
  - Documentation lists Querypilot governance goals, metrics, loops, evidence,
    and non-goals.
  - Documentation includes SQL guardrail, SELECT-only, executable SQL, tests,
    coverage, latency, review score, and security findings examples.
  - Documentation clarifies which parts belong in Querypilot versus PolicyFlow.
- Affected files:
  - `docs/querypilot-pilot.md`
  - `docs/roadmap-agentic-governance.md`
  - `workflows/examples/`
- Risk level: LOW
- Dependencies:
  - Add reference consumer project.
- Suggested labels:
  - `docs`
  - `querypilot`
  - `pilot`

