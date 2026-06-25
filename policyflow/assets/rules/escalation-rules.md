# Escalation Rules

## Escalate Immediately When

- risk level is unclear or appears understated
- protected areas are touched without approval path
- confidence falls below threshold
- architecture signals conflict
- contract ownership is unclear
- runtime impact is uncertain
- data integrity impact is uncertain
- scope expands
- tests fail repeatedly without convergence
- required reviews are weaker than `rules/risk-review-matrix.md`
- LOW-risk fast-path eligibility is lost
- loop governance is declared without explicit escalation conditions
- a loop is marked escalated without evidence that references a declared
  escalation condition

## Default Safety Rule

- prefer the safer classification
- escalate early instead of guessing
- treat loop escalation rules as governance metadata only; do not execute,
  schedule, route, or retry loop work from these rules
