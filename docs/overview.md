# Overview

PolicyFlow is a reusable governance and lightweight workflow orchestration layer
for agent-assisted software delivery.

It gives a Consumer-Repo:

- a common vocabulary for risk, confidence, evidence, and approval
- role definitions for planning, architecture, implementation, review, and QA
- explicit workflow phase state, runtime state, and handoffs
- typed overrides for approved exceptions
- bootstrap, doctor, sync, and workflow generation commands
- provider-neutral runner execution through a command contract
- GitHub issue, PR, and governance workflow templates
- local and CI validation for workflow files, PR bodies, and GitHub approvals

PolicyFlow is not a hosted scheduler, merge bot, or provider credential manager.
It owns workflow governance and state transitions while Consumer-Repos own their
domain context, implementation, and provider runtime setup.
