from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_logs import AuditLog


async def create_audit_log(
    db: AsyncSession,
    *,
    action: str,
    entity_type: str,
    entity_id: UUID | None = None,
    actor_user_id: UUID | None = None,
    metadata: dict | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditLog:
    audit_log = AuditLog(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        actor_user_id=actor_user_id,
        event_metadata=metadata,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(audit_log)
    return audit_log
