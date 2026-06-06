import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ.setdefault("OPENAI_MODEL", "gpt-4.1-mini")

from app.db.session import Base, engine
from app.main import app
from app.core.config import get_settings


@pytest.fixture(autouse=True)
def reset_settings() -> Iterator[None]:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def reset_database() -> Iterator[None]:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
