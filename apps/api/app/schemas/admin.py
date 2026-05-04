from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class AdminAlertItem(BaseModel):
    id: UUID
    child_id: UUID
    child_label: str
    severity: str
    created_at: datetime
    trigger_summary: str | None
    mode: str | None
    parent_viewed: bool


class AdminAuditLogItem(BaseModel):
    id: UUID
    created_at: datetime
    actor_user_id: UUID | None
    actor_email: EmailStr | None
    action: str
    metadata_summary: str | None
    ip_address: str | None


class AdminUserItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime


class AdminSystemHealth(BaseModel):
    status: str
    uptime_seconds: float
    database: str
