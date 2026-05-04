from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class VoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    parent_id: UUID | None
    helper_profile_id: UUID | None
    provider: str | None
    provider_voice_id: str | None
    consent_status: bool
    consent_timestamp: datetime | None
    consent_recording_key: str | None
    sample_recording_key: str | None
    preview_audio_key: str | None
    approved_for_child_use: bool
    approved_at: datetime | None
    deleted_at: datetime | None
    status: str
    created_at: datetime


class VoiceUploadResponse(BaseModel):
    id: UUID
    status: str
    key: str


class VoiceCloneResponse(BaseModel):
    id: UUID
    status: str
    provider_voice_id: str


class VoicePreviewRequest(BaseModel):
    text: str = Field(min_length=1, max_length=500)


class VoicePreviewResponse(BaseModel):
    id: UUID
    signed_url: str
    expires_in: int
