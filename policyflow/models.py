from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ExecutionMode(str, Enum):
    STRICT = "strict"


class ExecutionState(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class ExecutionPhaseName(str, Enum):
    PLANNING = "planning"
    ARCHITECTURE_CHECK = "architecture-check"
    IMPLEMENTATION = "implementation"
    REVIEW = "review"
    QA = "qa"
    APPROVAL = "approval"


class ReviewOutcome(str, Enum):
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"


class QaOutcome(str, Enum):
    PASSED = "passed"
    FAILED = "failed"


class OverrideType(str, Enum):
    SCOPE_EXCEPTION = "scope_exception"
    RISK_EXCEPTION = "risk_exception"
    PHASE_BYPASS = "phase_bypass"
    APPROVAL_BYPASS = "approval_bypass"
    NON_GOAL_EXCEPTION = "non_goal_exception"


class RuntimeStatus(str, Enum):
    IDLE = "idle"
    IN_PROGRESS = "in_progress"
    HANDOFF_PENDING = "handoff_pending"
    BLOCKED = "blocked"
    COMPLETED = "completed"


class HandoffStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class EvaluationComplianceStatus(str, Enum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"
    WAIVED = "waived"


class LoopGovernanceStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    TERMINATED = "terminated"
    ESCALATED = "escalated"
    BLOCKED = "blocked"


class WorkflowMetadata(BaseModel):
    id: str = Field(min_length=1)
    type: str = Field(min_length=1)


class WorkflowConfidence(BaseModel):
    planning: str = Field(min_length=1)
    implementation: str = Field(min_length=1)
    tests: str = Field(min_length=1)
    residual_uncertainty: str = Field(min_length=1)


class WorkflowContext(BaseModel):
    workflow_file: str = Field(min_length=1)
    risk_level: RiskLevel
    confidence: WorkflowConfidence


class WorkflowGovernance(BaseModel):
    required_reviews: list[str]
    human_approval_required: bool = False
    escalation_required: bool = False
    protected_areas_touched: list[str] | None = None
    approval_evidence: list[str] | None = None

    @field_validator("required_reviews")
    @classmethod
    def validate_required_reviews(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("governance.required_reviews must be a non-empty list")
        return value


class WorkflowExecutionPhase(BaseModel):
    phase: ExecutionPhaseName
    state: ExecutionState


class WorkflowExecution(BaseModel):
    mode: ExecutionMode
    phases: list[WorkflowExecutionPhase]

    @field_validator("phases")
    @classmethod
    def validate_phases(
        cls, value: list[WorkflowExecutionPhase]
    ) -> list[WorkflowExecutionPhase]:
        if not value:
            raise ValueError("execution.phases must be a non-empty list")

        phase_names = [phase.phase for phase in value]
        if len(phase_names) != len(set(phase_names)):
            raise ValueError("execution.phases must not repeat phase names")

        return value


class WorkflowRuntime(BaseModel):
    status: RuntimeStatus
    current_phase: ExecutionPhaseName | None = None
    active_agent: str | None = None
    last_transition: str | None = None
    block_reason: str | None = None


class PlanningEvidence(BaseModel):
    summary: str = Field(min_length=1)
    scope_locked: list[str]
    non_goals_locked: list[str]
    risk_rationale: str = Field(min_length=1)


class ArchitectureCheckEvidence(BaseModel):
    decision: str = Field(min_length=1)
    constraints: list[str]
    approval_path: str = Field(min_length=1)


class ReviewEvidence(BaseModel):
    outcome: ReviewOutcome
    findings_summary: str = Field(min_length=1)
    residual_risk: str = Field(min_length=1)


class QaEvidence(BaseModel):
    outcome: QaOutcome
    evidence_summary: str = Field(min_length=1)
    unresolved_risks: list[str]


class ApprovalEvidence(BaseModel):
    approved_by: str = Field(min_length=1)
    reference: str = Field(min_length=1)
    scope_confirmed: bool


class WorkflowEvidence(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    planning: PlanningEvidence | None = None
    architecture_check: ArchitectureCheckEvidence | None = Field(
        default=None, alias="architecture-check"
    )
    review: ReviewEvidence | None = None
    qa: QaEvidence | None = None
    approval: ApprovalEvidence | None = None


class PlanningContract(BaseModel):
    owner_agent: Literal["planning-agent"]
    issue_brief: str = Field(min_length=1)
    acceptance_criteria: list[str]
    approved_scope: list[str]
    non_goals: list[str]
    initial_risk_level: RiskLevel
    protected_areas_touched: list[str]
    confidence_summary: str = Field(min_length=1)
    escalation_flags: list[str]


class ArchitectureCheckContract(BaseModel):
    owner_agent: Literal["architecture-agent"]
    architecture_assessment: str = Field(min_length=1)
    approved_scope: list[str]
    module_boundaries: list[str]
    contract_impact: str = Field(min_length=1)
    risk_review_decision: str = Field(min_length=1)
    required_reviews: list[str]
    implementation_constraints: list[str]


class ImplementationContract(BaseModel):
    owner_agent: Literal["senior-dev-agent"]
    implementation_summary: str = Field(min_length=1)
    changed_files: list[str]
    test_summary: str = Field(min_length=1)
    docs_updates: list[str]
    known_limitations: list[str]
    unresolved_questions: list[str]


class ReviewContract(BaseModel):
    owner_agent: Literal["review-agent"]
    review_findings: list[str]
    required_fixes: list[str]
    severity: str = Field(min_length=1)
    approval_status: str = Field(min_length=1)
    review_approval: str = Field(min_length=1)
    residual_risk: str = Field(min_length=1)
    qa_focus_areas: list[str]
    test_expectations: list[str]


class QaContract(BaseModel):
    owner_agent: Literal["qa-agent"]
    qa_report: str = Field(min_length=1)
    quality_gate_status: str = Field(min_length=1)
    unresolved_risks: list[str]
    approval_required: bool
    merge_readiness: bool


class WorkflowContracts(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    planning: PlanningContract | None = None
    architecture_check: ArchitectureCheckContract | None = Field(
        default=None, alias="architecture-check"
    )
    implementation: ImplementationContract | None = None
    review: ReviewContract | None = None
    qa: QaContract | None = None


class OverrideBase(BaseModel):
    id: str = Field(min_length=1)
    type: OverrideType
    reason: str = Field(min_length=1)
    scope_impact: str = Field(min_length=1)
    risk_impact: str = Field(min_length=1)
    mitigations: list[str]
    approved_by: str | None = None
    approval_reference: str | None = None
    review_by: date | None = None
    expires_on: date | None = None


class ScopeExceptionOverride(OverrideBase):
    type: Literal["scope_exception"]
    affected_scope_items: list[str]


class RiskExceptionOverride(OverrideBase):
    type: Literal["risk_exception"]
    original_risk: RiskLevel
    effective_risk: RiskLevel


class PhaseBypassOverride(OverrideBase):
    type: Literal["phase_bypass"]
    bypassed_phase: ExecutionPhaseName
    compensating_controls: list[str]


class ApprovalBypassOverride(OverrideBase):
    type: Literal["approval_bypass"]
    approval_target: str = Field(min_length=1)
    compensating_controls: list[str]


class NonGoalExceptionOverride(OverrideBase):
    type: Literal["non_goal_exception"]
    affected_non_goals: list[str]


WorkflowOverride = Annotated[
    ScopeExceptionOverride
    | RiskExceptionOverride
    | PhaseBypassOverride
    | ApprovalBypassOverride
    | NonGoalExceptionOverride,
    Field(discriminator="type"),
]


class WorkflowHandoff(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    from_phase: ExecutionPhaseName
    to_phase: ExecutionPhaseName
    status: HandoffStatus
    required_inputs: list[str]
    produced_outputs: list[str]
    blockers: list[str] | None = None
    override_refs: list[str] | None = None

    @field_validator("required_inputs", "produced_outputs")
    @classmethod
    def validate_artifacts(cls, value: list[str], info) -> list[str]:
        if not value:
            raise ValueError(f"{info.field_name} must be a non-empty list")
        return value


class LoopStopCondition(BaseModel):
    id: str = Field(min_length=1)
    description: str = Field(min_length=1)


class LoopEscalationCondition(BaseModel):
    id: str = Field(min_length=1)
    trigger: str = Field(min_length=1)
    escalate_to: str = Field(min_length=1)


class WorkflowLoop(BaseModel):
    id: str = Field(min_length=1)
    source_phase: ExecutionPhaseName
    target_phase: ExecutionPhaseName
    allowed_feedback_sources: list[str]
    max_iterations: int
    current_iteration: int
    status: LoopGovernanceStatus
    stop_conditions: list[LoopStopCondition]
    escalation_conditions: list[LoopEscalationCondition]
    evidence_refs: list[str]

    @field_validator("evidence_refs")
    @classmethod
    def validate_evidence_refs(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("evidence_refs must be a non-empty list")
        return value


class WorkflowLoopGovernance(BaseModel):
    loops: list[WorkflowLoop]

    @field_validator("loops")
    @classmethod
    def validate_loops(cls, value: list[WorkflowLoop]) -> list[WorkflowLoop]:
        if not value:
            raise ValueError("loops must be a non-empty list")
        return value


class EvaluationThreshold(BaseModel):
    operator: str = Field(min_length=1)
    value: str = Field(min_length=1)


class EvaluationMetric(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    source: str = Field(min_length=1)
    required: bool = False
    thresholds: EvaluationThreshold
    actual_value: str | None = None
    status: EvaluationComplianceStatus
    evidence_refs: list[str]
    blocks_merge: bool = False

    @field_validator("evidence_refs")
    @classmethod
    def validate_evidence_refs(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("evidence_refs must be a non-empty list")
        return value


class EvaluationCategory(BaseModel):
    id: str = Field(min_length=1)
    required_metrics: list[EvaluationMetric]

    @field_validator("required_metrics")
    @classmethod
    def validate_required_metrics(
        cls, value: list[EvaluationMetric]
    ) -> list[EvaluationMetric]:
        if not value:
            raise ValueError("required_metrics must be a non-empty list")
        return value


class WorkflowEvaluation(BaseModel):
    compliance_status: EvaluationComplianceStatus
    categories: list[EvaluationCategory]

    @field_validator("categories")
    @classmethod
    def validate_categories(
        cls, value: list[EvaluationCategory]
    ) -> list[EvaluationCategory]:
        if not value:
            raise ValueError("categories must be a non-empty list")
        return value


class WorkflowDocument(BaseModel):
    workflow: WorkflowMetadata
    context: WorkflowContext
    governance: WorkflowGovernance
    execution: WorkflowExecution
    evidence: WorkflowEvidence | None = None
    evaluation: WorkflowEvaluation | None = None
    loop_governance: WorkflowLoopGovernance | None = None
    contracts: WorkflowContracts | None = None
    overrides: list[WorkflowOverride] | None = None
    runtime: WorkflowRuntime | None = None
    handoffs: list[WorkflowHandoff] | None = None
