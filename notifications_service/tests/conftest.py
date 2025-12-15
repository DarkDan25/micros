import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..app.database import Base, get_db
from ..app.main import app
from uuid import UUID

# Тестовая SQLite БД
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_notifications.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Override зависимости get_db
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db_session():
    """Создает и сбрасывает таблицы перед/после тестов"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """TestClient с переопределением get_db"""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_notification_data():
    return {
        "user_id": UUID("550e8400-e29b-41d4-a716-446655440000"),
        "type": "receipt",
        "message": "Your booking has been confirmed for Avatar 2",
        "data": {"booking_id": "12345", "movie_title": "Avatar 2"}
    }


@pytest.fixture
def sample_bulk_notification_data():
    return {
        "user_ids": [
            UUID("550e8400-e29b-41d4-a716-446655440000"),
            UUID("660e8400-e29b-41d4-a716-446655440001"),
            UUID("770e8400-e29b-41d4-a716-446655440002")
        ],
        "type": "promotional",
        "message": "Get 20% off on your next booking!",
        "data": {"offer_code": "SAVE20", "discount_percent": 20}
    }
