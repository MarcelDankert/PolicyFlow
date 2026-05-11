# Risk Classification

## Purpose

Classify changes before implementation so workflow strictness matches real operational risk.

## LOW

Typical examples:
- documentation
- comments
- non-critical refactors
- test improvements
- dashboard-only changes with no control impact

## MEDIUM

Typical examples:
- API changes
- database access layer changes without schema changes
- runtime or deployment configuration changes
- observability integration changes
- internal contract changes

## HIGH

Typical examples:
- protected business logic
- critical execution boundary changes
- database schema changes
- contracts
- secrets, IAM, or security controls
- deployment pipeline changes
- architecture boundary changes

## Rules

- Use the highest applicable risk level.
- Confidence cannot downgrade risk.
- Protected areas default to HIGH unless explicitly justified otherwise.
- Required reviews are governed by `rules/risk-review-matrix.md`.
