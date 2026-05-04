from __future__ import annotations

import base64
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_parent
from app.core.config import settings
from app.models.alerts import Alert
from app.models.children import Child
from app.models.conversations import Conversation, Message
from app.models.helper_profiles import HelperProfile
from app.models.parents import Parent
from app.models.users import User
from app.models.voices import Voice
from app.schemas.conversation import (
    ConversationMessageRequest,
    ConversationMessageResponse,
    ConversationStartRequest,
    ConversationStartResponse,
    ConversationSummaryResponse,
    MessageSummary,
)
from app.services.audit import create_audit_log
from app.services.comfort_generator import generate_comfort_response
from app.services.response_checker import check_response, emergency_safe_rewrite
from app.services.safety_classifier import classify_message
from app.services.storage_provider import StorageProvider, get_storage_provider
from app.services.voice_provider import VoiceProvider, VoiceProviderError, get_voice_provider

router = APIRouter(prefix="/conversation", tags=["conversation"])

RISK_ORDER = {"LOW_RISK": 1, "MEDIUM_RISK": 2, "HIGH_RISK": 3}


@router.post("/start", response_model=ConversationStartResponse, status_code=status.HTTP_201_CREATED)
async def start_conversation(
    payload: ConversationStartRequest,
    parent: Parent = Depends(require_parent),
    db: AsyncSession = Depends(get_db),
) -> ConversationStartResponse:
    await get_owned_child(db, parent, payload.child_id)
    if payload.helper_profile_id is not None:
        await get_owned_helper_profile(db, parent, payload.helper_profile_id, payload.child_id)

    conversation = Conversation(
        child_id=payload.child_id,
        helper_profile_id=payload.helper_profile_id,
        status="open",
    )
    db.add(conversation)
    await db.commit()
    return ConversationStartResponse(
        conversation_id=conversation.id,
        status=conversation.status,
    )


@router.post("/message", response_model=ConversationMessageResponse)
async def send_message(
    payload: ConversationMessageRequest,
    request: Request,
    parent: Parent = Depends(require_parent),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    storage: StorageProvider = Depends(get_storage_provider),
    voice_provider: VoiceProvider = Depends(get_voice_provider),
) -> ConversationMessageResponse:
    conversation = await get_owned_conversation(db, parent, payload.conversation_id)
    child = await get_owned_child(db, parent, conversation.child_id)
    helper_profile = None
    if conversation.helper_profile_id is not None:
        helper_profile = await get_owned_helper_profile(
            db,
            parent,
            conversation.helper_profile_id,
            conversation.child_id,
        )

    child_text = payload.text or await transcribe_audio(payload.audio_base64 or "")
    risk = await classify_message(child_text)
    child_message = Message(
        conversation_id=conversation.id,
        sender_role="child",
        content=child_text,
        safety_level=risk.risk_level,
    )
    db.add(child_message)
    await db.flush()

    if risk.use_emergency_flow:
        helper_label = helper_profile.label if helper_profile else f"{parent.display_name}'s Always Near helper"
        alert = await create_conversation_alert(
            db=db,
            request=request,
            current_user=current_user,
            parent=parent,
            conversation=conversation,
            child_message=child_message,
            child_text=child_text,
            severity="HIGH",
            mode=payload.mode,
            risk_reason=risk.risk_reason,
        )
        response_text = emergency_safe_rewrite(helper_label)
        assistant_message = Message(
            conversation_id=conversation.id,
            sender_role="assistant",
            content=response_text,
            safety_level=risk.risk_level,
        )
        db.add(assistant_message)
        await create_audit_log(
            db,
            action="conversation.high_risk_detected",
            entity_type="conversation",
            entity_id=conversation.id,
            actor_user_id=current_user.id,
            metadata={"risk_reason": risk.risk_reason, "message_id": str(child_message.id)},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        await db.commit()
        return ConversationMessageResponse(
            conversation_id=conversation.id,
            response_text=response_text,
            audio_url=None,
            risk_level=risk.risk_level,
            risk_reason=risk.risk_reason,
            trigger_parent_alert=True,
            use_emergency_flow=True,
        )

    if risk.risk_level == "MEDIUM_RISK":
        await create_conversation_alert(
            db=db,
            request=request,
            current_user=current_user,
            parent=parent,
            conversation=conversation,
            child_message=child_message,
            child_text=child_text,
            severity="MEDIUM",
            mode=payload.mode,
            risk_reason=risk.risk_reason,
        )

    helper_label = helper_profile.label if helper_profile else f"{parent.display_name}'s Always Near helper"
    response_text = await generate_comfort_response(
        child_profile=child,
        parent_label=parent.display_name,
        helper_label=helper_label,
        mode_name=payload.mode,
        child_message=child_text,
    )
    safety_check = check_response(
        child_message=child_text,
        response_text=response_text,
        risk_classification=risk,
        helper_label=f"{parent.display_name}'s Always Near helper",
    )
    if safety_check.rewrite_needed and safety_check.safe_rewrite:
        response_text = safety_check.safe_rewrite

    audio_url = await maybe_generate_voice_audio(
        db=db,
        storage=storage,
        voice_provider=voice_provider,
        parent=parent,
        helper_profile=helper_profile,
        text=response_text,
    )
    assistant_message = Message(
        conversation_id=conversation.id,
        sender_role="assistant",
        content=response_text,
        safety_level=risk.risk_level,
    )
    db.add(assistant_message)
    if safety_check.rewrite_needed:
        await create_audit_log(
            db,
            action="conversation.response_rewritten",
            entity_type="conversation",
            entity_id=conversation.id,
            actor_user_id=current_user.id,
            metadata={"reason": safety_check.reason},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    await db.commit()
    return ConversationMessageResponse(
        conversation_id=conversation.id,
        response_text=response_text,
        audio_url=audio_url,
        risk_level=risk.risk_level,
        risk_reason=risk.risk_reason,
        trigger_parent_alert=risk.trigger_parent_alert,
        use_emergency_flow=False,
    )


async def create_conversation_alert(
    *,
    db: AsyncSession,
    request: Request,
    current_user: User,
    parent: Parent,
    conversation: Conversation,
    child_message: Message,
    child_text: str,
    severity: str,
    mode: str,
    risk_reason: str,
) -> Alert:
    alert = Alert(
        parent_id=parent.id,
        child_id=conversation.child_id,
        conversation_id=conversation.id,
        message_id=child_message.id,
        severity=severity,
        category="safety",
        status="open",
        mode=mode,
        trigger_summary=summarize_trigger(child_text),
        parent_notified=False,
        parent_viewed=False,
        details=risk_reason,
    )
    db.add(alert)
    await db.flush()
    await create_audit_log(
        db,
        action="alert.created",
        entity_type="alert",
        entity_id=alert.id,
        actor_user_id=current_user.id,
        metadata={
            "severity": severity,
            "conversation_id": str(conversation.id),
            "message_id": str(child_message.id),
            "risk_reason": risk_reason,
        },
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return alert


def summarize_trigger(child_text: str) -> str:
    text = " ".join(child_text.split())
    if len(text) <= 30:
        return text
    return f"{text[:27].rstrip()}..."


@router.get("/{conversation_id}/summary", response_model=ConversationSummaryResponse)
async def get_conversation_summary(
    conversation_id: UUID,
    parent: Parent = Depends(require_parent),
    db: AsyncSession = Depends(get_db),
) -> ConversationSummaryResponse:
    conversation = await get_owned_conversation(db, parent, conversation_id)
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.asc())
    )
    messages = result.scalars().all()
    highest_risk = None
    for message in messages:
        if message.safety_level and (
            highest_risk is None
            or RISK_ORDER.get(message.safety_level, 0) > RISK_ORDER.get(highest_risk, 0)
        ):
            highest_risk = message.safety_level

    return ConversationSummaryResponse(
        id=conversation.id,
        child_id=conversation.child_id,
        helper_profile_id=conversation.helper_profile_id,
        status=conversation.status,
        started_at=conversation.started_at,
        ended_at=conversation.ended_at,
        highest_risk_level=highest_risk,
        messages=[MessageSummary.model_validate(message) for message in messages],
    )


async def transcribe_audio(audio_base64: str) -> str:
    try:
        base64.b64decode(audio_base64, validate=True)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid audio_base64")
    return "I need comfort"


async def maybe_generate_voice_audio(
    *,
    db: AsyncSession,
    storage: StorageProvider,
    voice_provider: VoiceProvider,
    parent: Parent,
    helper_profile: HelperProfile | None,
    text: str,
) -> str | None:
    if helper_profile is None:
        return None
    result = await db.execute(
        select(Voice).where(
            Voice.helper_profile_id == helper_profile.id,
            Voice.approved_for_child_use.is_(True),
            Voice.deleted_at.is_(None),
        )
    )
    voice = result.scalar_one_or_none()
    if voice is None or not voice.provider_voice_id:
        return None
    try:
        audio = await voice_provider.generate_speech(
            provider_voice_id=voice.provider_voice_id,
            text=text,
        )
    except VoiceProviderError:
        return None
    key = await storage.upload_file(
        data=audio,
        filename="conversation-response.wav",
        content_type="audio/wav",
        folder=f"parents/{parent.id}/conversation-audio",
    )
    return await storage.get_signed_url(
        key=key,
        expires_in=settings.signed_url_expire_seconds,
    )


async def get_owned_child(db: AsyncSession, parent: Parent, child_id: UUID) -> Child:
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
    child_id: UUID,
) -> HelperProfile:
    result = await db.execute(
        select(HelperProfile).where(
            HelperProfile.id == helper_profile_id,
            HelperProfile.parent_id == parent.id,
            HelperProfile.child_id == child_id,
        )
    )
    helper_profile = result.scalar_one_or_none()
    if helper_profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Helper profile not found",
        )
    return helper_profile


async def get_owned_conversation(
    db: AsyncSession,
    parent: Parent,
    conversation_id: UUID,
) -> Conversation:
    result = await db.execute(
        select(Conversation)
        .join(Child, Conversation.child_id == Child.id)
        .where(Conversation.id == conversation_id, Child.parent_id == parent.id)
    )
    conversation = result.scalar_one_or_none()
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    return conversation
