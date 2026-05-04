from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    child_id: UUID
    helper_profile_id: UUID | None
    status: str
    started_at: datetime


class ConversationStartRequest(BaseModel):
    child_id: UUID
    helper_profile_id: UUID | None = None
    mode: str = Field(default="comfort", min_length=1, max_length=80)


class ConversationStartResponse(BaseModel):
    conversation_id: UUID
    status: str


class ConversationMessageRequest(BaseModel):
    conversation_id: UUID
    mode: str = Field(default="comfort", min_length=1, max_length=80)
    text: str | None = Field(default=None, max_length=4000)
    audio_base64: str | None = None

    @model_validator(mode="after")
    def require_text_or_audio(self) -> "ConversationMessageRequest":
        if not self.text and not self.audio_base64:
            raise ValueError("Either text or audio_base64 is required")
        return self


class ConversationMessageResponse(BaseModel):
    conversation_id: UUID
    response_text: str
    audio_url: str | None = None
    risk_level: str
    risk_reason: str
    trigger_parent_alert: bool
    use_emergency_flow: bool


class MessageSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sender_role: str
    content: str
    safety_level: str | None
    created_at: datetime


class ConversationSummaryResponse(BaseModel):
    id: UUID
    child_id: UUID
    helper_profile_id: UUID | None
    status: str
    started_at: datetime
    ended_at: datetime | None
    highest_risk_level: str | None
    messages: list[MessageSummary]
