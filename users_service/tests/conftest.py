import pytest
from uuid import uuid4
from datetime import datetime

import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ..app.database import Base, get_db
from ..app.main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    yield TestingSessionLocal()
    Base.metadata.drop_all(bind=engine)


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    # base_url без /api, чтобы не дублировать префикс
    async with AsyncClient(transport=transport, base_url="http://testserver") as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_register_data():
    return {
        "email": "newuser@example.com",
        "password": "securepassword123",
        "first_name": "Jane",
        "last_name": "Smith",
        "phone": "+0987654321"
    }


@pytest.fixture
def sample_login_data():
    return {
        "email": "test@example.com",
        "password": "testpassword123"
    }


@pytest.fixture
def sample_update_profile_data():
    return {
        "first_name": "UpdatedFirst",
        "last_name": "UpdatedLast",
        "phone": "+1111111111"
    }
