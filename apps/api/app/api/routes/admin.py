from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import Select, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_admin
from app.models.alerts import Alert
from app.models.audit_logs import AuditLog
from app.models.users import User
from app.schemas.admin import (
    AdminAlertItem,
    AdminAuditLogItem,
    AdminSystemHealth,
    AdminUserItem,
)
from app.services.audit import create_audit_log

router = APIRouter(prefix="/admin", tags=["admin"])
STARTED_AT = datetime.now(UTC)


@router.get("/alerts", response_model=list[AdminAlertItem])
async def list_admin_alerts(
    request: Request,
    severity: str | None = Query(default=None, pattern="^(HIGH|MEDIUM)$"),
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    parent_viewed: bool | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[AdminAlertItem]:
    await log_admin_access(
        db,
        request=request,
        admin_user=admin_user,
        action="admin.alerts.view",
        metadata={
            "severity": severity,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "parent_viewed": parent_viewed,
        },
    )

    query = apply_alert_filters(
        select(Alert).order_by(Alert.created_at.desc()).limit(limit).offset(offset),
        severity=severity,
        start_date=start_date,
        end_date=end_date,
        parent_viewed=parent_viewed,
    )
    result = await db.execute(query)
    alerts = result.scalars().all()
    await db.commit()
    return [
        AdminAlertItem(
            id=alert.id,
            child_id=alert.child_id,
            child_label=f"Child {str(alert.child_id)[:8]}",
            severity=alert.severity,
            created_at=alert.created_at,
            trigger_summary=alert.trigger_summary,
            mode=alert.mode,
            parent_viewed=alert.parent_viewed,
        )
        for alert in alerts
    ]


@router.get("/audit-logs", response_model=list[AdminAuditLogItem])
async def list_admin_audit_logs(
    request: Request,
    user_id: UUID | None = None,
    action: str | None = Query(default=None, max_length=120),
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[AdminAuditLogItem]:
    await log_admin_access(
        db,
        request=request,
        admin_user=admin_user,
        action="admin.audit_logs.view",
        metadata={
            "user_id": str(user_id) if user_id else None,
            "action": action,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
        },
    )

    query = (
        select(AuditLog, User.email)
        .outerjoin(User, AuditLog.actor_user_id == User.id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if user_id is not None:
        query = query.where(AuditLog.actor_user_id == user_id)
    if action:
        query = query.where(AuditLog.action == action)
    if start_date is not None:
        query = query.where(AuditLog.created_at >= start_date)
    if end_date is not None:
        query = query.where(AuditLog.created_at <= end_date)

    result = await db.execute(query)
    rows = result.all()
    await db.commit()
    return [
        AdminAuditLogItem(
            id=audit_log.id,
            created_at=audit_log.created_at,
            actor_user_id=audit_log.actor_user_id,
            actor_email=email,
            action=audit_log.action,
            metadata_summary=summarize_metadata(audit_log.event_metadata),
            ip_address=audit_log.ip_address,
        )
        for audit_log, email in rows
    ]


@router.get("/users", response_model=list[AdminUserItem])
async def list_admin_users(
    request: Request,
    role: str | None = Query(default=None, max_length=32),
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[AdminUserItem]:
    await log_admin_access(
        db,
        request=request,
        admin_user=admin_user,
        action="admin.users.view",
        metadata={
            "role": role,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
        },
    )

    query = select(User).order_by(User.created_at.desc()).limit(limit).offset(offset)
    if role:
        query = query.where(User.role == role)
    if start_date is not None:
        query = query.where(User.created_at >= start_date)
    if end_date is not None:
        query = query.where(User.created_at <= end_date)

    result = await db.execute(query)
    users = result.scalars().all()
    await db.commit()
    return [AdminUserItem.model_validate(user) for user in users]


@router.get("/system-health", response_model=AdminSystemHealth)
async def get_admin_system_health(
    request: Request,
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminSystemHealth:
    await log_admin_access(
        db,
        request=request,
        admin_user=admin_user,
        action="admin.system_health.view",
    )
    await db.execute(text("SELECT 1"))
    await db.commit()
    return AdminSystemHealth(
        status="ok",
        uptime_seconds=(datetime.now(UTC) - STARTED_AT).total_seconds(),
        database="ok",
    )


def apply_alert_filters(
    query: Select[tuple[Alert]],
    *,
    severity: str | None,
    start_date: datetime | None,
    end_date: datetime | None,
    parent_viewed: bool | None,
) -> Select[tuple[Alert]]:
    if severity:
        query = query.where(Alert.severity == severity)
    if start_date is not None:
        query = query.where(Alert.created_at >= start_date)
    if end_date is not None:
        query = query.where(Alert.created_at <= end_date)
    if parent_viewed is not None:
        query = query.where(Alert.parent_viewed.is_(parent_viewed))
    return query


async def log_admin_access(
    db: AsyncSession,
    *,
    request: Request,
    admin_user: User,
    action: str,
    metadata: dict | None = None,
) -> None:
    await create_audit_log(
        db,
        action=action,
        entity_type="admin",
        entity_id=admin_user.id,
        actor_user_id=admin_user.id,
        metadata=metadata,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.flush()


def summarize_metadata(metadata: dict | None) -> str | None:
    if not metadata:
        return None
    parts = [f"{key}={value}" for key, value in metadata.items() if value is not None]
    summary = ", ".join(parts)
    return summary[:240] if summary else None
