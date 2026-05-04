from app.db.base import Base
from app import models  # noqa: F401


def test_expected_tables_are_registered() -> None:
    assert {
        "users",
        "parents",
        "children",
        "helper_profiles",
        "avatars",
        "voices",
        "comfort_modes",
        "conversations",
        "messages",
        "alerts",
        "audit_logs",
    }.issubset(Base.metadata.tables.keys())
