# Querypilot Pilot

Querypilot is the first PolicyFlow pilot for Loop Governance and Evaluation
Governance. It is a good pilot because natural-language requests can produce
SQL, and SQL output can be checked with concrete, provider-neutral evidence.

PolicyFlow validates and reports the declared governance state. Querypilot owns
SQL parsing, SQL guardrail checks, execution evidence, runtime behavior,
credentials, benchmarks, and domain-specific quality calculations.

## Governance Goals

The Querypilot pilot should prove that a Consumer-Repo can use PolicyFlow to:

- declare SQL safety expectations before implementation starts
- connect generated SQL quality to measurable evaluation metrics
- make review, QA, security, and human arbitration loops explicit
- show which evidence blocks and artifacts support merge readiness
- keep SQL execution, provider credentials, and runtime orchestration outside
  PolicyFlow

## Metrics

Candidate Querypilot metrics should remain provider-neutral and evidence-backed:

- SQL guardrail status
- SELECT-only status
- executable SQL status
- tests and test pass rate
- coverage threshold
- latency, such as p95 response latency
- review score
- security findings

The canonical example is
`workflows/examples/querypilot-pilot-workflow.yml`. It declares these metrics in
the `evaluation` block and points them to workflow evidence or artifact refs.

## Loops

Querypilot can use Loop Governance for bounded feedback when generated SQL is
unsafe, non-executable, slow, ambiguous, or insufficiently reviewed.

Useful loops include:

- SQL safety loop for SQL guardrail failures
- QA loop for non-executable SQL
- review loop for low review score or unclear query intent
- security loop for security findings
- human arbitration loop for ambiguous data access or protected-table concerns

PolicyFlow records and validates these declarations. Querypilot or its
Consumer-Repo automation owns the actual feedback loop execution.

## Evidence

Querypilot evidence should make external checks reviewable without embedding SQL
or provider logic in PolicyFlow.

Recommended evidence sources:

- `evidence.qa` for executable SQL, tests, coverage, and latency summaries
- `evidence.review` for human review score and intent review
- `evidence.security` for SQL guardrail and security findings summaries
- `artifact://querypilot-sql-guardrail-report`
- `artifact://querypilot-executable-sql-report`
- `artifact://querypilot-coverage-report`
- `artifact://querypilot-latency-report`
- `artifact://querypilot-security-report`

PolicyFlow can validate that required `evidence.*` references exist and that
declared simple thresholds are satisfied by the values in the workflow.

## Non-Goals

The pilot does not make PolicyFlow responsible for:

- SQL generation
- SQL parsing
- SQL guardrail implementation
- query execution
- database connectivity
- provider SDK integration
- hosted runtime behavior
- scheduling feedback loops
- storing memory
- managing Querypilot credentials

PolicyFlow does not execute SQL. It validates and reports governance metadata
that Querypilot and its Consumer-Repo produce.

## Responsibility Split

Querypilot owns:

- natural-language-to-SQL behavior
- SQL guardrail implementation
- SELECT-only enforcement
- executable SQL checks
- database or sandbox execution
- test, coverage, latency, review, and security evidence production
- domain-specific thresholds and artifact storage

PolicyFlow owns:

- workflow structure validation
- loop governance declaration validation
- evaluation and metric declaration validation
- evidence reference validation
- audit, evaluation, and loop reporting
- PR body and approval claim validation when the Consumer-Repo enables them

