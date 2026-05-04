from datetime import UTC, datetime
import asyncio
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_parent
from app.core.config import settings
from app.models.parents import Parent
from app.models.users import User
from app.models.voices import Voice
from app.schemas.voice import (
    VoiceCloneResponse,
    VoicePreviewRequest,
    VoicePreviewResponse,
    VoiceResponse,
    VoiceUploadResponse,
)
from app.services.audit import create_audit_log
from app.services.storage_provider import StorageProvider, get_storage_provider
from app.services.voice_provider import VoiceProvider, VoiceProviderError, get_voice_provider

router = APIRouter(prefix="/voice", tags=["voice"])

MAX_AUDIO_BYTES = 20 * 1024 * 1024
ALLOWED_AUDIO_TYPES = {
    "audio/wav",
    "audio/wave",
    "audio/x-wav",
    "audio/mpeg",
    "audio/mp3",
    "audio/webm",
    "audio/ogg",
    "audio/mp4",
}


async def get_parent_voice(db: AsyncSession, parent: Parent) -> Voice | None:
    result = await db.execute(
        select(Voice)
        .where(Voice.parent_id == parent.id, Voice.deleted_at.is_(None))
        .order_by(Voice.created_at.desc())
    )
    return result.scalars().first()


async def get_or_create_parent_voice(db: AsyncSession, parent: Parent) -> Voice:
    voice = await get_parent_voice(db, parent)
    if voice is not None:
        return voice
    voice = Voice(parent_id=parent.id, status="draft", provider=settings.voice_provider)
    db.add(voice)
    await db.flush()
    return voice


async def get_owned_voice(db: AsyncSession, parent: Parent, voice_id: UUID) -> Voice:
    result = await db.execute(
        select(Voice).where(
            Voice.id == voice_id,
            Voice.parent_id == parent.id,
            Voice.deleted_at.is_(None),
        )
    )
    voice = result.scalar_one_or_none()
    if voice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voice not found")
    return voice


async def read_limited_upload(file: UploadFile, *, max_bytes: int) -> bytes:
    data = await file.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio file is larger than the 20 MB limit",
        )
    return data


def ensure_audio_file(file: UploadFile) -> None:
    suffix = Path(file.filename or "").suffix.lower()
    if file.content_type not in ALLOWED_AUDIO_TYPES and suffix not in {
        ".wav",
        ".mp3",
        ".webm",
        ".ogg",
        ".m4a",
    }:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Voice recording must be an audio file",
        )


@router.post("/consent-recording", response_model=VoiceUploadResponse)
async def upload_consent_recording(
    request: Request,
    audio: UploadFile = File(...),
    parent: Parent = Depends(require_parent),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    storage: StorageProvider = Depends(get_storage_provider),
) -> VoiceUploadResponse:
    ensure_audio_file(audio)
    data = await read_limited_upload(audio, max_bytes=MAX_AUDIO_BYTES)
    voice = await get_or_create_parent_voice(db, parent)
    key = await storage.upload_file(
        data=data,
        filename=audio.filename or "consent-recording.wav",
        content_type=audio.content_type or "application/octet-stream",
        folder=f"parents/{parent.id}/voice-consent",
    )
    voice.consent_recording_key = key
    voice.consent_record_url = None
    voice.consent_status = True
    voice.consent_timestamp = datetime.now(UTC)
    voice.status = "consent_recorded"
    await create_audit_log(
        db,
        action="voice.consent_recorded",
        entity_type="voice",
        entity_id=voice.id,
        actor_user_id=current_user.id,
        metadata={"content_type": audio.content_type, "size": len(data)},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    return VoiceUploadResponse(id=voice.id, status=voice.status, key=key)


@router.post("/sample-recording", response_model=VoiceUploadResponse)
async def upload_sample_recording(
    request: Request,
    audio: UploadFile = File(...),
    parent: Parent = Depends(require_parent),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    storage: StorageProvider = Depends(get_storage_provider),
) -> VoiceUploadResponse:
    ensure_audio_file(audio)
    data = await read_limited_upload(audio, max_bytes=MAX_AUDIO_BYTES)
    voice = await get_or_create_parent_voice(db, parent)
    key = await storage.upload_file(
        data=data,
        filename=audio.filename or "sample-recording.wav",
        content_type=audio.content_type or "application/octet-stream",
        folder=f"parents/{parent.id}/voice-samples",
    )
    voice.sample_recording_key = key
    voice.sample_url = None
    voice.status = "sample_recorded"
    await create_audit_log(
        db,
        action="voice.sample_recorded",
        entity_type="voice",
        entity_id=voice.id,
        actor_user_id=current_user.id,
        metadata={"content_type": audio.content_type, "size": len(data)},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    return VoiceUploadResponse(id=voice.id, status=voice.status, key=key)


@router.post("/create-clone", response_model=VoiceCloneResponse)
async def create_voice_clone(
    parent: Parent = Depends(require_parent),
    db: AsyncSession = Depends(get_db),
    storage: StorageProvider = Depends(get_storage_provider),
    voice_provider: VoiceProvider = Depends(get_voice_provider),
) -> VoiceCloneResponse:
    voice = await get_parent_voice(db, parent)
    if voice is None or not voice.consent_recording_key or not voice.sample_recording_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Consent and sample recordings are required before cloning",
        )
    if not voice.consent_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Parent consent is required before cloning",
        )

    try:
        consent_audio = await _read_local_or_placeholder(storage, voice.consent_recording_key)
        sample_audio = await _read_local_or_placeholder(storage, voice.sample_recording_key)
        provider_voice_id = await voice_provider.create_voice_clone(
            sample_audio=sample_audio,
            consent_audio=consent_audio,
            name=f"Always Near voice {voice.id}",
        )
    except VoiceProviderError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    voice.provider_voice_id = provider_voice_id
    voice.provider = settings.voice_provider
    voice.status = "clone_created"
    await db.commit()
    return VoiceCloneResponse(
        id=voice.id,
        status=voice.status,
        provider_voice_id=provider_voice_id,
    )


@router.post("/{voice_id}/preview", response_model=VoicePreviewResponse)
async def preview_voice(
    voice_id: UUID,
    payload: VoicePreviewRequest,
    parent: Parent = Depends(require_parent),
    db: AsyncSession = Depends(get_db),
    storage: StorageProvider = Depends(get_storage_provider),
    voice_provider: VoiceProvider = Depends(get_voice_provider),
) -> VoicePreviewResponse:
    voice = await get_owned_voice(db, parent, voice_id)
    if not voice.provider_voice_id or voice.status not in {"clone_created", "preview_ready", "approved"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Voice clone is required before preview generation",
        )
    if voice.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voice not found")

    try:
        preview_audio = await voice_provider.generate_speech(
            provider_voice_id=voice.provider_voice_id,
            text=payload.text,
        )
    except VoiceProviderError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    key = await storage.upload_file(
        data=preview_audio,
        filename="voice-preview.wav",
        content_type="audio/wav",
        folder=f"parents/{parent.id}/voice-previews",
    )
    voice.preview_audio_key = key
    voice.status = "preview_ready"
    await db.commit()
    signed_url = await storage.get_signed_url(
        key=key,
        expires_in=settings.signed_url_expire_seconds,
    )
    return VoicePreviewResponse(
        id=voice.id,
        signed_url=signed_url,
        expires_in=settings.signed_url_expire_seconds,
    )


@router.post("/{voice_id}/approve", response_model=VoiceResponse)
async def approve_voice(
    voice_id: UUID,
    request: Request,
    parent: Parent = Depends(require_parent),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Voice:
    voice = await get_owned_voice(db, parent, voice_id)
    if not voice.consent_status or not voice.consent_timestamp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Voice consent is required before approval",
        )
    if not voice.provider_voice_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Voice clone must be created before approval",
        )
    voice.approved_for_child_use = True
    voice.approved_at = datetime.now(UTC)
    voice.status = "approved"
    await create_audit_log(
        db,
        action="voice.approved",
        entity_type="voice",
        entity_id=voice.id,
        actor_user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    await db.refresh(voice)
    return voice


@router.delete("/{voice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_voice(
    voice_id: UUID,
    request: Request,
    parent: Parent = Depends(require_parent),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    storage: StorageProvider = Depends(get_storage_provider),
    voice_provider: VoiceProvider = Depends(get_voice_provider),
) -> None:
    voice = await get_owned_voice(db, parent, voice_id)
    if voice.provider_voice_id:
        try:
            await voice_provider.delete_voice(provider_voice_id=voice.provider_voice_id)
        except VoiceProviderError as exc:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    for key in [voice.consent_recording_key, voice.sample_recording_key, voice.preview_audio_key]:
        if key:
            await storage.delete_file(key=key)
    voice.deleted_at = datetime.now(UTC)
    voice.approved_for_child_use = False
    voice.status = "deleted"
    await create_audit_log(
        db,
        action="voice.deleted",
        entity_type="voice",
        entity_id=voice.id,
        actor_user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()


async def _read_local_or_placeholder(storage: StorageProvider, key: str) -> bytes:
    root_path = getattr(storage, "root_path", None)
    if root_path is not None:
        path = root_path / key
        if path.exists():
            return await asyncio.to_thread(path.read_bytes)
    return b""
