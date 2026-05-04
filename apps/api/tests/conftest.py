import os
import tempfile
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config


os.environ["JWT_SECRET"] = "test-only-secret-change-me"
TEST_ROOT = Path(tempfile.mkdtemp(prefix="always-near-tests-"))
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_ROOT / 'test.db'}"
os.environ["STORAGE_PROVIDER"] = "local"
os.environ["STORAGE_LOCAL_PATH"] = str(TEST_ROOT / "storage")
os.environ["VOICE_PROVIDER"] = "local"
os.environ["OPENAI_API_KEY"] = ""
os.environ["ELEVENLABS_API_KEY"] = ""


@pytest.fixture(scope="session", autouse=True)
def migrated_test_database() -> None:
    config = Config("alembic.ini")
    command.upgrade(config, "head")
