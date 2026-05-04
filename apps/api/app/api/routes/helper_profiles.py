from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_parent
from app.models.children import Child
from app.models.helper_profiles import HelperProfile
from app.models.parents import Parent
from app.models.users import User
from app.schemas.helper_profile import (
    HelperProfileCreate,
    HelperProfileLabelUpdate,
    HelperProfileResponse,
)
from app.services.audit import create_audit_log

router = APIRouter(prefix="/helper-profiles", tags=["helper-profiles"])


async def ensure_owned_child(db: AsyncSession, parent: Parent, child_id: UUID) -> Child:
    result = await db.execute(
        select(Child).where(Child.id == child_id, Child.parent_id == parent.id)
    )
    child = result.scalar_one_or_none()
    if child is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Child not found")
    return child


async def get_owned_helper_profile(
    db: AsyncSession,
    parent: Parent,
    helper_profile_id: UUID,
) -> HelperProfile:
    result = await db.execute(
        select(HelperProfile).where(
            HelperProfile.id == helper_profile_id,
            HelperProfile.parent_id == parent.id,
        )
    )
    helper_profile = result.scalar_one_or_none()
    if helper_profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Helper profile not found",
        )
    return helper_profile


@router.post("", response_model=HelperProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_helper_profile(
    payload: HelperProfileCreate,
    request: Request,
    parent: Parent = Depends(require_parent),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HelperProfile:
    await ensure_owned_child(db, parent, payload.child_id)
    helper_profile = HelperProfile(
        parent_id=parent.id,
        child_id=payload.child_id,
        label=payload.label,
        description=payload.description,
        status="draft",
    )
    db.add(helper_profile)
    await db.flush()
    await create_audit_log(
        db,
        action="helper_profile.created",
        entity_type="helper_profile",
        entity_id=helper_profile.id,
        actor_user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    await db.refresh(helper_profile)
    return helper_profile


@router.get("/{helper_profile_id}", response_model=HelperProfileResponse)
async def get_helper_profile(
    helper_profile_id: UUID,
    parent: Parent = Depends(require_parent),
    db: AsyncSession = Depends(get_db),
) -> HelperProfile:
    return await get_owned_helper_profile(db, parent, helper_profile_id)


@router.put("/{helper_profile_id}/label", response_model=HelperProfileResponse)
async def update_helper_profile_label(
    helper_profile_id: UUID,
    payload: HelperProfileLabelUpdate,
    request: Request,
    parent: Parent = Depends(require_parent),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HelperProfile:
    helper_profile = await get_owned_helper_profile(db, parent, helper_profile_id)
    helper_profile.label = payload.label
    await create_audit_log(
        db,
        action="helper_profile.label_updated",
        entity_type="helper_profile",
        entity_id=helper_profile.id,
        actor_user_id=current_user.id,
        metadata=payload.model_dump(),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    await db.refresh(helper_profile)
    return helper_profile


@router.post("/{helper_profile_id}/final-approve", response_model=HelperProfileResponse)
async def final_approve_helper_profile(
    helper_profile_id: UUID,
    request: Request,
    parent: Parent = Depends(require_parent),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HelperProfile:
    helper_profile = await get_owned_helper_profile(db, parent, helper_profile_id)
    helper_profile.status = "approved"
    helper_profile.approved_at = datetime.now(UTC)
    helper_profile.paused_at = None
    await create_audit_log(
        db,
        action="helper_profile.final_approved",
        entity_type="helper_profile",
        entity_id=helper_profile.id,
        actor_user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    await db.refresh(helper_profile)
    return helper_profile


@router.post("/{helper_profile_id}/pause", response_model=HelperProfileResponse)
async def pause_helper_profile(
    helper_profile_id: UUID,
    request: Request,
    parent: Parent = Depends(require_parent),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HelperProfile:
    helper_profile = await get_owned_helper_profile(db, parent, helper_profile_id)
    helper_profile.status = "paused"
    helper_profile.paused_at = datetime.now(UTC)
    await create_audit_log(
        db,
        action="helper_profile.paused",
        entity_type="helper_profile",
        entity_id=helper_profile.id,
        actor_user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    await db.refresh(helper_profile)
    return helper_profile


@router.delete("/{helper_profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_helper_profile(
    helper_profile_id: UUID,
    request: Request,
    parent: Parent = Depends(require_parent),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    helper_profile = await get_owned_helper_profile(db, parent, helper_profile_id)
    await db.delete(helper_profile)
    await create_audit_log(
        db,
        action="helper_profile.deleted",
        entity_type="helper_profile",
        entity_id=helper_profile.id,
        actor_user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
