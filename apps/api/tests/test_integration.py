import asyncio
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.main import app
from app.models.alerts import Alert
from app.models.voices import Voice


def authenticated_client() -> TestClient:
    client = TestClient(app)
    response = client.post(
        "/auth/signup",
        json={
            "email": f"integration-{uuid4()}@example.com",
            "password": "correct-horse-123",
            "display_name": "Mum",
        },
    )
    assert response.status_code == 201
    client.headers.update({"Authorization": f"Bearer {response.json()['access_token']}"})
    return client


def create_ready_conversation(client: TestClient) -> tuple[str, str]:
    child = client.post("/children", json={"name": "Sam"})
    assert child.status_code == 201
    child_id = child.json()["id"]

    modes = client.get(f"/children/{child_id}/modes")
    assert modes.status_code == 200
    assert any(mode["safety_status"] == "approved" for mode in modes.json())

    helper = client.post(
        "/helper-profiles",
        json={"child_id": child_id, "label": "Mum's Always Near helper"},
    )
    assert helper.status_code == 201
    helper_payload = helper.json()
    approved = client.post(f"/helper-profiles/{helper_payload['id']}/final-approve")
    assert approved.status_code == 200
    asyncio.run(seed_approved_voice(helper_payload["parent_id"], helper_payload["id"]))

    conversation = client.post(
        "/conversation/start",
        json={
            "child_id": child_id,
            "helper_profile_id": helper_payload["id"],
            "mode": "comfort",
        },
    )
    assert conversation.status_code == 201
    return conversation.json()["conversation_id"], child_id


async def seed_approved_voice(parent_id: str, helper_profile_id: str) -> None:
    async with AsyncSessionLocal() as db:
        voice = Voice(
            parent_id=UUID(parent_id),
            helper_profile_id=UUID(helper_profile_id),
            provider="local",
            provider_voice_id=f"local-{uuid4().hex}",
            consent_status=True,
            approved_for_child_use=True,
            status="approved",
        )
        db.add(voice)
        await db.commit()


def send_message(client: TestClient, conversation_id: str, text: str, mode: str = "comfort") -> dict:
    response = client.post(
        "/conversation/message",
        json={"conversation_id": conversation_id, "mode": mode, "text": text},
    )
    assert response.status_code == 200
    return response.json()


def test_low_risk_conversation_returns_safe_comfort_and_audio() -> None:
    client = authenticated_client()
    conversation_id, _ = create_ready_conversation(client)

    payload = send_message(client, conversation_id, "I miss Mum")

    assert payload["risk_level"] == "LOW_RISK"
    assert payload["use_emergency_flow"] is False
    assert "Mum's Always Near helper" in payload["response_text"]
    assert "real grown-up" in payload["response_text"]
    assert payload["audio_url"].startswith("/internal/local-storage/")


def test_medium_risk_conversation_creates_alert_and_safe_comfort() -> None:
    client = authenticated_client()
    conversation_id, _ = create_ready_conversation(client)

    payload = send_message(client, conversation_id, "It is too loud and I can't cope")
    alerts = client.get("/alerts")

    assert payload["risk_level"] == "MEDIUM_RISK"
    assert payload["use_emergency_flow"] is False
    assert "Mum's Always Near helper" in payload["response_text"]
    assert "real grown-up" in payload["response_text"]
    assert alerts.status_code == 200
    assert any(alert["severity"] == "MEDIUM" for alert in alerts.json())


def test_high_risk_conversation_uses_emergency_flow_without_audio() -> None:
    client = authenticated_client()
    conversation_id, _ = create_ready_conversation(client)

    payload = send_message(client, conversation_id, "I can't breathe")

    assert payload["risk_level"] == "HIGH_RISK"
    assert payload["use_emergency_flow"] is True
    assert "real grown-up" in payload["response_text"]
    assert "You are safe right now" not in payload["response_text"]
    assert payload["audio_url"] is None
    assert asyncio.run(count_alerts(conversation_id)) == 1


async def count_alerts(conversation_id: str) -> int:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Alert).where(Alert.conversation_id == UUID(conversation_id))
        )
        return len(result.scalars().all())
