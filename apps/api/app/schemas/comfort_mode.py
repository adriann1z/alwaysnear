from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ComfortModeCreate(BaseModel):
    mode_name: str = Field(min_length=1, max_length=120)
    script: str | None = Field(default=None, max_length=4000)


class ComfortModeUpdate(BaseModel):
    mode_name: str | None = Field(default=None, min_length=1, max_length=120)
    script: str | None = Field(default=None, max_length=4000)


class ComfortModeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    child_id: UUID
    name: str
    mode_name: str
    description: str | None
    routine_prompt: str | None
    script: str | None
    is_active: bool
    active: bool
    safety_status: str
    parent_approval_status: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def model_validate(cls, obj, *args, **kwargs):
        if not isinstance(obj, dict):
            obj = {
                "id": obj.id,
                "child_id": obj.child_id,
                "name": obj.name,
                "mode_name": obj.name,
                "description": obj.description,
                "routine_prompt": obj.routine_prompt,
                "script": obj.routine_prompt,
                "is_active": obj.is_active,
                "active": obj.is_active,
                "safety_status": obj.safety_status,
                "parent_approval_status": obj.parent_approval_status,
                "created_at": obj.created_at,
                "updated_at": obj.updated_at,
            }
        return super().model_validate(obj, *args, **kwargs)


class ComfortModeCreateResponse(BaseModel):
    id: UUID
    safety_status: str
    parent_approval_status: str


class ComfortModeSafetyCheckResponse(BaseModel):
    mode: ComfortModeResponse
    safe: bool
    reason: str


class ComfortModeDeleteResponse(BaseModel):
    success: bool
