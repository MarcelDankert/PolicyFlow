from __future__ import annotations


class WorkflowValidationError(Exception):
    """Raised when a workflow file cannot be loaded or validated."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("\n".join(errors))
