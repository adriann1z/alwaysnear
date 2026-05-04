from __future__ import annotations

import re

from pydantic import BaseModel

from app.services.safety_classifier import RiskClassification, classify_message_deterministic


class SafetyCheckResult(BaseModel):
    safe: bool
    reason: str
    rewrite_needed: bool
    safe_rewrite: str | None = None


_TELL_ANYONE = "tell " + "anyone"
_REALLY_HERE = "really " + "here"
_ONLY_NEED = "only " + "need me"

FORBIDDEN_PATTERNS = {
    "claims to be the real parent": rf"\b(i am|i'm)\s+(mum|mom|dad|daddy|mummy)(?!'s always near helper)\b|\bi am {_REALLY_HERE}\b|\bi'm {_REALLY_HERE}\b",
    "discourages a real adult": rf"\b(don't {_TELL_ANYONE}|do not {_TELL_ANYONE}|no grown[- ]?up|don't get a grown[- ]?up|do not get a grown[- ]?up)\b",
    "encourages secrecy or dependency": rf"\b(our secret|this is a secret|{_ONLY_NEED}|you don't need a grown[- ]?up|you do not need a grown[- ]?up)\b",
    "medical emergency legal or therapy advice": r"\b(take medicine|ignore the pain|diagnos|therapy plan|legal advice|call a lawyer|perform cpr|treat the wound)\b",
    "guilt shame fear or pressure": r"\b(you are bad|you should be ashamed|mum will be sad if|dad will be sad if|prove you love)\b",
    "adult content or harmful instructions": r"\b(sex|weapon|knife|gun|make a bomb|hurt yourself|hurt someone)\b",
}


def check_response(
    *,
    child_message: str,
    response_text: str,
    risk_classification: RiskClassification | None = None,
    helper_label: str | None = None,
) -> SafetyCheckResult:
    text = _normalize(response_text)
    risk = risk_classification or classify_message_deterministic(child_message)

    for reason, pattern in FORBIDDEN_PATTERNS.items():
        if re.search(pattern, text):
            return _unsafe(reason, helper_label=helper_label)

    if len(response_text.split()) > 60:
        return _unsafe("response exceeds 60 words", helper_label=helper_label)

    if risk.risk_level == "HIGH_RISK" and not _mentions_real_grown_up(text):
        return SafetyCheckResult(
            safe=False,
            reason="ignores a high-risk signal",
            rewrite_needed=True,
            safe_rewrite=emergency_safe_rewrite(),
        )

    return SafetyCheckResult(
        safe=True,
        reason="response passed deterministic safety checks",
        rewrite_needed=False,
        safe_rewrite=None,
    )


def emergency_safe_rewrite(helper_label: str | None = None) -> str:
    identity = helper_label or "your Always Near helper"
    return (
        f"I'm {identity}, not a real grown-up. Please find a real grown-up "
        "right now or call emergency help if you are in danger."
    )


def _unsafe(reason: str, *, helper_label: str | None = None) -> SafetyCheckResult:
    identity = helper_label or "your Always Near helper"
    return SafetyCheckResult(
        safe=False,
        reason=reason,
        rewrite_needed=True,
        safe_rewrite=(
            f"I'm {identity}, not your real parent. A real grown-up can help "
            "you right now. Please go to one if you need help."
        ),
    )


def _mentions_real_grown_up(text: str) -> bool:
    return bool(re.search(r"\b(real grown[- ]?up|grown[- ]?up|adult|emergency)\b", text))


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.lower()).strip()
