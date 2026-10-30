"""Grow-only failure semantics; string-compatible for non-MCP callers."""
from pydantic import BaseModel, ConfigDict, Field, StrictStr, StrictInt, field_validator
from typing import Annotated
from errors import PublicToolError

class GrowExecutionError(PublicToolError):
    """Known failure before any memory write."""
    failure_class = "execution_failed"

class GrowItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content: Annotated[StrictStr, Field(min_length=1)]
    title: StrictStr | None = None
    name: StrictStr | None = None
    tags: StrictStr | list[StrictStr] | None = None
    domain: StrictStr | list[StrictStr] | None = None
    importance: Annotated[StrictInt, Field(ge=1, le=10)] | None = None
    valence: Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)] | None = None
    arousal: Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)] | None = None
    source_ranges: list[list[int]] | None = None

    @field_validator("valence", "arousal", mode="before")
    @classmethod
    def reject_boolean(cls, value):
        if isinstance(value, bool):
            raise ValueError("must be a number in [0, 1]")
        return value

class GrowFailure(str):
    def __new__(cls, text, failure_class="parameter_validation"):
        value = super().__new__(cls, text)
        value.failure_class = failure_class
        return value
