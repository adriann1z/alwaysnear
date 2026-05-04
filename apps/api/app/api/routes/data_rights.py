from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_parent
from app.core.security import hash_password
from app.models.alerts import Alert
from app.models.audit_logs import AuditLog
from app.models.avatars import Avatar
from app.models.children import Child
from app.models.comfort_modes import ComfortMode
from app.models.conversations import Conversation, Message
from app.models.helper_profiles import HelperProfile
from app.models.parents import Parent
from app.models.users import User
from app.models.voices import Voice
from app.services.audit import create_audit_log
from app.services.storage_provider import StorageProvider, get_storage_provider
from app.services.voice_provider import VoiceProvider, VoiceProviderError, get_voice_provider

router = APIRouter(tags=["data-rights"])

DELETE_CONFIRMATION = "DELETE MY ALWAYS NEAR ACCOUNT"


@router.get("/data/export")
async def export_parent_data(
    request: Request,
    response: Response,
    parent: Parent = Depends(require_parent),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    children = (
        await db.execute(select(Child).where(Child.parent_id == parent.id))
    ).scalars().all()
    child_ids = [child.id for child in children]
    helper_profiles = (
        await db.execute(select(HelperProfile).where(HelperProfile.parent_id == parent.id))
    ).scalars().all()
    avatars = (
        await db.execute(select(Avatar).where(Avatar.parent_id == parent.id))
    ).scalars().all()
    voices = (
        await db.execute(select(Voice).where(Voice.parent_id == parent.id))
    ).scalars().all()
    comfort_modes = (
        await db.execute(select(ComfortMode).where(ComfortMode.child_id.in_(child_ids)))
    ).scalars().all() if child_ids else []
    conversations = (
        await db.execute(select(Conversation).where(Conversation.child_id.in_(child_ids)))
    ).scalars().all() if child_ids else []
    conversation_ids = [conversation.id for conversation in conversations]
    messages = (
        await db.execute(select(Message).where(Message.conversation_id.in_(conversation_ids)))
    ).scalars().all() if conversation_ids else []
    alerts = (
        await db.execute(select(Alert).where(Alert.parent_id == parent.id))
    ).scalars().all()
    audit_logs = (
        await db.execute(select(AuditLog).where(AuditLog.actor_user_id == current_user.id))
    ).scalars().all()

    await create_audit_log(
        db,
        action="data.exported",
        entity_type="parent",
        entity_id=parent.id,
        actor_user_id=current_user.id,
        metadata={"children": len(children), "alerts": len(alerts)},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()

    response.headers["Content-Disposition"] = 'attachment; filename="always-near-export.json"'
    return {
        "exported_at": datetime.now(UTC).isoformat(),
        "user": {
            "id": str(current_user.id),
            "email": current_user.email,
            "role": current_user.role,
            "is_active": current_user.is_active,
            "created_at": current_user.created_at.isoformat(),
        },
        "parent": {
            "id": str(parent.id),
            "display_name": parent.display_name,
            "phone": parent.phone,
            "timezone": parent.timezone,
            "consent_given": parent.consent_given,
            "privacy_acknowledged": parent.privacy_acknowledged,
            "created_at": parent.created_at.isoformat(),
        },
        "children": [
            {
                "id": str(child.id),
                "name": child.name,
                "nickname": child.nickname,
                "date_of_birth": child.date_of_birth.isoformat() if child.date_of_birth else None,
                "pronouns": child.pronouns,
                "comfort_notes": child.comfort_notes,
                "is_active": child.is_active,
                "created_at": child.created_at.isoformat(),
            }
            for child in children
        ],
        "helper_profiles": [
            {
                "id": str(helper.id),
                "child_id": str(helper.child_id),
                "label": helper.label,
                "description": helper.description,
                "status": helper.status,
                "approved_at": helper.approved_at.isoformat() if helper.approved_at else None,
                "paused_at": helper.paused_at.isoformat() if helper.paused_at else None,
            }
            for helper in helper_profiles
        ],
        "avatars": [avatar_export(avatar) for avatar in avatars],
        "voices": [voice_export(voice) for voice in voices],
        "comfort_modes": [
            {
                "id": str(mode.id),
                "child_id": str(mode.child_id),
                "name": mode.name,
                "description": mode.description,
                "routine_prompt": mode.routine_prompt,
                "safety_status": mode.safety_status,
                "parent_approval_status": mode.parent_approval_status,
                "is_active": mode.is_active,
            }
            for mode in comfort_modes
        ],
        "conversations": summarize_conversations(conversations, messages),
        "alerts": [
            {
                "id": str(alert.id),
                "child_id": str(alert.child_id),
                "conversation_id": str(alert.conversation_id) if alert.conversation_id else None,
                "severity": alert.severity,
                "category": alert.category,
                "status": alert.status,
                "mode": alert.mode,
                "trigger_summary": alert.trigger_summary,
                "parent_viewed": alert.parent_viewed,
                "created_at": alert.created_at.isoformat(),
            }
            for alert in alerts
        ],
        "audit_logs": [
            {
                "id": str(log.id),
                "action": log.action,
                "entity_type": log.entity_type,
                "entity_id": str(log.entity_id) if log.entity_id else None,
                "created_at": log.created_at.isoformat(),
                "ip_address": log.ip_address,
            }
            for log in audit_logs
        ],
    }


@router.post("/data/delete-request")
async def request_data_deletion(
    request: Request,
    parent: Parent = Depends(require_parent),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    await create_audit_log(
        db,
        action="data.delete_requested",
        entity_type="parent",
        entity_id=parent.id,
        actor_user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    return {"detail": "Deletion request received"}


@router.delete("/account")
async def delete_account(
    request: Request,
    payload: dict = Body(...),
    parent: Parent = Depends(require_parent),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    storage: StorageProvider = Depends(get_storage_provider),
    voice_provider: VoiceProvider = Depends(get_voice_provider),
) -> dict[str, str]:
    if payload.get("confirmation_phrase") != DELETE_CONFIRMATION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Confirmation phrase does not match",
        )

    voices = (
        await db.execute(select(Voice).where(Voice.parent_id == parent.id))
    ).scalars().all()
    avatars = (
        await db.execute(select(Avatar).where(Avatar.parent_id == parent.id))
    ).scalars().all()

    await revoke_voice_assets(voices, storage, voice_provider)
    await revoke_avatar_assets(avatars, storage)

    await db.execute(
        update(AuditLog)
        .where(AuditLog.actor_user_id == current_user.id)
        .values(actor_user_id=None, event_metadata={"anonymized": True})
    )
    await create_audit_log(
        db,
        action="data.account_deleted",
        entity_type="user",
        entity_id=current_user.id,
        actor_user_id=current_user.id,
        metadata={"parent_id": str(parent.id)},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    current_user.email = f"deleted-{uuid4().hex}@deleted.always-near.local"
    current_user.password_hash = hash_password(uuid4().hex)
    current_user.is_active = False
    await db.delete(parent)
    await db.commit()
    return {"detail": "Account deleted"}


def avatar_export(avatar: Avatar) -> dict:
    return {
        "id": str(avatar.id),
        "helper_profile_id": str(avatar.helper_profile_id) if avatar.helper_profile_id else None,
        "provider": avatar.provider,
        "consent_status": avatar.consent_status,
        "consent_timestamp": avatar.consent_timestamp.isoformat() if avatar.consent_timestamp else None,
        "approved_for_child_use": avatar.approved_for_child_use,
        "approved_at": avatar.approved_at.isoformat() if avatar.approved_at else None,
        "deleted_at": avatar.deleted_at.isoformat() if avatar.deleted_at else None,
        "status": avatar.status,
        "has_original_image": avatar.original_image_key is not None,
    }


def voice_export(voice: Voice) -> dict:
    return {
        "id": str(voice.id),
        "helper_profile_id": str(voice.helper_profile_id) if voice.helper_profile_id else None,
        "provider": voice.provider,
        "consent_status": voice.consent_status,
        "consent_timestamp": voice.consent_timestamp.isoformat() if voice.consent_timestamp else None,
        "approved_for_child_use": voice.approved_for_child_use,
        "approved_at": voice.approved_at.isoformat() if voice.approved_at else None,
        "deleted_at": voice.deleted_at.isoformat() if voice.deleted_at else None,
        "status": voice.status,
        "has_consent_recording": voice.consent_recording_key is not None,
        "has_sample_recording": voice.sample_recording_key is not None,
        "has_preview_audio": voice.preview_audio_key is not None,
    }


def summarize_conversations(conversations: list[Conversation], messages: list[Message]) -> list[dict]:
    messages_by_conversation: dict[object, list[Message]] = {}
    for message in messages:
        messages_by_conversation.setdefault(message.conversation_id, []).append(message)
    return [
        {
            "id": str(conversation.id),
            "child_id": str(conversation.child_id),
            "helper_profile_id": str(conversation.helper_profile_id)
            if conversation.helper_profile_id
            else None,
            "status": conversation.status,
            "started_at": conversation.started_at.isoformat(),
            "ended_at": conversation.ended_at.isoformat() if conversation.ended_at else None,
            "message_count": len(messages_by_conversation.get(conversation.id, [])),
            "risk_levels": sorted(
                {
                    message.safety_level
                    for message in messages_by_conversation.get(conversation.id, [])
                    if message.safety_level
                }
            ),
        }
        for conversation in conversations
    ]


async def revoke_voice_assets(
    voices: list[Voice],
    storage: StorageProvider,
    voice_provider: VoiceProvider,
) -> None:
    for voice in voices:
        if voice.provider_voice_id:
            try:
                await voice_provider.delete_voice(provider_voice_id=voice.provider_voice_id)
            except VoiceProviderError:
                pass
        for key in [voice.consent_recording_key, voice.sample_recording_key, voice.preview_audio_key]:
            if key:
                await storage.delete_file(key=key)
        voice.deleted_at = datetime.now(UTC)
        voice.status = "deleted"
        voice.approved_for_child_use = False


async def revoke_avatar_assets(avatars: list[Avatar], storage: StorageProvider) -> None:
    for avatar in avatars:
        if avatar.original_image_key:
            await storage.delete_file(key=avatar.original_image_key)
        avatar.deleted_at = datetime.now(UTC)
        avatar.signed_urls_revoked_at = datetime.now(UTC)
        avatar.status = "deleted"
        avatar.approved_for_child_use = False
