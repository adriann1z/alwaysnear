from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def forbidden_phrases() -> list[str]:
    return [
        "I am " + "Mum",
        "I am " + "Dad",
        "I am " + "really here",
        "I am your " + "real parent",
        "Don't " + "tell anyone",
        "Don" + "\u2019" + "t tell anyone",
        "This is " + "our secret",
        "You " + "only need me",
        "You don't " + "need a grown-up",
        "You don" + "\u2019" + "t need a grown-up",
    ]


def test_runtime_source_does_not_contain_forbidden_phrases() -> None:
    root = Path(__file__).resolve().parents[3]
    runtime_paths = [
        root / "apps" / "api" / "app",
        root / "apps" / "web" / "app",
        root / "apps" / "web" / "components",
        root / "apps" / "web" / "lib",
    ]
    violations: list[str] = []
    for runtime_path in runtime_paths:
        for path in runtime_path.rglob("*"):
            if path.is_file() and path.suffix in {".py", ".ts", ".tsx", ".md"}:
                text = path.read_text(encoding="utf-8").lower()
                for phrase in forbidden_phrases():
                    if phrase.lower() in text:
                        violations.append(f"{path.relative_to(root)}: {phrase}")
    assert violations == []


def test_representative_api_responses_do_not_emit_forbidden_phrases() -> None:
    client = TestClient(app)
    signup = client.post(
        "/auth/signup",
        json={
            "email": f"phrase-sweep-{uuid4()}@example.com",
            "password": "correct-horse-123",
            "display_name": "Mum",
        },
    )
    assert signup.status_code == 201
    client.headers.update({"Authorization": f"Bearer {signup.json()['access_token']}"})
    child = client.post("/children", json={"name": "Sam"})
    assert child.status_code == 201
    conversation = client.post(
        "/conversation/start",
        json={"child_id": child.json()["id"], "mode": "comfort"},
    )
    assert conversation.status_code == 201
    low = client.post(
        "/conversation/message",
        json={
            "conversation_id": conversation.json()["conversation_id"],
            "mode": "comfort",
            "text": "I miss Mum",
        },
    )
    high = client.post(
        "/conversation/message",
        json={
            "conversation_id": conversation.json()["conversation_id"],
            "mode": "comfort",
            "text": "I can't breathe",
        },
    )
    assert low.status_code == 200
    assert high.status_code == 200

    combined = f"{low.text}\n{high.text}".lower()
    for phrase in forbidden_phrases():
        assert phrase.lower() not in combined
