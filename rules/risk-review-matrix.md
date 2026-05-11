# Risk Review Matrix

## Purpose

This is the normative source of truth for required reviews and approval depth.

## LOW

Required reviews:
- `review-agent`

QA:
- optional unless behavior, runtime expectations, or validation flow changed

Human approval:
- not required by default

Confidence threshold:
- `0.75`

Preferred workflow path:
- `workflows/templates/low-risk-workflow.template.yml`

## MEDIUM

Required reviews:
- `architecture-agent`
- `review-agent`
- `qa-agent`

Human approval:
- only if escalation triggered

Confidence threshold:
- `0.85`

## HIGH

Required reviews:
- `architecture-agent`
- `review-agent`
- `qa-agent`
- human approval

Human approval:
- always required

Confidence:
- advisory only
- confidence cannot bypass approval

## Workflow Rule

Any workflow is invalid if:
- `required_reviews` is weaker than this matrix
- `human_approval_required` is weaker than this matrix
- a LOW-risk fast path is used for MEDIUM or HIGH work
