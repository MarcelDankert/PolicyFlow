from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

from policyflow.exceptions import WorkflowValidationError


DEFAULT_CONFIG_PATH = Path("policyflow.yml")


class PolicyFlowPaths(BaseModel):
    changes: Path = Path("policyflow")
    pr_template: Path = Path(".github/PULL_REQUEST_TEMPLATE.md")
    governance_workflow: Path = Path(".github/workflows/policyflow.yml")

    @field_validator("changes", "pr_template", "governance_workflow")
    @classmethod
    def validate_relative_path(cls, value: Path, info) -> Path:
        if value.is_absolute():
            raise ValueError(f"paths.{info.field_name} must be a relative path")
        return value


class PolicyFlowGithub(BaseModel):
    enabled: bool = True


class PolicyFlowConfig(BaseModel):
    version: Literal[2]
    paths: PolicyFlowPaths = Field(default_factory=PolicyFlowPaths)
    github: PolicyFlowGithub = Field(default_factory=PolicyFlowGithub)

    @model_validator(mode="after")
    def validate_github_paths(self) -> PolicyFlowConfig:
        if not self.github.enabled:
            return self
        if not self.paths.pr_template:
            raise ValueError("paths.pr_template is required when github.enabled is true")
        if not self.paths.governance_workflow:
            raise ValueError("paths.governance_workflow is required when github.enabled is true")
        return self


def load_config(path: str | Path = DEFAULT_CONFIG_PATH) -> PolicyFlowConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise WorkflowValidationError([f"PolicyFlow config file not found: {config_path}"])

    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise WorkflowValidationError([f"Invalid PolicyFlow config YAML: {exc}"]) from exc

    if not isinstance(data, dict):
        raise WorkflowValidationError(["PolicyFlow config must contain a top-level YAML mapping"])

    try:
        return PolicyFlowConfig.model_validate(data)
    except ValidationError as exc:
        raise WorkflowValidationError(_format_config_errors(exc)) from exc


def _format_config_errors(exc: ValidationError) -> list[str]:
    errors: list[str] = []
    for error in exc.errors():
        message = str(error["msg"])
        if message.startswith("Value error, "):
            message = message.removeprefix("Value error, ")
        location = _format_location(error.get("loc", ()))
        if location:
            if message.startswith(f"{location} "):
                errors.append(message)
            else:
                errors.append(f"{location}: {message}")
        else:
            errors.append(message)
    return errors


def _format_location(location: Any) -> str:
    if not location or location == ():
        return ""
    return ".".join(str(part) for part in location)
