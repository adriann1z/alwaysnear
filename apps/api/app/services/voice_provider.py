from __future__ import annotations

import asyncio
import math
import struct
import wave
from abc import ABC, abstractmethod
from io import BytesIO
from uuid import uuid4

import httpx

from app.core.config import settings


class VoiceProviderError(RuntimeError):
    pass


class VoiceProvider(ABC):
    @abstractmethod
    async def create_voice_clone(
        self,
        *,
        sample_audio: bytes,
        consent_audio: bytes,
        name: str,
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    async def generate_speech(self, *, provider_voice_id: str, text: str) -> bytes:
        raise NotImplementedError

    @abstractmethod
    async def delete_voice(self, *, provider_voice_id: str) -> None:
        raise NotImplementedError


class LocalVoiceProvider(VoiceProvider):
    async def create_voice_clone(
        self,
        *,
        sample_audio: bytes,
        consent_audio: bytes,
        name: str,
    ) -> str:
        return f"local-{uuid4().hex}"

    async def generate_speech(self, *, provider_voice_id: str, text: str) -> bytes:
        return await asyncio.to_thread(_generate_tone_wav)

    async def delete_voice(self, *, provider_voice_id: str) -> None:
        return None


class ElevenLabsVoiceProvider(VoiceProvider):
    base_url = "https://api.elevenlabs.io/v1"

    def __init__(self) -> None:
        if not settings.elevenlabs_api_key:
            raise VoiceProviderError("ELEVENLABS_API_KEY is required")
        self.headers = {"xi-api-key": settings.elevenlabs_api_key}

    async def create_voice_clone(
        self,
        *,
        sample_audio: bytes,
        consent_audio: bytes,
        name: str,
    ) -> str:
        files = {
            "files": ("sample.wav", sample_audio, "audio/wav"),
        }
        data = {
            "name": name,
            "description": "Always Near parent-approved helper voice clone",
        }
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.base_url}/voices/add",
                headers=self.headers,
                data=data,
                files=files,
            )
        if response.status_code >= 400:
            raise VoiceProviderError("Voice clone provider rejected the request")
        payload = response.json()
        voice_id = payload.get("voice_id")
        if not voice_id:
            raise VoiceProviderError("Voice clone provider did not return a voice id")
        return voice_id

    async def generate_speech(self, *, provider_voice_id: str, text: str) -> bytes:
        payload = {"text": text, "model_id": settings.elevenlabs_model_id}
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.base_url}/text-to-speech/{provider_voice_id}",
                headers={**self.headers, "accept": "audio/mpeg"},
                json=payload,
            )
        if response.status_code >= 400:
            raise VoiceProviderError("Voice provider could not generate preview speech")
        return response.content

    async def delete_voice(self, *, provider_voice_id: str) -> None:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.delete(
                f"{self.base_url}/voices/{provider_voice_id}",
                headers=self.headers,
            )
        if response.status_code >= 400:
            raise VoiceProviderError("Voice provider could not delete the voice")


def _generate_tone_wav() -> bytes:
    sample_rate = 16000
    duration_seconds = 1
    frequency = 440
    amplitude = 8000
    buffer = BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        for index in range(sample_rate * duration_seconds):
            sample = int(amplitude * math.sin(2 * math.pi * frequency * index / sample_rate))
            wav_file.writeframes(struct.pack("<h", sample))
    return buffer.getvalue()


def get_voice_provider() -> VoiceProvider:
    provider = settings.voice_provider.lower()
    if provider == "local":
        return LocalVoiceProvider()
    if provider == "elevenlabs":
        return ElevenLabsVoiceProvider()
    raise VoiceProviderError(f"Unsupported voice provider: {settings.voice_provider}")
