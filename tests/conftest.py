import os

os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["TRANSPORT_PROVIDER"] = "mock"
os.environ["PAYMENTS_MODE"] = "sandbox"
os.environ["ADMIN_API_KEY"] = "test-admin-key"

import pytest
from fastapi.testclient import TestClient

from app.core.db import engine
from app.main import app
from app.models import Base


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
