import asyncio
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.security import create_access_token, hash_password
from app.db.session import AsyncSessionLocal
from app.main import app
from app.models.audit_logs import AuditLog
from app.models.users import User


def parent_client(display_name: str = "Mum") -> TestClient:
    client = TestClient(app)
    response = client.post(
        "/auth/signup",
        json={
            "email": f"admin-parent-{uuid4()}@example.com",
            "password": "correct-horse-123",
            "display_name": display_name,
        },
    )
    assert response.status_code == 201
    client.headers.update({"Authorization": f"Bearer {response.json()['access_token']}"})
    return client


def admin_client() -> TestClient:
    user_id = asyncio.run(create_admin_user())
    client = TestClient(app)
    client.headers.update({"Authorization": f"Bearer {create_access_token(str(user_id))}"})
    return client


async def create_admin_user():
    async with AsyncSessionLocal() as db:
        user = User(
            email=f"stage11-admin-{uuid4()}@example.com",
            password_hash=hash_password("correct-horse-123"),
            role="admin",
        )
        db.add(user)
        await db.commit()
        return user.id


def create_child_and_alert(client: TestClient, text: str, child_name: str = "Sam") -> dict:
    child_response = client.post("/children", json={"name": child_name})
    assert child_response.status_code == 201
    conversation_response = client.post(
        "/conversation/start",
        json={"child_id": child_response.json()["id"], "mode": "comfort"},
    )
    assert conversation_response.status_code == 201
    message_response = client.post(
        "/conversation/message",
        json={
            "conversation_id": conversation_response.json()["conversation_id"],
            "mode": "comfort",
            "text": text,
        },
    )
    assert message_response.status_code == 200
    alert_response = client.get("/alerts")
    assert alert_response.status_code == 200
    return alert_response.json()[0]


def test_parent_cannot_access_admin_routes() -> None:
    client = parent_client()

    assert client.get("/admin/alerts").status_code == 403
    assert client.get("/admin/audit-logs").status_code == 403
    assert client.get("/admin/users").status_code == 403
    assert client.get("/admin/system-health").status_code == 403


def test_admin_can_fetch_alerts_and_audit_logs() -> None:
    parent = parent_client()
    create_child_and_alert(parent, "I can't breathe")

    admin = admin_client()
    alerts = admin.get("/admin/alerts")
    audit_logs = admin.get("/admin/audit-logs")

    assert alerts.status_code == 200
    assert audit_logs.status_code == 200
    assert any(alert["severity"] == "HIGH" for alert in alerts.json())
    assert any(log["action"] == "admin.audit_logs.view" for log in audit_logs.json())


def test_admin_alert_filters_return_matching_results() -> None:
    parent = parent_client()
    create_child_and_alert(parent, "I can't breathe")
    create_child_and_alert(parent, "I am so scared and I can't calm down", "Ari")

    admin = admin_client()
    high = admin.get("/admin/alerts?severity=HIGH")
    medium = admin.get("/admin/alerts?severity=MEDIUM")

    assert high.status_code == 200
    assert medium.status_code == 200
    assert high.json()
    assert medium.json()
    assert all(alert["severity"] == "HIGH" for alert in high.json())
    assert all(alert["severity"] == "MEDIUM" for alert in medium.json())


def test_admin_audit_filters_return_matching_results() -> None:
    parent = parent_client()
    create_child_and_alert(parent, "I can't breathe")

    admin = admin_client()
    response = admin.get("/admin/audit-logs?action=alert.created")

    assert response.status_code == 200
    assert response.json()
    assert all(log["action"] == "alert.created" for log in response.json())


def test_admin_access_triggers_audit_log() -> None:
    admin = admin_client()
    before = asyncio.run(count_audit_logs("admin.alerts.view"))

    response = admin.get("/admin/alerts")
    after = asyncio.run(count_audit_logs("admin.alerts.view"))

    assert response.status_code == 200
    assert after == before + 1


async def count_audit_logs(action: str) -> int:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(AuditLog).where(AuditLog.action == action)
        )
        return len(result.scalars().all())
