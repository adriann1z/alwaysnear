from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_parent
from app.models.children import Child
from app.models.comfort_modes import ComfortMode
from app.models.parents import Parent
from app.models.users import User
from app.schemas.comfort_mode import (
    ComfortModeCreate,
    ComfortModeCreateResponse,
    ComfortModeDeleteResponse,
    ComfortModeResponse,
    ComfortModeSafetyCheckResponse,
    ComfortModeUpdate,
)
from app.services.audit import create_audit_log
from app.services.response_checker import check_response

router = APIRouter(tags=["comfort-modes"])


@router.post(
    "/children/{child_id}/modes",
    response_model=ComfortModeCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_comfort_mode(
    child_id: UUID,
    payload: ComfortModeCreate,
    request: Request,
    parent: Parent = Depends(require_parent),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ComfortModeCreateResponse:
    await get_owned_child(db, parent, child_id)
    mode = ComfortMode(
        child_id=child_id,
        name=payload.mode_name,
        routine_prompt=payload.script,
        is_active=True,
        safety_status="pending",
        parent_approval_status="pending",
    )
    db.add(mode)
    await db.flush()
    await create_audit_log(
        db,
        action="comfort_mode.created",
        entity_type="comfort_mode",
        entity_id=mode.id,
        actor_user_id=current_user.id,
        metadata={"child_id": str(child_id), "mode_name": mode.name},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    return ComfortModeCreateResponse(
        id=mode.id,
        safety_status=mode.safety_status,
        parent_approval_status=mode.parent_approval_status,
    )


@router.get("/children/{child_id}/modes", response_model=list[ComfortModeResponse])
async def list_comfort_modes(
    child_id: UUID,
    parent: Parent = Depends(require_parent),
    db: AsyncSession = Depends(get_db),
) -> list[ComfortMode]:
    await get_owned_child(db, parent, child_id)
    result = await db.execute(
        select(ComfortMode)
        .where(ComfortMode.child_id == child_id)
        .order_by(ComfortMode.created_at.asc())
    )
    return list(result.scalars().all())


@router.put("/modes/{mode_id}", response_model=ComfortModeResponse)
async def update_comfort_mode(
    mode_id: UUID,
    payload: ComfortModeUpdate,
    request: Request,
    parent: Parent = Depends(require_parent),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ComfortMode:
    mode = await get_owned_mode(db, parent, mode_id)
    values = payload.model_dump(exclude_unset=True)
    if "mode_name" in values:
        mode.name = values["mode_name"]
    if "script" in values:
        mode.routine_prompt = values["script"]
        mode.safety_status = "pending"
        mode.parent_approval_status = "pending"
    await create_audit_log(
        db,
        action="comfort_mode.updated",
        entity_type="comfort_mode",
        entity_id=mode.id,
        actor_user_id=current_user.id,
        metadata=values,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    await db.refresh(mode)
    return mode


@router.delete("/modes/{mode_id}", response_model=ComfortModeDeleteResponse)
async def delete_comfort_mode(
    mode_id: UUID,
    request: Request,
    parent: Parent = Depends(require_parent),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ComfortModeDeleteResponse:
    mode = await get_owned_mode(db, parent, mode_id)
    mode.is_active = False
    await create_audit_log(
        db,
        action="comfort_mode.deactivated",
        entity_type="comfort_mode",
        entity_id=mode.id,
        actor_user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    return ComfortModeDeleteResponse(success=True)


@router.post("/modes/{mode_id}/safety-check", response_model=ComfortModeSafetyCheckResponse)
async def safety_check_comfort_mode(
    mode_id: UUID,
    request: Request,
    parent: Parent = Depends(require_parent),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ComfortModeSafetyCheckResponse:
    mode = await get_owned_mode(db, parent, mode_id)
    result = check_response(
        child_message=mode.name,
        response_text=mode.routine_prompt or "",
    )
    mode.safety_status = "approved" if result.safe else "failed"
    await create_audit_log(
        db,
        action="comfort_mode.safety_checked",
        entity_type="comfort_mode",
        entity_id=mode.id,
        actor_user_id=current_user.id,
        metadata={"safe": result.safe, "reason": result.reason},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    await db.refresh(mode)
    return ComfortModeSafetyCheckResponse(
        mode=ComfortModeResponse.model_validate(mode),
        safe=result.safe,
        reason=result.reason,
    )


@router.post("/modes/{mode_id}/approve", response_model=ComfortModeResponse)
async def approve_comfort_mode(
    mode_id: UUID,
    request: Request,
    parent: Parent = Depends(require_parent),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ComfortMode:
    mode = await get_owned_mode(db, parent, mode_id)
    if mode.safety_status != "approved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Comfort mode must pass safety check before parent approval",
        )
    mode.parent_approval_status = "approved"
    await create_audit_log(
        db,
        action="comfort_mode.approved",
        entity_type="comfort_mode",
        entity_id=mode.id,
        actor_user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    await db.refresh(mode)
    return mode


async def get_owned_child(db: AsyncSession, parent: Parent, child_id: UUID) -> Child:
    result = await db.execute(
        select(Child).where(Child.id == child_id, Child.parent_id == parent.id)
    )
    child = result.scalar_one_or_none()
    if child is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Child not found")
    return child


async def get_owned_mode(db: AsyncSession, parent: Parent, mode_id: UUID) -> ComfortMode:
    result = await db.execute(
        select(ComfortMode)
        .join(Child, ComfortMode.child_id == Child.id)
        .where(ComfortMode.id == mode_id, Child.parent_id == parent.id)
    )
    mode = result.scalar_one_or_none()
    if mode is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comfort mode not found",
        )
    return mode
