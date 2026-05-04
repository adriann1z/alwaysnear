from datetime import UTC, datetime

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_parent
from app.models.avatars import Avatar
from app.models.helper_profiles import HelperProfile
from app.models.parents import Parent
from app.models.users import User
from app.schemas.liveavatar import (
    LiveAvatarConfigureRequest,
    LiveAvatarConfigureResponse,
    LiveAvatarSessionResponse,
    LiveAvatarSpeakResponse,
    LiveAvatarStopRequest,
    LiveAvatarStopResponse,
)
from app.services.audit import create_audit_log
from app.services.liveavatar_provider import (
    LiveAvatarProvider,
    LiveAvatarProviderError,
    get_liveavatar_provider,
)

router = APIRouter(prefix="/liveavatar", tags=["liveavatar"])


@router.post("/configure", response_model=LiveAvatarConfigureResponse)
async def configure_liveavatar(
    payload: LiveAvatarConfigureRequest,
    request: Request,
    parent: Parent = Depends(require_parent),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LiveAvatarConfigureResponse:
    avatar = await get_parent_approved_avatar(db, parent)
    avatar.liveavatar_avatar_id = payload.avatar_id
    avatar.liveavatar_status = "configured"
    await create_audit_log(
        db,
        action="liveavatar.configured",
        entity_type="avatar",
        entity_id=avatar.id,
        actor_user_id=current_user.id,
        metadata={"provider": "heygen_liveavatar"},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    return LiveAvatarConfigureResponse(
        avatar_id=payload.avatar_id,
        status=avatar.liveavatar_status,
    )


@router.post("/session/start", response_model=LiveAvatarSessionResponse)
async def start_liveavatar_session(
    request: Request,
    parent: Parent = Depends(require_parent),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    provider: LiveAvatarProvider = Depends(get_liveavatar_provider),
) -> LiveAvatarSessionResponse:
    await get_active_approved_helper(db, parent)
    avatar = await get_parent_approved_avatar(db, parent)
    if not avatar.liveavatar_avatar_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LiveAvatar avatar ID is not configured",
        )
    try:
        session = await provider.start_session(avatar_id=avatar.liveavatar_avatar_id)
    except LiveAvatarProviderError as exc:
        avatar.liveavatar_status = "error"
        await db.commit()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    avatar.liveavatar_session_id = session.session_id
    avatar.liveavatar_embed_url = session.embed_url
    avatar.liveavatar_last_started_at = datetime.now(UTC)
    avatar.liveavatar_status = "session_started"
    await create_audit_log(
        db,
        action="liveavatar.session_started",
        entity_type="avatar",
        entity_id=avatar.id,
        actor_user_id=current_user.id,
        metadata={"mock": session.mock},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    return LiveAvatarSessionResponse(**session.model_dump())


@router.post("/session/stop", response_model=LiveAvatarStopResponse)
async def stop_liveavatar_session(
    payload: LiveAvatarStopRequest,
    request: Request,
    parent: Parent = Depends(require_parent),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    provider: LiveAvatarProvider = Depends(get_liveavatar_provider),
) -> LiveAvatarStopResponse:
    avatar = await get_parent_configured_avatar(db, parent)
    session_id = payload.session_id or avatar.liveavatar_session_id
    if not session_id:
        return LiveAvatarStopResponse(stopped=True)
    try:
        stopped = await provider.stop_session(session_id=session_id)
    except LiveAvatarProviderError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    avatar.liveavatar_session_id = None
    avatar.liveavatar_status = "configured"
    await create_audit_log(
        db,
        action="liveavatar.session_stopped",
        entity_type="avatar",
        entity_id=avatar.id,
        actor_user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    return LiveAvatarStopResponse(stopped=stopped)


@router.post("/session/speak", response_model=LiveAvatarSpeakResponse)
async def speak_liveavatar_session(
    request: Request,
    audio: UploadFile = File(...),
    parent: Parent = Depends(require_parent),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    provider: LiveAvatarProvider = Depends(get_liveavatar_provider),
) -> LiveAvatarSpeakResponse:
    avatar = await get_parent_configured_avatar(db, parent)
    if not avatar.liveavatar_session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LiveAvatar session has not been started",
        )
    data = await audio.read()
    try:
        result = await provider.send_audio(
            session_id=avatar.liveavatar_session_id,
            audio_bytes=data,
            content_type=audio.content_type or "application/octet-stream",
        )
    except LiveAvatarProviderError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    await create_audit_log(
        db,
        action="liveavatar.audio_sent",
        entity_type="avatar",
        entity_id=avatar.id,
        actor_user_id=current_user.id,
        metadata={"content_type": audio.content_type, "size": len(data)},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    return LiveAvatarSpeakResponse(**result.model_dump())


async def get_active_approved_helper(db: AsyncSession, parent: Parent) -> HelperProfile:
    result = await db.execute(
        select(HelperProfile)
        .where(
            HelperProfile.parent_id == parent.id,
            HelperProfile.status == "approved",
        )
        .order_by(HelperProfile.updated_at.desc())
    )
    helper = result.scalars().first()
    if helper is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Approved helper profile is required",
        )
    return helper


async def get_parent_approved_avatar(db: AsyncSession, parent: Parent) -> Avatar:
    result = await db.execute(
        select(Avatar)
        .where(
            Avatar.parent_id == parent.id,
            Avatar.approved_for_child_use.is_(True),
            Avatar.deleted_at.is_(None),
        )
        .order_by(Avatar.updated_at.desc())
    )
    avatar = result.scalars().first()
    if avatar is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Approved avatar is required",
        )
    return avatar


async def get_parent_configured_avatar(db: AsyncSession, parent: Parent) -> Avatar:
    avatar = await get_parent_approved_avatar(db, parent)
    if not avatar.liveavatar_avatar_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LiveAvatar avatar ID is not configured",
        )
    return avatar
