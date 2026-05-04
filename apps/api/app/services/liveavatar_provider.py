from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import httpx
from pydantic import BaseModel

from app.core.config import settings


class LiveAvatarProviderError(RuntimeError):
    pass


class LiveAvatarSession(BaseModel):
    session_id: str
    embed_url: str | None = None
    sdk_token: str | None = None
    expires_at: datetime | None = None
    mock: bool = False


class LiveAvatarSpeakResult(BaseModel):
    accepted: bool
    mode: str
    message: str


class LiveAvatarProvider(ABC):
    @abstractmethod
    async def start_session(self, *, avatar_id: str) -> LiveAvatarSession:
        raise NotImplementedError

    @abstractmethod
    async def stop_session(self, *, session_id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def send_audio(
        self,
        *,
        session_id: str,
        audio_bytes: bytes,
        content_type: str,
    ) -> LiveAvatarSpeakResult:
        raise NotImplementedError


class MockLiveAvatarProvider(LiveAvatarProvider):
    async def start_session(self, *, avatar_id: str) -> LiveAvatarSession:
        session_id = f"mock-liveavatar-{uuid4().hex}"
        return LiveAvatarSession(
            session_id=session_id,
            embed_url=f"/internal/mock-liveavatar/{session_id}",
            expires_at=datetime.now(UTC) + timedelta(minutes=15),
            mock=True,
        )

    async def stop_session(self, *, session_id: str) -> bool:
        return True

    async def send_audio(
        self,
        *,
        session_id: str,
        audio_bytes: bytes,
        content_type: str,
    ) -> LiveAvatarSpeakResult:
        return LiveAvatarSpeakResult(
            accepted=True,
            mode="mock",
            message="Mock session accepted audio for local rendering",
        )


class HeyGenLiveAvatarProvider(LiveAvatarProvider):
    def __init__(self) -> None:
        if not settings.heygen_liveavatar_api_key:
            raise LiveAvatarProviderError("HEYGEN_LIVEAVATAR_API_KEY is required")
        self.base_url = settings.heygen_liveavatar_base_url.rstrip("/")
        self.headers = {
            "X-Api-Key": settings.heygen_liveavatar_api_key,
            "Accept": "application/json",
        }

    async def start_session(self, *, avatar_id: str) -> LiveAvatarSession:
        payload = {"avatar_id": avatar_id, "mode": "lite"}
        data = await self._post_json("/v1/liveavatar/sessions", payload)
        return LiveAvatarSession(
            session_id=str(data.get("session_id") or data.get("id")),
            embed_url=data.get("embed_url") or data.get("url"),
            sdk_token=data.get("session_token") or data.get("token"),
            expires_at=_parse_datetime(data.get("expires_at")),
            mock=False,
        )

    async def stop_session(self, *, session_id: str) -> bool:
        await self._post_json(f"/v1/liveavatar/sessions/{session_id}/stop", {})
        return True

    async def send_audio(
        self,
        *,
        session_id: str,
        audio_bytes: bytes,
        content_type: str,
    ) -> LiveAvatarSpeakResult:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self.base_url}/v1/liveavatar/sessions/{session_id}/audio",
                    headers=self.headers,
                    files={"audio": ("response-audio", audio_bytes, content_type)},
                )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise LiveAvatarProviderError("LiveAvatar provider could not accept audio") from exc
        return LiveAvatarSpeakResult(
            accepted=True,
            mode="server_audio",
            message="Audio accepted by LiveAvatar provider",
        )

    async def _post_json(self, path: str, payload: dict) -> dict:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self.base_url}{path}",
                    headers={**self.headers, "Content-Type": "application/json"},
                    json=payload,
                )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            raise LiveAvatarProviderError("LiveAvatar provider request failed") from exc
        except ValueError as exc:
            raise LiveAvatarProviderError("LiveAvatar provider returned invalid JSON") from exc
        if not data.get("session_id") and not data.get("id") and path.endswith("/sessions"):
            raise LiveAvatarProviderError("LiveAvatar provider did not return a session id")
        return data


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def get_liveavatar_provider() -> LiveAvatarProvider:
    if not settings.heygen_liveavatar_enabled:
        return MockLiveAvatarProvider()
    return HeyGenLiveAvatarProvider()
