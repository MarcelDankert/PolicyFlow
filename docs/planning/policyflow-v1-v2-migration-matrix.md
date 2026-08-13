# PolicyFlow V1 to V2 Migration Matrix

PolicyFlow 2.0 is a breaking release. This matrix defines the intended treatment of V1 capabilities and fields. The goal is bounded migration diagnostics, not indefinite backward compatibility.

| V1 Capability / Field | V2 Decision | New Representation | Migration Action | Breaking Risk |
| --- | --- | --- | --- | --- |
| `workflow.id` | RENAME | `change.id` | Move the stable change identifier to `change.id`. | MEDIUM |
| `workflow.type` | RENAME | `change.type` | Map existing workflow type to V2 change type where possible. | MEDIUM |
| `workflow` metadata object | RENAME | `change` | Replace workflow-centric terminology with change governance terminology. | MEDIUM |
| `context.workflow_file` | REMOVE | PR body `Change file` reference and file path supplied to CLI | Do not store self-referential path in schema; PR validation checks supplied path and PR claim. | MEDIUM |
| `context.risk_level` | RENAME | `risk.level` | Convert `LOW/MEDIUM/HIGH` to `low/medium/high`. | MEDIUM |
| `context.confidence.planning` | SIMPLIFY | `confidence.summary` | Collapse phase-specific confidence into one governance confidence summary. | MEDIUM |
| `context.confidence.implementation` | SIMPLIFY | `confidence.summary` | Merge useful uncertainty into summary. | MEDIUM |
| `context.confidence.tests` | SIMPLIFY | evidence entries with `type: test` | Represent test confidence as external evidence. | MEDIUM |
| `context.confidence.residual_uncertainty` | SIMPLIFY | `confidence.summary` or evidence notes | Preserve only if it affects governance decision. | MEDIUM |
| `context` object | REBUILD | `change`, `risk`, `confidence` | Split V1 context into explicit V2 governance concepts. | HIGH |
| `governance.required_reviews` | KEEP | `governance.required_reviews` | Preserve concept; role names may become repository-defined review identifiers. | LOW |
| `governance.human_approval_required` | KEEP | `governance.human_approval_required` | Preserve as core human-in-the-loop control. | LOW |
| `governance.escalation_required` | SIMPLIFY | derived from `risk.protected_areas` and policies, or evidence/override | Remove unless it changes a governance decision beyond risk/protected areas. | MEDIUM |
| `governance.protected_areas_touched` | RENAME | `risk.protected_areas` | Move protected-area declaration under risk. | MEDIUM |
| `governance.approval_evidence` | SIMPLIFY | evidence entry with `type: approval` | Replace descriptive list with structured evidence item. | MEDIUM |
| `governance` object | KEEP | `governance` | Keep only required reviews and human approval requirement by default. | LOW |
| `execution.mode` | REMOVE | none | Strict execution mode is a workflow engine concern. | HIGH |
| `execution.phases` | REMOVE | none by default | Phase state is removed unless a future issue proves direct governance value. | HIGH |
| `execution` object | REMOVE | none | V2 validates evidence and merge readiness, not phase transitions. | HIGH |
| `contracts.planning` | MOVE | external evidence | Planning output may be evidence, but PolicyFlow does not own agent role contracts. | HIGH |
| `contracts.architecture-check` | MOVE | external evidence | Architecture review becomes evidence/review entry if required. | HIGH |
| `contracts.implementation` | MOVE | external evidence | Implementation details remain outside core schema. | HIGH |
| `contracts.review` | MOVE | external evidence and PR review data | Review contract becomes evidence or GitHub review validation. | HIGH |
| `contracts.qa` | MOVE | external evidence | QA output becomes evidence produced by CI/human/external tools. | HIGH |
| `contracts.owner_agent` | REMOVE | none | Agent identity is execution ownership. | HIGH |
| `contracts` object | MOVE | external evidence | Produce normalized evidence outside PolicyFlow. | HIGH |
| `runtime.status` | REMOVE | validation result status | Runtime state is replaced by PolicyFlow's own validation result: `PASS/WARN/BLOCK`. | HIGH |
| `runtime.current_phase` | REMOVE | none | Current phase is workflow engine state. | HIGH |
| `runtime.active_agent` | REMOVE | none | Active agent is execution state. | HIGH |
| `runtime.last_transition` | REMOVE | external runtime logs | Transition history belongs to external runtimes. | HIGH |
| `runtime.block_reason` | SIMPLIFY | validation diagnostics or evidence status | Blocking governance reasons are diagnostics, not persisted runtime state. | HIGH |
| `runtime` object | REMOVE | none | Core V2 has no runtime state. | HIGH |
| `handoffs.from_phase` | MOVE | external runtime evidence | Handoff source belongs to runtime/workflow tooling. | HIGH |
| `handoffs.to_phase` | MOVE | external runtime evidence | Handoff target belongs to runtime/workflow tooling. | HIGH |
| `handoffs.status` | MOVE | external runtime evidence | Handoff status is runtime state. | HIGH |
| `handoffs.required_inputs` | SIMPLIFY | required evidence IDs | Keep only when represented as evidence requirements. | HIGH |
| `handoffs.produced_outputs` | SIMPLIFY | evidence IDs | Produced outputs become evidence entries. | HIGH |
| `handoffs.blockers` | SIMPLIFY | validation diagnostics or evidence status | Blocking facts become evidence status or diagnostics. | HIGH |
| `handoffs.override_refs` | SIMPLIFY | `overrides` referenced from evidence/PR | Preserve only as governance exception references. | HIGH |
| `handoffs` object | MOVE | external runtime evidence | First-class handoff state leaves core. | HIGH |
| `loop_governance.loops` | MOVE | external runtime or evidence policy | Loop execution and state live outside PolicyFlow. | HIGH |
| `loop_governance.current_iteration` | REMOVE | none | Current iteration is runtime state. | HIGH |
| `loop_governance.max_iterations` | MOVE | external runtime policy | May be validated by external runtime; not V2 core. | MEDIUM |
| `loop_governance.stop_conditions` | MOVE | external runtime policy/evidence | Represent final result as evidence if governance requires it. | MEDIUM |
| `loop_governance.escalation_conditions` | MOVE | external runtime policy/evidence | Represent escalation as evidence or override if it affects merge readiness. | MEDIUM |
| `loop_governance.status` | REMOVE | evidence status if needed | Loop status is not a core governance concept. | HIGH |
| `loop_governance` object | MOVE | external runtime/evidence | V2 core does not model loop state. | HIGH |
| `evaluation.compliance_status` | SIMPLIFY | validation result and evidence statuses | Overall compliance is computed by PolicyFlow from evidence, not stored as metric object. | MEDIUM |
| `evaluation.categories` | SIMPLIFY | evidence `type` and repository policy | Categories may map to evidence types such as `test`, `security`, `review`. | MEDIUM |
| `evaluation.required_metrics` | MOVE | external analytics or CI evidence | Metrics are produced outside PolicyFlow. | HIGH |
| `evaluation.thresholds` | MOVE | CI/security/performance tooling | Threshold calculation is outside core. | HIGH |
| `evaluation.actual_value` | REMOVE | external evidence reference | PolicyFlow does not calculate or store analytics values. | HIGH |
| `evaluation.blocks_merge` | SIMPLIFY | evidence `status` plus governance rule | Blocking behavior is derived from required evidence status. | MEDIUM |
| `evaluation` object | SIMPLIFY | `evidence` list | Replace with normalized evidence entries. | HIGH |
| `overrides.id` | KEEP | `overrides[].id` | Preserve stable exception IDs. | LOW |
| `overrides.type` | SIMPLIFY | `risk_exception`, `approval_exception`, `evidence_exception`, `scope_exception` | Reduce override type set. | MEDIUM |
| `overrides.reason` | KEEP | `overrides[].reason` | Preserve required justification. | LOW |
| `overrides.scope_impact` | SIMPLIFY | `reason` or type-specific fields | Keep only if validation uses it. | MEDIUM |
| `overrides.risk_impact` | SIMPLIFY | `reason` or type-specific fields | Keep only if validation uses it. | MEDIUM |
| `overrides.mitigations` | SIMPLIFY | evidence or reason | Preserve only if it affects governance. | MEDIUM |
| `overrides.approved_by` | KEEP | `overrides[].approved_by` | Preserve approval identity for exception governance. | LOW |
| `overrides.approval_reference` | RENAME | `overrides[].approval_ref` | Use shorter evidence reference naming. | LOW |
| `overrides.review_by` | KEEP | `overrides[].review_by` | Preserve lifecycle check. | LOW |
| `overrides.expires_on` | KEEP | `overrides[].expires_on` | Preserve lifecycle check. | LOW |
| `phase_bypass` override | REMOVE | none | Phase bypass is a workflow engine concept. | HIGH |
| `approval_bypass` override | RENAME | `approval_exception` | Keep governance concept, simplify name. | MEDIUM |
| `non_goal_exception` override | SIMPLIFY | `scope_exception` | Fold into scope exception if needed. | MEDIUM |
| evidence block keyed by phase | SIMPLIFY | `evidence[]` list | Convert phase evidence to normalized evidence items. | HIGH |
| `evidence.planning` | SIMPLIFY | evidence item with `type: planning` or governance summary | Keep only if repository policy requires planning evidence. | MEDIUM |
| `evidence.architecture-check` | SIMPLIFY | evidence item with `type: review` or `architecture` | Preserve as review evidence if required by risk. | MEDIUM |
| `evidence.review` | KEEP/SIMPLIFY | evidence item with `type: review` | Convert to normalized evidence item. | MEDIUM |
| `evidence.qa` | SIMPLIFY | evidence item with `type: test` or `qa` | Convert to external evidence. | MEDIUM |
| `evidence.approval` | KEEP/SIMPLIFY | evidence item with `type: approval` plus GitHub review validation | Preserve human approval governance. | MEDIUM |
| runner config `policyflow.runners.yml` | REMOVE | external runtime config | Move to Sentinel-AI-Core, consumer tooling, or adapters. | HIGH |
| agent assets | MOVE | external runtime or consumer repo | Do not package or generate by default. | MEDIUM |
| prompt assets | MOVE | external runtime or consumer repo | Do not package or generate by default. | MEDIUM |
| `run-phase` command | MOVE | external runtime command | PolicyFlow validates evidence produced by the runtime. | HIGH |
| `start-phase` command | MOVE | external runtime/workflow tooling | Remove from core CLI. | HIGH |
| `complete-phase` command | MOVE | external runtime/workflow tooling | Remove from core CLI. | HIGH |
| `block-phase` command | MOVE | external runtime/workflow tooling | Remove from core CLI. | HIGH |
| `record-handoff` command | MOVE | external runtime/workflow tooling | Remove from core CLI. | HIGH |
| `next-step` command | MOVE | external runtime/workflow tooling | Remove from core CLI. | MEDIUM |
| `handoff-status` command | MOVE | external runtime/workflow tooling | Remove from core CLI. | MEDIUM |
| `status` command | REMOVE | `validate --json` | Merge-readiness summary is part of validation output. | MEDIUM |
| `audit` command | REMOVE | external analytics or batch validation | Do not preserve audit architecture in core. | MEDIUM |
| `evaluation-report` command | REMOVE | external analytics/reporting | Outside reporting boundary. | MEDIUM |
| `loop-report` command | REMOVE | external runtime/analytics | Outside reporting boundary. | MEDIUM |
| `sync` command | REMOVE | release notes/manual migration | Managed asset synchronization removed. | MEDIUM |
| `new-workflow` command | REMOVE | example file or external scaffolding | V2 init provides an example, not generator subsystem. | MEDIUM |
| `config-check` command | REMOVE/FOLD | `doctor` | Doctor owns readiness checks. | LOW |
| `validate-github-approvals` command | RENAME/FOLD | `validate-pr --github-reviews` | Keep capability as PR governance option, not separate command. | LOW |
| runtime Python API | REMOVE | none | Public API is governance-only. | HIGH |
| `audit_workflows` API | REMOVE/SIMPLIFY | validation JSON or external reporting | No stable audit v1 compatibility in V2. | MEDIUM |
| `get_workflow_status` API | REMOVE/SIMPLIFY | validation result merge-readiness | Replace with validation result. | MEDIUM |
| Codex runner module | MOVE | external Codex adapter | Remove from core package. | MEDIUM |
| GitHub approval validation | KEEP/SIMPLIFY | `github.py` and `validate-pr --github-reviews` | Keep read-only approval evidence validation. | LOW |
| bootstrap assets | REBUILD | minimal V2 init assets | Remove runtime, runner, agent, prompt, sync, and large template assets. | HIGH |
| `.policyflow/bootstrap.json` | REMOVE | none | No managed asset sync metadata. | MEDIUM |
| GitHub Actions workflow | KEEP/SIMPLIFY | read-only V2 validation workflow | Keep only read-only PR/evidence checks. | MEDIUM |
| PR template | KEEP/SIMPLIFY | concise V2 PR template | Keep fields that validation needs. | LOW |
| issue templates | REMOVE by default | optional external repo conventions | Not required for merge governance. | LOW |
| top-level/package asset mirrors | REBUILD | one source of truth | Remove drift and package only V2 governance assets. | MEDIUM |

## Migration Diagnostics

V2 validation should produce actionable diagnostics for V1 files:

- `context.risk_level` -> `risk.level`.
- `workflow.id` -> `change.id`.
- `workflow.type` -> `change.type`.
- `governance.protected_areas_touched` -> `risk.protected_areas`.
- `evidence.<phase>` -> `evidence[]` item.
- `runtime` is removed; external systems own runtime state.
- `handoffs` are removed; external systems own handoff state.
- `contracts` are moved to external evidence.
- `evaluation` is simplified into evidence; metric calculation is external.
- `loop_governance` is moved outside core.

Diagnostics should identify the field path, V2 decision, and migration action.

## Migration Command Decision

No `policyflow migrate` command is included in the initial V2 plan.

Reason:

- The V2 schema is intentionally much smaller.
- Runtime, handoff, contract, loop, and evaluation fields require product decisions that cannot be safely auto-converted.
- Diagnostics and documentation have lower long-term maintenance cost.

Reconsider a migration command only after testing real V1 repositories shows repeated mechanical conversions with low ambiguity.

