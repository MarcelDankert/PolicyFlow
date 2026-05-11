# Confidence Governance

## Purpose

Use confidence as a reporting and escalation signal, not as an approval substitute.

## Dimensions

- implementation confidence
- architecture alignment confidence
- test completeness confidence
- contract safety confidence

## Thresholds

- LOW: `0.75`
- MEDIUM: `0.85`
- HIGH: advisory only, never sufficient on its own

## Rules

- confidence must be evaluated together with risk and scope
- review and QA remain necessary even with high confidence
- low confidence is an escalation signal
- HIGH-risk work always requires human approval
