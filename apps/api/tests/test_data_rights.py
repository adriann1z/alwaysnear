from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.services.voice_provider import VoiceProvider, get_voice_provider


class TrackingVoiceProvider(VoiceProvider):
    def __init__(self) -> None:
        self.deleted: list[str] = []

    async def create_voice_clone(self, *, sample_audio: bytes, consent_audio: bytes, name: str) -> str:
        return f"tracked-{uuid4().hex}"

    async def generate_speech(self, *, provider_voice_id: str, text: str) -> bytes:
        return b"RIFF....WAVEfmt "

    async def delete_voice(self, *, provider_voice_id: str) -> None:
        self.deleted.append(provider_voice_id)


def authenticated_client(email_prefix: str = "privacy") -> tuple[TestClient, str, str]:
    email = f"{email_prefix}-{uuid4()}@example.com"
    password = "correct-horse-123"
    client = TestClient(app)
    response = client.post(
        "/auth/signup",
        json={
            "email": email,
            "password": password,
            "display_name": "Privacy Parent",
        },
    )
    assert response.status_code == 201
    client.headers.update({"Authorization": f"Bearer {response.json()['access_token']}"})
    return client, email, password


def create_child(client: TestClient, name: str) -> str:
    response = client.post("/children", json={"name": name})
    assert response.status_code == 201
    return response.json()["id"]


def create_voice(client: TestClient) -> tuple[str, str]:
    consent = client.post(
        "/voice/consent-recording",
        files={"audio": ("consent.wav", b"RIFF....WAVEfmt ", "audio/wav")},
    )
    assert consent.status_code == 200
    sample = client.post(
        "/voice/sample-recording",
        files={"audio": ("sample.wav", b"RIFF....WAVEfmt ", "audio/wav")},
    )
    assert sample.status_code == 200
    clone = client.post("/voice/create-clone")
    assert clone.status_code == 200
    return clone.json()["id"], clone.json()["provider_voice_id"]


def create_avatar(client: TestClient) -> str:
    consent = client.post("/avatar/consent", json={"consent_status": True})
    assert consent.status_code == 200
    upload = client.post(
        "/avatar/upload",
        files={"image": ("avatar.png", b"\x89PNG\r\n\x1a\n", "image/png")},
    )
    assert upload.status_code == 200
    return upload.json()["id"]


def test_data_export_returns_only_parent_data_and_no_raw_file_urls() -> None:
    owner, _, _ = authenticated_client("export-owner")
    other, _, _ = authenticated_client("export-other")
    create_child(owner, "Owner Child")
    create_child(other, "Other Child")
    create_avatar(owner)
    create_voice(owner)

    response = owner.get("/data/export")

    assert response.status_code == 200
    payload = response.json()
    raw = response.text
    assert any(child["name"] == "Owner Child" for child in payload["children"])
    assert all(child["name"] != "Other Child" for child in payload["children"])
    assert "password_hash" not in raw
    assert "signed_url" not in raw
    assert "asset_url" not in raw
    assert "sample_url" not in raw
    assert "consent_record_url" not in raw
    assert "original_image_key" not in raw
    assert "sample_recording_key" not in raw
    assert payload["avatars"][0]["has_original_image"] is True
    assert payload["voices"][0]["has_sample_recording"] is True


def test_delete_voice_marks_deleted_and_blocks_preview() -> None:
    client, _, _ = authenticated_client("delete-voice")
    voice_id, _ = create_voice(client)

    delete = client.delete(f"/voice/{voice_id}")
    preview = client.post(f"/voice/{voice_id}/preview", json={"text": "Preview after delete"})

    assert delete.status_code == 204
    assert preview.status_code == 404


def test_delete_avatar_invalidates_signed_url_access() -> None:
    client, _, _ = authenticated_client("delete-avatar")
    avatar_id = create_avatar(client)
    signed = client.get(f"/avatar/{avatar_id}")
    assert signed.status_code == 200
    assert "signature=" in signed.json()["signed_url"]

    delete = client.delete(f"/avatar/{avatar_id}")
    after_delete = client.get(f"/avatar/{avatar_id}")

    assert delete.status_code == 204
    assert after_delete.status_code == 404


def test_delete_account_requires_exact_phrase_deletes_data_and_blocks_login() -> None:
    tracker = TrackingVoiceProvider()
    app.dependency_overrides[get_voice_provider] = lambda: tracker
    try:
        client, email, password = authenticated_client("delete-account")
        create_child(client, "Delete Child")
        voice_id, provider_voice_id = create_voice(client)
        create_avatar(client)

        rejected = client.request(
            "DELETE",
            "/account",
            json={"confirmation_phrase": "DELETE ALWAYS NEAR"},
        )
        assert rejected.status_code == 400

        deleted = client.request(
            "DELETE",
            "/account",
            json={"confirmation_phrase": "DELETE MY ALWAYS NEAR ACCOUNT"},
        )
        assert deleted.status_code == 200
        assert provider_voice_id in tracker.deleted

        blocked_profile = client.get("/parent/profile")
        assert blocked_profile.status_code == 401

        login = TestClient(app).post(
            "/auth/login",
            json={"email": email, "password": password},
        )
        assert login.status_code == 401

        assert client.post(f"/voice/{voice_id}/approve").status_code == 401
    finally:
        app.dependency_overrides.pop(get_voice_provider, None)


def test_parents_cannot_delete_or_export_another_parents_data() -> None:
    owner, _, _ = authenticated_client("rights-owner")
    other, _, _ = authenticated_client("rights-other")
    owner_child_id = create_child(owner, "Scoped Child")
    other_child_id = create_child(other, "Private Child")
    owner_voice_id, _ = create_voice(owner)
    owner_avatar_id = create_avatar(owner)

    assert other.delete(f"/voice/{owner_voice_id}").status_code == 404
    assert other.delete(f"/avatar/{owner_avatar_id}").status_code == 404

    export = other.get("/data/export")
    assert export.status_code == 200
    raw = export.text
    assert other_child_id in raw
    assert owner_child_id not in raw
    assert "Scoped Child" not in raw
