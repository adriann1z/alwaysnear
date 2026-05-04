from datetime import datetime

from pydantic import BaseModel, Field


class LiveAvatarConfigureRequest(BaseModel):
    avatar_id: str = Field(min_length=1, max_length=255)


class LiveAvatarConfigureResponse(BaseModel):
    avatar_id: str
    status: str


class LiveAvatarSessionResponse(BaseModel):
    session_id: str
    embed_url: str | None = None
    sdk_token: str | None = None
    expires_at: datetime | None = None
    mock: bool


class LiveAvatarStopRequest(BaseModel):
    session_id: str | None = Field(default=None, max_length=255)


class LiveAvatarStopResponse(BaseModel):
    stopped: bool


class LiveAvatarSpeakResponse(BaseModel):
    accepted: bool
    mode: str
    message: str
