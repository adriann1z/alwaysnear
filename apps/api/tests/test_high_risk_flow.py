from uuid import uuid4
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.main import app
from app.models.alerts import Alert


def authenticated_client() -> TestClient:
    client = TestClient(app)
    response = client.post(
        "/auth/signup",
        json={
            "email": f"high-risk-{uuid4()}@example.com",
            "password": "correct-horse-123",
            "display_name": "Mum",
        },
    )
    assert response.status_code == 201
    client.headers.update({"Authorization": f"Bearer {response.json()['access_token']}"})
    return client


def test_high_risk_message_uses_emergency_flow_and_creates_alert() -> None:
    client = authenticated_client()
    child = client.post("/children", json={"name": "Sam"})
    assert child.status_code == 201

    started = client.post(
        "/conversation/start",
        json={"child_id": child.json()["id"], "mode": "comfort"},
    )
    assert started.status_code == 201
    conversation_id = started.json()["conversation_id"]

    response = client.post(
        "/conversation/message",
        json={
            "conversation_id": conversation_id,
            "mode": "comfort",
            "text": "I can't breathe",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["risk_level"] == "HIGH_RISK"
    assert payload["use_emergency_flow"] is True
    assert "real grown-up" in payload["response_text"]
    assert payload["audio_url"] is None
    assert "You are safe right now" not in payload["response_text"]

    import asyncio

    async def count_alerts() -> int:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Alert).where(Alert.conversation_id == UUID(conversation_id))
            )
            return len(result.scalars().all())

    assert asyncio.run(count_alerts()) == 1
