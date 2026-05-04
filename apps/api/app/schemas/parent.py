from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ParentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    display_name: str
    phone: str | None
    timezone: str
    consent_given: bool
    consent_given_at: datetime | None
    privacy_acknowledged: bool
    created_at: datetime
    updated_at: datetime


class ParentUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    phone: str | None = Field(default=None, max_length=40)
    timezone: str | None = Field(default=None, min_length=1, max_length=80)


class ParentConsentRequest(BaseModel):
    privacy_acknowledged: bool = True
