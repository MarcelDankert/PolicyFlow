from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class WorkflowMetadata(BaseModel):
    id: str = Field(min_length=1)
    type: str = Field(min_length=1)


class WorkflowContext(BaseModel):
    workflow_file: str = Field(min_length=1)
    risk_level: RiskLevel


class WorkflowGovernance(BaseModel):
    required_reviews: list[str]
    human_approval_required: bool = False
    approval_evidence: list[str] | None = None

    @field_validator("required_reviews")
    @classmethod
    def validate_required_reviews(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("governance.required_reviews must be a non-empty list")
        return value


class WorkflowDocument(BaseModel):
    workflow: WorkflowMetadata
    context: WorkflowContext
    governance: WorkflowGovernance
