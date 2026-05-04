from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_parent
from app.models.parents import Parent
from app.models.users import User
from app.schemas.parent import ParentConsentRequest, ParentResponse, ParentUpdate
from app.services.audit import create_audit_log

router = APIRouter(prefix="/parent", tags=["parent"])


@router.get("/profile", response_model=ParentResponse)
async def get_profile(parent: Parent = Depends(require_parent)) -> Parent:
    return parent


@router.put("/profile", response_model=ParentResponse)
async def update_profile(
    payload: ParentUpdate,
    request: Request,
    parent: Parent = Depends(require_parent),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Parent:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(parent, field, value)
    await create_audit_log(
        db,
        action="parent.profile_updated",
        entity_type="parent",
        entity_id=parent.id,
        actor_user_id=current_user.id,
        metadata=payload.model_dump(exclude_unset=True),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    await db.refresh(parent)
    return parent


@router.post("/consent", response_model=ParentResponse)
async def consent(
    payload: ParentConsentRequest,
    request: Request,
    parent: Parent = Depends(require_parent),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Parent:
    parent.consent_given = True
    parent.consent_given_at = datetime.now(UTC)
    parent.privacy_acknowledged = payload.privacy_acknowledged
    await create_audit_log(
        db,
        action="parent.consent_given",
        entity_type="parent",
        entity_id=parent.id,
        actor_user_id=current_user.id,
        metadata=payload.model_dump(),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    await db.refresh(parent)
    return parent
