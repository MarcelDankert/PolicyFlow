## Summary
Implements a bounded PolicyFlow change.

## Linked Issue
#1

## Workflow File
- `workflows/examples/valid-medium.yml`

## Scope
- In scope: bounded workflow validation
- Out of scope: unrelated changes
- Allowed in this PR: small same-scope workflow clarifications
- Not allowed in this PR: silent scope, risk, or non-goal expansion

## Non-Goals
- no unrelated changes

## Governance
- Declared risk level: MEDIUM
- Required reviews completed: architecture-agent, review-agent, qa-agent
- Human approval login if required:
- Human approval reference if required:
- Escalation notes: none
- Protected areas touched: none

## Evidence
- Planning evidence: `evidence.planning`
- Architecture evidence: `evidence.architecture-check`
- Review evidence: n/a
- QA evidence: n/a
- Approval evidence: n/a

## Overrides
- Override ID: phase-bypass-1
- Override type: phase_bypass
- Approved by login: architecture-agent
- Approval reference: ARCH-OVERRIDE-1
- Mitigations confirmed: yes

## Confirmation
- [x] The implementation matches the declared scope
- [x] Non-goals were respected
- [x] The linked workflow file governed this change
- [x] The workflow file existed before implementation and governed the work from the start
- [x] Scope, non-goals, and risk were fixed in the workflow before implementation started
- [x] Required workflow phases were executed as visible working steps, not only documented after the fact

## Tests
```text
pytest -q
```

## Docs
- [ ] Docs updated
- [x] No docs update needed
