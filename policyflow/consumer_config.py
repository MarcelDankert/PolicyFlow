from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

from policyflow.exceptions import WorkflowValidationError


DEFAULT_CONSUMER_CONFIG_PATH = Path("policyflow.yml")


class ConsumerConfigPaths(BaseModel):
    workflows: Path = Path("ai/workflows")
    prompts: Path = Path("ai/prompts")
    agents: Path = Path("ai/agents")
    rules: Path = Path("ai/rules")
    project_context: Path = Path("ai/project-context.yml")
    runner_config: Path = Path("policyflow.runners.yml")
    pr_template: Path = Path(".github/PULL_REQUEST_TEMPLATE.md")
    issue_templates: Path = Path(".github/ISSUE_TEMPLATE")
    governance_workflow: Path = Path(".github/workflows/policyflow-governance.yml")

    @field_validator(
        "workflows",
        "prompts",
        "agents",
        "rules",
        "project_context",
        "runner_config",
        "pr_template",
        "issue_templates",
        "governance_workflow",
    )
    @classmethod
    def validate_relative_path(cls, value: Path, info) -> Path:
        if value.is_absolute():
            raise ValueError(f"paths.{info.field_name} must be a relative path")
        return value


class ConsumerConfigFeatures(BaseModel):
    pr_validation: bool = True
    github_approval_checks: bool = True
    runner_execution: bool = True
    bootstrap_managed_assets: bool = True


class ConsumerConfigBootstrap(BaseModel):
    managed_assets: list[Path] = Field(default_factory=list)

    @field_validator("managed_assets")
    @classmethod
    def validate_managed_assets(cls, value: list[Path]) -> list[Path]:
        for path in value:
            if path.is_absolute():
                raise ValueError("bootstrap.managed_assets entries must be relative paths")
        return value


class ConsumerConfig(BaseModel):
    version: int
    paths: ConsumerConfigPaths = Field(default_factory=ConsumerConfigPaths)
    features: ConsumerConfigFeatures = Field(default_factory=ConsumerConfigFeatures)
    bootstrap: ConsumerConfigBootstrap = Field(default_factory=ConsumerConfigBootstrap)

    @model_validator(mode="after")
    def validate_version(self) -> ConsumerConfig:
        if self.version != 1:
            raise ValueError("version must be 1")
        return self


def load_consumer_config(path: str | Path = DEFAULT_CONSUMER_CONFIG_PATH) -> ConsumerConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise WorkflowValidationError([f"Consumer config file not found: {config_path}"])

    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise WorkflowValidationError([f"Invalid consumer config YAML: {exc}"]) from exc

    if not isinstance(data, dict):
        raise WorkflowValidationError(
            ["Consumer config file must contain a top-level YAML mapping"]
        )

    try:
        return ConsumerConfig.model_validate(data)
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
    if not location:
        return ""
    if location == ():
        return ""
    return ".".join(str(part) for part in location)
