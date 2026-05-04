from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_parent
from app.models.alerts import Alert
from app.models.children import Child
from app.models.conversations import Conversation
from app.models.parents import Parent
from app.models.users import User
from app.schemas.alert import AlertDetail, AlertListItem
from app.services.audit import create_audit_log

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertListItem])
async def list_alerts(
    parent: Parent = Depends(require_parent),
    db: AsyncSession = Depends(get_db),
) -> list[AlertListItem]:
    result = await db.execute(
        select(Alert, Child.name)
        .join(Child, Alert.child_id == Child.id)
        .where(Alert.parent_id == parent.id)
        .order_by(Alert.created_at.desc())
    )
    return [
        AlertListItem(
            id=alert.id,
            child_name=child_name,
            severity=alert.severity,
            created_at=alert.created_at,
            mode=alert.mode,
            trigger_summary=alert.trigger_summary,
            parent_viewed=alert.parent_viewed,
        )
        for alert, child_name in result.all()
    ]


@router.get("/{alert_id}", response_model=AlertDetail)
async def get_alert(
    alert_id: UUID,
    parent: Parent = Depends(require_parent),
    db: AsyncSession = Depends(get_db),
) -> AlertDetail:
    alert, child_name, conversation_status = await get_owned_alert_detail(db, parent, alert_id)
    return build_alert_detail(alert, child_name, conversation_status)


@router.post("/{alert_id}/mark-viewed", response_model=AlertDetail)
async def mark_alert_viewed(
    alert_id: UUID,
    request: Request,
    parent: Parent = Depends(require_parent),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AlertDetail:
    alert, child_name, conversation_status = await get_owned_alert_detail(db, parent, alert_id)
    alert.parent_viewed = True
    await create_audit_log(
        db,
        action="alert.marked_viewed",
        entity_type="alert",
        entity_id=alert.id,
        actor_user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    await db.refresh(alert)
    return build_alert_detail(alert, child_name, conversation_status)


async def get_owned_alert_detail(
    db: AsyncSession,
    parent: Parent,
    alert_id: UUID,
) -> tuple[Alert, str, str | None]:
    result = await db.execute(
        select(Alert, Child.name, Conversation.status)
        .join(Child, Alert.child_id == Child.id)
        .outerjoin(Conversation, Alert.conversation_id == Conversation.id)
        .where(Alert.id == alert_id, Alert.parent_id == parent.id)
    )
    row = result.first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    alert, child_name, conversation_status = row
    return alert, child_name, conversation_status


def build_alert_detail(
    alert: Alert,
    child_name: str,
    conversation_status: str | None,
) -> AlertDetail:
    return AlertDetail(
        id=alert.id,
        child_id=alert.child_id,
        child_name=child_name,
        conversation_id=alert.conversation_id,
        severity=alert.severity,
        category=alert.category,
        status=alert.status,
        mode=alert.mode,
        trigger_summary=alert.trigger_summary,
        details=alert.details,
        parent_notified=alert.parent_notified,
        parent_viewed=alert.parent_viewed,
        created_at=alert.created_at,
        conversation_status=conversation_status,
    )
