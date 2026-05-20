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


class WorkflowMetadata(BaseModel):
    id: str = Field(min_length=1)
    type: str = Field(min_length=1)


class WorkflowContext(BaseModel):
    workflow_file: str = Field(min_length=1)
    risk_level: RiskLevel


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


class WorkflowDocument(BaseModel):
    workflow: WorkflowMetadata
    context: WorkflowContext
    governance: WorkflowGovernance
    execution: WorkflowExecution
    evidence: WorkflowEvidence | None = None
    contracts: WorkflowContracts | None = None
    overrides: list[WorkflowOverride] | None = None
