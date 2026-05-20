from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, field_validator


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


class WorkflowDocument(BaseModel):
    workflow: WorkflowMetadata
    context: WorkflowContext
    governance: WorkflowGovernance
    execution: WorkflowExecution
