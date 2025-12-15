import pytest
import pytest_asyncio
from uuid import uuid4
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..app.main import app
from ..app.database import Base, get_db
from ..app.services.review_service import ReviewService
from ..app.endpoints.review_router import get_review_service

# Тестовая SQLite база на диске (чтобы таблицы были видны всем сессиям)
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Создаём таблицы один раз
Base.metadata.create_all(bind=test_engine)

# Перекрываем get_db
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest_asyncio.fixture(scope="function")
async def client():
    # Перекрываем ReviewService для каждого запроса
    def get_review_service_override():
        db = TestingSessionLocal()
        return ReviewService(db=db)

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_review_service] = get_review_service_override

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client

    app.dependency_overrides.clear()

# Простейшие фикстуры
@pytest.fixture
def sample_user_id():
    return uuid4()

@pytest.fixture
def sample_target_id():
    return "movie_test"

@pytest.fixture
def sample_review_data():
    return {
        "target_id": "movie_test",
        "rating": 8,
        "text": "Great movie!"
    }
