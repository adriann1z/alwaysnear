from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_parent
from app.models.children import Child
from app.models.comfort_modes import ComfortMode
from app.models.parents import Parent
from app.models.users import User
from app.schemas.child import ChildCreate, ChildResponse, ChildUpdate
from app.services.audit import create_audit_log

router = APIRouter(prefix="/children", tags=["children"])


async def get_owned_child(db: AsyncSession, parent: Parent, child_id: UUID) -> Child:
    result = await db.execute(
        select(Child).where(Child.id == child_id, Child.parent_id == parent.id)
    )
    child = result.scalar_one_or_none()
    if child is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Child not found")
    return child


@router.post("", response_model=ChildResponse, status_code=status.HTTP_201_CREATED)
async def create_child(
    payload: ChildCreate,
    request: Request,
    parent: Parent = Depends(require_parent),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Child:
    child = Child(parent_id=parent.id, **payload.model_dump())
    db.add(child)
    await db.flush()
    create_default_comfort_modes(db, child=child, parent=parent)
    await create_audit_log(
        db,
        action="child.created",
        entity_type="child",
        entity_id=child.id,
        actor_user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    await db.refresh(child)
    return child


@router.get("/{child_id}", response_model=ChildResponse)
async def get_child(
    child_id: UUID,
    parent: Parent = Depends(require_parent),
    db: AsyncSession = Depends(get_db),
) -> Child:
    return await get_owned_child(db, parent, child_id)


@router.put("/{child_id}", response_model=ChildResponse)
async def update_child(
    child_id: UUID,
    payload: ChildUpdate,
    request: Request,
    parent: Parent = Depends(require_parent),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Child:
    child = await get_owned_child(db, parent, child_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(child, field, value)
    await create_audit_log(
        db,
        action="child.updated",
        entity_type="child",
        entity_id=child.id,
        actor_user_id=current_user.id,
        metadata=payload.model_dump(exclude_unset=True),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    await db.refresh(child)
    return child


@router.delete("/{child_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_child(
    child_id: UUID,
    request: Request,
    parent: Parent = Depends(require_parent),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    child = await get_owned_child(db, parent, child_id)
    await db.delete(child)
    await create_audit_log(
        db,
        action="child.deleted",
        entity_type="child",
        entity_id=child.id,
        actor_user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()


def create_default_comfort_modes(db: AsyncSession, *, child: Child, parent: Parent) -> None:
    child_name = child.nickname or child.name
    parent_label = parent.display_name
    helper_identity = f"{parent_label}'s Always Near helper"
    defaults = [
        ("I feel scared", "I see you're scared"),
        ("I feel sad", "I see you're sad"),
        ("I feel angry", "I see you're angry"),
        (f"I miss {parent_label}", f"I hear that you miss {parent_label}"),
        ("It is too loud", "I hear that it feels too loud"),
        ("Bedtime", "I see bedtime feels hard"),
        ("I feel overwhelmed", "I see you're overwhelmed"),
        ("I need a hug", "I hear that you need comfort"),
    ]
    for mode_name, feeling_line in defaults:
        script = (
            f"I'm {helper_identity}. {feeling_line}, {child_name}. Put your feet on the "
            f"floor and take one slow breath. You are safe right now, and {parent_label} "
            "loves you. If you need more help, find a grown-up."
        )
        db.add(
            ComfortMode(
                child_id=child.id,
                name=mode_name,
                routine_prompt=script,
                is_active=True,
                safety_status="approved",
                parent_approval_status="approved",
            )
        )
