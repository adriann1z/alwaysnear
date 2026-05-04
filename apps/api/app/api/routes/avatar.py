from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_parent
from app.core.config import settings
from app.models.avatars import Avatar
from app.models.parents import Parent
from app.models.users import User
from app.schemas.avatar import (
    AvatarConsentRequest,
    AvatarResponse,
    AvatarSignedUrlResponse,
    AvatarUploadResponse,
)
from app.services.audit import create_audit_log
from app.services.storage_provider import StorageProvider, get_storage_provider

router = APIRouter(prefix="/avatar", tags=["avatar"])

MAX_AVATAR_BYTES = 5 * 1024 * 1024
ALLOWED_AVATAR_TYPES = {"image/jpeg", "image/png", "image/webp"}


async def get_parent_avatar(db: AsyncSession, parent: Parent) -> Avatar | None:
    result = await db.execute(
        select(Avatar)
        .where(Avatar.parent_id == parent.id, Avatar.deleted_at.is_(None))
        .order_by(Avatar.created_at.desc())
    )
    return result.scalars().first()


async def get_or_create_parent_avatar(db: AsyncSession, parent: Parent) -> Avatar:
    avatar = await get_parent_avatar(db, parent)
    if avatar is not None:
        return avatar
    avatar = Avatar(parent_id=parent.id, status="draft", provider=settings.storage_provider)
    db.add(avatar)
    await db.flush()
    return avatar


async def get_owned_avatar(db: AsyncSession, parent: Parent, avatar_id: UUID) -> Avatar:
    result = await db.execute(
        select(Avatar).where(
            Avatar.id == avatar_id,
            Avatar.parent_id == parent.id,
            Avatar.deleted_at.is_(None),
        )
    )
    avatar = result.scalar_one_or_none()
    if avatar is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Avatar not found")
    return avatar


async def read_limited_upload(file: UploadFile, *, max_bytes: int) -> bytes:
    data = await file.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is larger than the 5 MB limit",
        )
    return data


@router.post("/consent", response_model=AvatarResponse)
async def consent_avatar(
    payload: AvatarConsentRequest,
    request: Request,
    parent: Parent = Depends(require_parent),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Avatar:
    avatar = await get_or_create_parent_avatar(db, parent)
    avatar.consent_status = payload.consent_status
    avatar.consent_timestamp = datetime.now(UTC)
    if not payload.consent_status:
        avatar.approved_for_child_use = False
        avatar.approved_at = None
        avatar.status = "consent_revoked"
    elif avatar.status == "draft":
        avatar.status = "consented"

    await create_audit_log(
        db,
        action="avatar.consent_updated",
        entity_type="avatar",
        entity_id=avatar.id,
        actor_user_id=current_user.id,
        metadata=payload.model_dump(),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    await db.refresh(avatar)
    return avatar


@router.post("/upload", response_model=AvatarUploadResponse)
async def upload_avatar(
    request: Request,
    image: UploadFile = File(...),
    parent: Parent = Depends(require_parent),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    storage: StorageProvider = Depends(get_storage_provider),
) -> AvatarUploadResponse:
    if image.content_type not in ALLOWED_AVATAR_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Avatar image must be JPEG, PNG, or WEBP",
        )
    data = await read_limited_upload(image, max_bytes=MAX_AVATAR_BYTES)
    avatar = await get_or_create_parent_avatar(db, parent)
    key = await storage.upload_file(
        data=data,
        filename=image.filename or "avatar",
        content_type=image.content_type or "application/octet-stream",
        folder=f"parents/{parent.id}/avatars",
    )
    avatar.original_image_key = key
    avatar.status = "uploaded"
    avatar.approved_for_child_use = False
    avatar.approved_at = None

    await create_audit_log(
        db,
        action="avatar.uploaded",
        entity_type="avatar",
        entity_id=avatar.id,
        actor_user_id=current_user.id,
        metadata={"content_type": image.content_type, "size": len(data)},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    return AvatarUploadResponse(id=avatar.id, status=avatar.status, original_image_key=key)


@router.get("/{avatar_id}", response_model=AvatarSignedUrlResponse)
async def get_avatar(
    avatar_id: UUID,
    parent: Parent = Depends(require_parent),
    db: AsyncSession = Depends(get_db),
    storage: StorageProvider = Depends(get_storage_provider),
) -> AvatarSignedUrlResponse:
    avatar = await get_owned_avatar(db, parent, avatar_id)
    if not avatar.original_image_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar image has not been uploaded",
        )
    signed_url = await storage.get_signed_url(
        key=avatar.original_image_key,
        expires_in=settings.signed_url_expire_seconds,
    )
    return AvatarSignedUrlResponse(
        id=avatar.id,
        signed_url=signed_url,
        expires_in=settings.signed_url_expire_seconds,
    )


@router.post("/{avatar_id}/approve", response_model=AvatarResponse)
async def approve_avatar(
    avatar_id: UUID,
    request: Request,
    parent: Parent = Depends(require_parent),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Avatar:
    avatar = await get_owned_avatar(db, parent, avatar_id)
    if not avatar.consent_status or not avatar.consent_timestamp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Avatar consent is required before approval",
        )
    if not avatar.original_image_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Avatar upload is required before approval",
        )
    avatar.approved_for_child_use = True
    avatar.approved_at = datetime.now(UTC)
    avatar.status = "approved"
    await create_audit_log(
        db,
        action="avatar.approved",
        entity_type="avatar",
        entity_id=avatar.id,
        actor_user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    await db.refresh(avatar)
    return avatar


@router.delete("/{avatar_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_avatar(
    avatar_id: UUID,
    request: Request,
    parent: Parent = Depends(require_parent),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    storage: StorageProvider = Depends(get_storage_provider),
) -> None:
    avatar = await get_owned_avatar(db, parent, avatar_id)
    if avatar.original_image_key:
        await storage.delete_file(key=avatar.original_image_key)
    avatar.deleted_at = datetime.now(UTC)
    avatar.signed_urls_revoked_at = datetime.now(UTC)
    avatar.approved_for_child_use = False
    avatar.status = "deleted"
    await create_audit_log(
        db,
        action="avatar.deleted",
        entity_type="avatar",
        entity_id=avatar.id,
        actor_user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
