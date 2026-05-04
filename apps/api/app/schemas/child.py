from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ChildBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    nickname: str | None = Field(default=None, max_length=120)
    date_of_birth: date | None = None
    pronouns: str | None = Field(default=None, max_length=80)
    comfort_notes: str | None = Field(default=None, max_length=4000)


class ChildCreate(ChildBase):
    pass


class ChildUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    nickname: str | None = Field(default=None, max_length=120)
    date_of_birth: date | None = None
    pronouns: str | None = Field(default=None, max_length=80)
    comfort_notes: str | None = Field(default=None, max_length=4000)
    is_active: bool | None = None


class ChildResponse(ChildBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    parent_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
