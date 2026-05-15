# Governance Enforcement Roadmap

## Current Enforcement

- workflow YAML validation
- `workflow` metadata validation
- `context.workflow_file` validation
- `context.risk_level` validation
- `governance.required_reviews` validation
- risk-review matrix validation
- `HIGH` human approval validation
- `HIGH` approval evidence validation
- protected-area escalation validation
- CLI support via `policyflow validate <workflow.yml>`
- PR body completeness validation via `policyflow validate-pr <workflow.yml> <pr-body.md>`

## Current Fail Conditions

- HIGH risk without human approval
- HIGH risk without approval evidence
- missing `workflow_file`
- missing `required_reviews`
- weaker-than-matrix review requirements
- protected area touched without escalation
- protected area touched outside `HIGH` risk
- PR body missing linked issue
- PR body workflow path mismatches the workflow file
- PR body declared risk level mismatches the workflow file
- PR body does not confirm workflow governance

## Next Planned Enforcement

- workflow file reference validation against PR metadata
- schema normalization after more real consumer usage
- GitHub API-based PR validation after the markdown-file workflow is validated in practice
