from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AvatarResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    parent_id: UUID | None
    helper_profile_id: UUID | None
    provider: str | None
    original_image_key: str | None
    consent_status: bool
    consent_timestamp: datetime | None
    approved_for_child_use: bool
    approved_at: datetime | None
    deleted_at: datetime | None
    status: str
    liveavatar_avatar_id: str | None = None
    liveavatar_status: str = "not_configured"
    liveavatar_session_id: str | None = None
    liveavatar_embed_url: str | None = None
    liveavatar_last_started_at: datetime | None = None
    created_at: datetime


class AvatarConsentRequest(BaseModel):
    consent_status: bool


class AvatarUploadResponse(BaseModel):
    id: UUID
    status: str
    original_image_key: str


class AvatarSignedUrlResponse(BaseModel):
    id: UUID
    signed_url: str
    expires_in: int
