# Test fixtures: an isolated throwaway database + a TestClient.
import os
import pathlib
import tempfile

# Must be set *before* app.db.database is imported so the engine points at a temp file.
_TMP = pathlib.Path(tempfile.mkdtemp(prefix="banktest-"))
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP / 'test.db'}"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.services.security_service import login_throttle  # noqa: E402


@pytest.fixture(autouse=True)
def _fresh_state():
    """Empty schema + no leftover lockouts before every test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    login_throttle._failures.clear()
    login_throttle._locked_until.clear()
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
