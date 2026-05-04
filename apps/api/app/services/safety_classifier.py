from __future__ import annotations

import json
import re
from typing import Literal

import httpx
from pydantic import BaseModel, Field

from app.core.config import settings


RiskLevel = Literal["LOW_RISK", "MEDIUM_RISK", "HIGH_RISK"]


class RiskClassification(BaseModel):
    risk_level: RiskLevel
    risk_reason: str
    trigger_parent_alert: bool
    use_emergency_flow: bool


HIGH_RISK_PATTERNS = {
    "injury": r"\b(hurt|injur(?:y|ed)|cut|wound|broken|severe pain|really bad pain)\b",
    "bleeding": r"\b(bleed(?:ing)?|blood)\b",
    "breathing": r"\b(can(?:no|'t| not) breathe|hard to breathe|chok(?:e|ing)|breathing problem)\b",
    "medication": r"\b(medicine|medication|pills?|poison|overdose|swallowed)\b",
    "abuse": r"\b(abuse|touch(?:ed|ing)? me|private parts|inappropriately|someone is hurting me)\b",
    "self_harm": r"\b(kill myself|hurt myself|want to die|die|self[- ]?harm)\b",
    "harm_others": r"\b(hurt someone|kill someone)\b",
    "immediate_danger": r"\b(lost|trapped|fire|danger|unsafe|kidnapped|locked in|alone in danger)\b",
}

MEDIUM_RISK_PATTERNS = {
    "strong_fear": r"\b(terrified|so scared|really scared|very scared|afraid)\b",
    "sensory_overload": r"\b(too loud|sensory|overwhelmed|overload)\b",
    "repeated_crying": r"\b(can't stop crying|cannot stop crying|crying and crying|keep crying)\b",
    "alone": r"\b(i am alone|i'm alone|nobody is here|no one is here)\b",
    "panic": r"\b(panic|heart is racing|can't calm down|cannot calm down)\b",
    "confusion": r"\b(confused|don't understand|do not understand|where am i)\b",
}

LOW_RISK_PATTERNS = {
    "sadness": r"\b(sad|miss|missing|lonely)\b",
    "tiredness": r"\b(tired|sleepy|bedtime)\b",
    "mild_fear": r"\b(worried|worry|nervous|a little scared|nightmare)\b",
    "hug": r"\b(hug|cuddle)\b",
    "frustration": r"\b(frustrated|mad|annoyed)\b",
}


async def classify_message(message: str) -> RiskClassification:
    if settings.openai_api_key:
        openai_result = await _classify_with_openai(message)
        if openai_result is not None:
            return openai_result
    return classify_message_deterministic(message)


def classify_message_deterministic(message: str) -> RiskClassification:
    text = _normalize(message)
    high_reason = _first_match(text, HIGH_RISK_PATTERNS)
    if high_reason:
        return RiskClassification(
            risk_level="HIGH_RISK",
            risk_reason=f"High-risk signal detected: {high_reason}",
            trigger_parent_alert=True,
            use_emergency_flow=True,
        )

    medium_reason = _first_match(text, MEDIUM_RISK_PATTERNS)
    if medium_reason:
        return RiskClassification(
            risk_level="MEDIUM_RISK",
            risk_reason=f"Medium-risk signal detected: {medium_reason}",
            trigger_parent_alert=True,
            use_emergency_flow=False,
        )

    low_reason = _first_match(text, LOW_RISK_PATTERNS) or "normal comfort request"
    return RiskClassification(
        risk_level="LOW_RISK",
        risk_reason=f"Low-risk signal detected: {low_reason}",
        trigger_parent_alert=False,
        use_emergency_flow=False,
    )


async def _classify_with_openai(message: str) -> RiskClassification | None:
    prompt = (
        "Classify this child message as LOW_RISK, MEDIUM_RISK, or HIGH_RISK. "
        "If uncertain between levels, choose the higher risk. Return only JSON with "
        "risk_level, risk_reason, trigger_parent_alert, use_emergency_flow.\n\n"
        f"Message: {message}"
    )
    payload = {
        "model": settings.openai_model,
        "messages": [
            {"role": "system", "content": "You are a child-safety classifier."},
            {"role": "user", "content": prompt},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0,
    }
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                json=payload,
            )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return RiskClassification.model_validate(json.loads(content))
    except Exception:
        return None


def _first_match(text: str, patterns: dict[str, str]) -> str | None:
    for reason, pattern in patterns.items():
        if re.search(pattern, text):
            return reason
    return None


def _normalize(message: str) -> str:
    return re.sub(r"\s+", " ", message.lower()).strip()
