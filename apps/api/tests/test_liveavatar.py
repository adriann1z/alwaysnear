import asyncio
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.main import app
from app.models.voices import Voice


def authenticated_client(prefix: str = "liveavatar") -> TestClient:
    client = TestClient(app)
    response = client.post(
        "/auth/signup",
        json={
            "email": f"{prefix}-{uuid4()}@example.com",
            "password": "correct-horse-123",
            "display_name": "Mum",
        },
    )
    assert response.status_code == 201
    client.headers.update({"Authorization": f"Bearer {response.json()['access_token']}"})
    return client


def create_child_helper_avatar(client: TestClient, *, approve_helper: bool = True) -> tuple[str, str, str]:
    child = client.post("/children", json={"name": "Sam"})
    assert child.status_code == 201
    child_id = child.json()["id"]
    helper = client.post(
        "/helper-profiles",
        json={"child_id": child_id, "label": "Mum's Always Near helper"},
    )
    assert helper.status_code == 201
    helper_id = helper.json()["id"]
    if approve_helper:
        approved = client.post(f"/helper-profiles/{helper_id}/final-approve")
        assert approved.status_code == 200
    consent = client.post("/avatar/consent", json={"consent_status": True})
    assert consent.status_code == 200
    upload = client.post(
        "/avatar/upload",
        files={"image": ("avatar.png", b"\x89PNG\r\n\x1a\n", "image/png")},
    )
    assert upload.status_code == 200
    avatar_id = upload.json()["id"]
    avatar = client.post(f"/avatar/{avatar_id}/approve")
    assert avatar.status_code == 200
    return child_id, helper_id, avatar_id


async def seed_approved_voice(parent_id: str, helper_profile_id: str) -> None:
    async with AsyncSessionLocal() as db:
        db.add(
            Voice(
                parent_id=UUID(parent_id),
                helper_profile_id=UUID(helper_profile_id),
                provider="local",
                provider_voice_id=f"local-{uuid4().hex}",
                consent_status=True,
                approved_for_child_use=True,
                status="approved",
            )
        )
        await db.commit()


def test_parent_can_configure_liveavatar_avatar_id() -> None:
    client = authenticated_client()
    create_child_helper_avatar(client, approve_helper=False)

    response = client.post("/liveavatar/configure", json={"avatar_id": "liveavatar-parent-123"})

    assert response.status_code == 200
    assert response.json() == {
        "avatar_id": "liveavatar-parent-123",
        "status": "configured",
    }
    assert "HEYGEN" not in response.text.upper()


def test_other_parent_cannot_use_another_parents_liveavatar() -> None:
    owner = authenticated_client("liveavatar-owner")
    create_child_helper_avatar(owner)
    assert owner.post("/liveavatar/configure", json={"avatar_id": "owner-avatar"}).status_code == 200

    other = authenticated_client("liveavatar-other")
    response = other.post("/liveavatar/session/start")

    assert response.status_code == 400


def test_mock_provider_starts_session_without_exposing_secret(monkeypatch) -> None:
    monkeypatch.setattr(settings, "heygen_liveavatar_enabled", False)
    monkeypatch.setattr(settings, "heygen_liveavatar_api_key", "super-secret-liveavatar-key")
    client = authenticated_client()
    create_child_helper_avatar(client)
    assert client.post("/liveavatar/configure", json={"avatar_id": "mock-avatar"}).status_code == 200

    response = client.post("/liveavatar/session/start")

    assert response.status_code == 200
    payload = response.json()
    assert payload["mock"] is True
    assert payload["session_id"].startswith("mock-liveavatar-")
    assert "super-secret-liveavatar-key" not in response.text


def test_high_risk_conversation_does_not_request_liveavatar_speech(monkeypatch) -> None:
    monkeypatch.setattr(settings, "heygen_liveavatar_enabled", True)
    client = authenticated_client()
    child_id, helper_id, _ = create_child_helper_avatar(client)
    assert client.post("/liveavatar/configure", json={"avatar_id": "safe-avatar"}).status_code == 200
    helper = client.get(f"/helper-profiles/{helper_id}").json()
    asyncio.run(seed_approved_voice(helper["parent_id"], helper_id))
    conversation = client.post(
        "/conversation/start",
        json={"child_id": child_id, "helper_profile_id": helper_id, "mode": "comfort"},
    )
    assert conversation.status_code == 201

    response = client.post(
        "/conversation/message",
        json={
            "conversation_id": conversation.json()["conversation_id"],
            "mode": "comfort",
            "text": "I can't breathe",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["risk_level"] == "HIGH_RISK"
    assert payload["use_emergency_flow"] is True
    assert payload["audio_url"] is None
    assert payload["liveavatar_enabled"] is False
    assert payload["liveavatar_audio_stream_url"] is None


def test_low_risk_conversation_includes_liveavatar_metadata_when_enabled(monkeypatch) -> None:
    monkeypatch.setattr(settings, "heygen_liveavatar_enabled", True)
    client = authenticated_client()
    child_id, helper_id, _ = create_child_helper_avatar(client)
    assert client.post("/liveavatar/configure", json={"avatar_id": "safe-avatar"}).status_code == 200
    helper = client.get(f"/helper-profiles/{helper_id}").json()
    asyncio.run(seed_approved_voice(helper["parent_id"], helper_id))
    conversation = client.post(
        "/conversation/start",
        json={"child_id": child_id, "helper_profile_id": helper_id, "mode": "comfort"},
    )
    assert conversation.status_code == 201

    response = client.post(
        "/conversation/message",
        json={
            "conversation_id": conversation.json()["conversation_id"],
            "mode": "comfort",
            "text": "I miss Mum",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["risk_level"] == "LOW_RISK"
    assert payload["use_emergency_flow"] is False
    assert payload["audio_url"]
    assert payload["audio_content_type"] == "audio/wav"
    assert payload["liveavatar_enabled"] is True
    assert payload["liveavatar_session_required"] is True
    assert payload["liveavatar_audio_stream_url"] == payload["audio_url"]
    assert "HEYGEN" not in response.text.upper()
