from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


FORBIDDEN_LABEL_PARTS = ("i am", "real", "live", "ai mum", "ai dad")


def validate_helper_label(label: str) -> str:
    normalized = " ".join(label.strip().split())
    lowered = normalized.lower()
    if not lowered.endswith("helper"):
        raise ValueError('Helper label must end in "helper"')
    for forbidden in FORBIDDEN_LABEL_PARTS:
        if forbidden in lowered:
            raise ValueError(f'Helper label must not include "{forbidden}"')
    return normalized


class HelperProfileCreate(BaseModel):
    child_id: UUID
    label: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=4000)

    @field_validator("label")
    @classmethod
    def validate_label(cls, value: str) -> str:
        return validate_helper_label(value)


class HelperProfileLabelUpdate(BaseModel):
    label: str = Field(min_length=1, max_length=120)

    @field_validator("label")
    @classmethod
    def validate_label(cls, value: str) -> str:
        return validate_helper_label(value)


class HelperProfileUpdate(BaseModel):
    description: str | None = Field(default=None, max_length=4000)


class HelperProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    parent_id: UUID
    child_id: UUID
    label: str
    description: str | None
    status: Literal["draft", "approved", "paused"]
    approved_at: datetime | None
    paused_at: datetime | None
    created_at: datetime
    updated_at: datetime
