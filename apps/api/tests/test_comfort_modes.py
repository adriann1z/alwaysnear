from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


SAFE_SCRIPT = (
    "I'm Mum's Always Near helper. I see you feel worried. Put your feet on the "
    "floor and take one slow breath. You are safe right now, and Mum loves you. "
    "If you need more help, find a grown-up."
)


def authenticated_client(display_name: str = "Mum") -> TestClient:
    client = TestClient(app)
    response = client.post(
        "/auth/signup",
        json={
            "email": f"comfort-{uuid4()}@example.com",
            "password": "correct-horse-123",
            "display_name": display_name,
        },
    )
    assert response.status_code == 201
    client.headers.update({"Authorization": f"Bearer {response.json()['access_token']}"})
    return client


def create_child(client: TestClient, name: str = "Sam") -> str:
    response = client.post("/children", json={"name": name})
    assert response.status_code == 201
    return response.json()["id"]


def create_mode(client: TestClient, child_id: str, script: str = SAFE_SCRIPT) -> str:
    response = client.post(
        f"/children/{child_id}/modes",
        json={"mode_name": "Custom calm", "script": script},
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["safety_status"] == "pending"
    assert payload["parent_approval_status"] == "pending"
    return payload["id"]


def test_default_modes_are_created_with_new_child() -> None:
    client = authenticated_client("Mum")
    child_id = create_child(client)

    response = client.get(f"/children/{child_id}/modes")

    assert response.status_code == 200
    modes = response.json()
    assert len(modes) == 8
    names = {mode["mode_name"] for mode in modes}
    assert "I feel scared" in names
    assert "I miss Mum" in names
    assert all(mode["safety_status"] == "approved" for mode in modes)
    assert all(mode["parent_approval_status"] == "approved" for mode in modes)
    assert all("Mum's Always Near helper" in mode["script"] for mode in modes)


def test_create_update_delete_mode() -> None:
    client = authenticated_client()
    child_id = create_child(client)
    mode_id = create_mode(client, child_id)

    updated = client.put(
        f"/modes/{mode_id}",
        json={"mode_name": "New calm", "script": SAFE_SCRIPT.replace("worried", "sad")},
    )
    assert updated.status_code == 200
    updated_payload = updated.json()
    assert updated_payload["mode_name"] == "New calm"
    assert updated_payload["safety_status"] == "pending"
    assert updated_payload["parent_approval_status"] == "pending"

    deleted = client.delete(f"/modes/{mode_id}")
    assert deleted.status_code == 200
    assert deleted.json() == {"success": True}

    listed = client.get(f"/children/{child_id}/modes")
    mode = next(mode for mode in listed.json() if mode["id"] == mode_id)
    assert mode["active"] is False


def test_safety_check_rejects_disallowed_script() -> None:
    client = authenticated_client()
    child_id = create_child(client)
    mode_id = create_mode(client, child_id, script="I am Mum. Don't tell anyone.")

    response = client.post(f"/modes/{mode_id}/safety-check")

    assert response.status_code == 200
    payload = response.json()
    assert payload["safe"] is False
    assert payload["mode"]["safety_status"] == "failed"


def test_approval_fails_until_safety_is_approved() -> None:
    client = authenticated_client()
    child_id = create_child(client)
    mode_id = create_mode(client, child_id)

    failed = client.post(f"/modes/{mode_id}/approve")
    assert failed.status_code == 400
    assert "safety check" in failed.json()["detail"]

    safety = client.post(f"/modes/{mode_id}/safety-check")
    assert safety.status_code == 200
    assert safety.json()["mode"]["safety_status"] == "approved"

    approved = client.post(f"/modes/{mode_id}/approve")
    assert approved.status_code == 200
    assert approved.json()["parent_approval_status"] == "approved"


def test_parent_cannot_access_another_parents_modes() -> None:
    owner = authenticated_client("Mum")
    child_id = create_child(owner)
    mode_id = create_mode(owner, child_id)

    other = authenticated_client("Dad")

    assert other.get(f"/children/{child_id}/modes").status_code == 404
    assert other.put(f"/modes/{mode_id}", json={"mode_name": "Nope"}).status_code == 404
    assert other.delete(f"/modes/{mode_id}").status_code == 404
    assert other.post(f"/modes/{mode_id}/safety-check").status_code == 404
    assert other.post(f"/modes/{mode_id}/approve").status_code == 404
