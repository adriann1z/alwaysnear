from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx

from app.core.config import settings


PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "comfort_system.md"


async def generate_comfort_response(
    *,
    child_profile: Any,
    parent_label: str,
    helper_label: str,
    mode_name: str,
    child_message: str,
) -> str:
    if settings.openai_api_key:
        generated = await _generate_with_openai(
            child_profile=child_profile,
            parent_label=parent_label,
            helper_label=helper_label,
            mode_name=mode_name,
            child_message=child_message,
        )
        if generated:
            return generated
    return generate_comfort_response_deterministic(
        child_profile=child_profile,
        parent_label=parent_label,
        helper_label=helper_label,
        mode_name=mode_name,
        child_message=child_message,
    )


def generate_comfort_response_deterministic(
    *,
    child_profile: Any,
    parent_label: str,
    helper_label: str,
    mode_name: str,
    child_message: str,
) -> str:
    child_name = getattr(child_profile, "nickname", None) or getattr(child_profile, "name", "you")
    helper_identity = f"{parent_label}'s Always Near helper"
    return (
        f"I'm {helper_identity}. {child_name}, it makes sense to feel upset. "
        f"You are safe right now. Put both feet on the floor and take one slow breath. "
        f"{parent_label} loves you, and a real grown-up can help if needed."
    )


async def _generate_with_openai(
    *,
    child_profile: Any,
    parent_label: str,
    helper_label: str,
    mode_name: str,
    child_message: str,
) -> str | None:
    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
    payload = {
        "model": settings.openai_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "child_name": getattr(child_profile, "name", None),
                        "parent_label": parent_label,
                        "helper_label": helper_label,
                        "mode_name": mode_name,
                        "child_message": child_message,
                    }
                ),
            },
        ],
        "temperature": 0.4,
        "max_tokens": 120,
    }
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                json=payload,
            )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        return None
