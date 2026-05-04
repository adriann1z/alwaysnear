from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def authenticated_client(display_name: str = "Mum") -> TestClient:
    client = TestClient(app)
    response = client.post(
        "/auth/signup",
        json={
            "email": f"alerts-{uuid4()}@example.com",
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


def start_conversation(client: TestClient, child_id: str) -> str:
    response = client.post(
        "/conversation/start",
        json={"child_id": child_id, "mode": "comfort"},
    )
    assert response.status_code == 201
    return response.json()["conversation_id"]


def send_message(client: TestClient, conversation_id: str, text: str, mode: str = "comfort") -> dict:
    response = client.post(
        "/conversation/message",
        json={"conversation_id": conversation_id, "mode": mode, "text": text},
    )
    assert response.status_code == 200
    return response.json()


def create_alert_from_message(client: TestClient, text: str, child_name: str = "Sam") -> dict:
    child_id = create_child(client, child_name)
    conversation_id = start_conversation(client, child_id)
    send_message(client, conversation_id, text)
    alerts = client.get("/alerts")
    assert alerts.status_code == 200
    return alerts.json()[0]


def test_high_and_medium_risk_messages_create_alerts() -> None:
    client = authenticated_client()
    child_id = create_child(client)
    conversation_id = start_conversation(client, child_id)

    high = send_message(client, conversation_id, "I can't breathe")
    assert high["risk_level"] == "HIGH_RISK"

    medium = send_message(client, conversation_id, "I am so scared and I can't calm down")
    assert medium["risk_level"] == "MEDIUM_RISK"

    response = client.get("/alerts")
    assert response.status_code == 200
    alerts = response.json()
    severities = {alert["severity"] for alert in alerts}
    assert {"HIGH", "MEDIUM"}.issubset(severities)
    assert all(alert["parent_viewed"] is False for alert in alerts)
    assert all(alert["trigger_summary"] for alert in alerts)


def test_alerts_endpoint_returns_only_current_parent_alerts() -> None:
    owner = authenticated_client("Mum")
    owner_alert = create_alert_from_message(owner, "I can't breathe", "Sam")

    other = authenticated_client("Dad")
    create_alert_from_message(other, "I am so scared and I can't calm down", "Ari")

    owner_list = owner.get("/alerts")
    other_list = other.get("/alerts")

    assert owner_list.status_code == 200
    assert other_list.status_code == 200
    owner_ids = {alert["id"] for alert in owner_list.json()}
    other_ids = {alert["id"] for alert in other_list.json()}
    assert owner_alert["id"] in owner_ids
    assert owner_ids.isdisjoint(other_ids)


def test_alert_detail_and_mark_viewed_reject_other_parent() -> None:
    owner = authenticated_client("Mum")
    alert = create_alert_from_message(owner, "I can't breathe")

    other = authenticated_client("Dad")

    assert other.get(f"/alerts/{alert['id']}").status_code == 404
    assert other.post(f"/alerts/{alert['id']}/mark-viewed").status_code == 404


def test_mark_viewed_updates_only_parent_viewed() -> None:
    client = authenticated_client()
    alert = create_alert_from_message(client, "I can't breathe")

    before = client.get(f"/alerts/{alert['id']}")
    assert before.status_code == 200
    before_payload = before.json()

    viewed = client.post(f"/alerts/{alert['id']}/mark-viewed")
    assert viewed.status_code == 200
    viewed_payload = viewed.json()

    assert before_payload["parent_viewed"] is False
    assert viewed_payload["parent_viewed"] is True
    for field in [
        "id",
        "child_id",
        "child_name",
        "conversation_id",
        "severity",
        "category",
        "status",
        "mode",
        "trigger_summary",
        "details",
        "parent_notified",
        "created_at",
    ]:
        assert viewed_payload[field] == before_payload[field]


def test_alerts_are_sorted_newest_first() -> None:
    client = authenticated_client()
    child_id = create_child(client)
    conversation_id = start_conversation(client, child_id)

    send_message(client, conversation_id, "I can't breathe")
    send_message(client, conversation_id, "I am so scared and I can't calm down")

    response = client.get("/alerts")
    assert response.status_code == 200
    alerts = response.json()

    assert len(alerts) >= 2
    created_values = [alert["created_at"] for alert in alerts[:2]]
    assert created_values == sorted(created_values, reverse=True)
    assert alerts[0]["severity"] == "MEDIUM"
