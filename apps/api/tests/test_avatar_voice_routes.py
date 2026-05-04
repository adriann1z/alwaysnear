from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def authenticated_client() -> TestClient:
    client = TestClient(app)
    response = client.post(
        "/auth/signup",
        json={
            "email": f"stage4-{uuid4()}@example.com",
            "password": "correct-horse-123",
            "display_name": "Stage Four",
        },
    )
    assert response.status_code == 201
    token = response.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


def test_avatar_upload_rejects_invalid_type() -> None:
    client = authenticated_client()

    response = client.post(
        "/avatar/upload",
        files={"image": ("avatar.txt", b"not an image", "text/plain")},
    )

    assert response.status_code == 400


def test_avatar_upload_rejects_large_file() -> None:
    client = authenticated_client()

    response = client.post(
        "/avatar/upload",
        files={"image": ("avatar.png", b"x" * (5 * 1024 * 1024 + 1), "image/png")},
    )

    assert response.status_code == 400


def test_avatar_get_returns_signed_non_public_url() -> None:
    client = authenticated_client()
    consent = client.post("/avatar/consent", json={"consent_status": True})
    assert consent.status_code == 200
    upload = client.post(
        "/avatar/upload",
        files={"image": ("avatar.png", b"\x89PNG\r\n\x1a\n", "image/png")},
    )
    assert upload.status_code == 200
    avatar_id = upload.json()["id"]

    response = client.get(f"/avatar/{avatar_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["signed_url"].startswith("/internal/local-storage/")
    assert "signature=" in payload["signed_url"]
    assert not payload["signed_url"].startswith("http://")
    assert not payload["signed_url"].startswith("https://")


def test_mock_voice_flow_end_to_end() -> None:
    client = authenticated_client()

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
    voice_id = clone.json()["id"]
    assert clone.json()["provider_voice_id"].startswith("local-")

    preview = client.post(f"/voice/{voice_id}/preview", json={"text": "Hello from preview"})
    assert preview.status_code == 200
    assert preview.json()["signed_url"].startswith("/internal/local-storage/")

    approve = client.post(f"/voice/{voice_id}/approve")
    assert approve.status_code == 200
    assert approve.json()["approved_for_child_use"] is True

    delete = client.delete(f"/voice/{voice_id}")
    assert delete.status_code == 204
