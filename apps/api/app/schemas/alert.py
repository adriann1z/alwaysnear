from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    parent_id: UUID
    child_id: UUID
    severity: str
    category: str
    status: str
    details: str | None
    created_at: datetime


class AlertListItem(BaseModel):
    id: UUID
    child_name: str
    severity: str
    created_at: datetime
    mode: str | None
    trigger_summary: str | None
    parent_viewed: bool


class AlertDetail(BaseModel):
    id: UUID
    child_id: UUID
    child_name: str
    conversation_id: UUID | None
    severity: str
    category: str
    status: str
    mode: str | None
    trigger_summary: str | None
    details: str | None
    parent_notified: bool
    parent_viewed: bool
    created_at: datetime
    conversation_status: str | None = None
