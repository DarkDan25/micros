import pytest
import pytest_asyncio
from uuid import uuid4
from httpx import AsyncClient

from ..app.main import app
from ..app.services.review_service import ReviewService
from ..app.database import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Настройка тестовой SQLite базы
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


# AsyncClient с override зависимостей
@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    def get_review_service_override():
        return ReviewService(db_session)

    app.dependency_overrides[ReviewService] = get_review_service_override
    # Если у тебя используется Depends(get_review_service) в router
    from ..app.endpoints.review_router import get_review_service
    app.dependency_overrides[get_review_service] = get_review_service_override

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_id():
    return uuid4()


@pytest.fixture
def sample_target_id():
    return "movie_test"


@pytest.fixture
def sample_review_data():
    return {"target_id": "movie_test", "rating": 8, "text": "Great movie!"}


@pytest.mark.integration
@pytest.mark.asyncio
class TestReviewEndpoints:

    async def test_create_review_success(self, client, sample_review_data, sample_user_id):
        r = await client.post(f"/api/reviews/?user_id={sample_user_id}", json=sample_review_data)
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert data["user_id"] == str(sample_user_id)
        assert data["target_id"] == sample_review_data["target_id"]
        assert data["rating"] == sample_review_data["rating"]
        assert data["text"] == sample_review_data["text"]
        assert data["status"] == "active"
        assert "created_at" in data
        assert data["updated_at"] is None

    async def test_create_review_duplicate(self, client, sample_review_data, sample_user_id):
        await client.post(f"/api/reviews/?user_id={sample_user_id}", json=sample_review_data)
        r2 = await client.post(f"/api/reviews/?user_id={sample_user_id}", json=sample_review_data)
        assert r2.status_code == 400
        assert "already reviewed" in r2.json()["detail"]

    async def test_create_review_invalid_rating(self, client, sample_user_id):
        invalid_low = {"target_id": "movie_test", "rating": 0, "text": "Invalid"}
        invalid_high = {"target_id": "movie_test", "rating": 11, "text": "Invalid"}
        r_low = await client.post(f"/api/reviews/?user_id={sample_user_id}", json=invalid_low)
        r_high = await client.post(f"/api/reviews/?user_id={sample_user_id}", json=invalid_high)
        assert r_low.status_code == 422
        assert r_high.status_code == 422

    async def test_create_review_missing_user_id(self, client, sample_review_data):
        r = await client.post("/api/reviews/", json=sample_review_data)
        assert r.status_code == 422

    async def test_get_reviews_by_target_success(self, client, sample_target_id):
        for i in range(3):
            uid = uuid4()
            await client.post(f"/api/reviews/?user_id={uid}", json={"target_id": sample_target_id, "rating": 6+i, "text": f"Review {i}"})
        r = await client.get(f"/api/reviews/?target_id={sample_target_id}")
        assert r.status_code == 200
        data = r.json()
        assert len(data["items"]) == 3
        for review in data["items"]:
            assert review["target_id"] == sample_target_id

    async def test_get_reviews_pagination(self, client, sample_target_id):
        for i in range(15):
            uid = uuid4()
            await client.post(f"/api/reviews/?user_id={uid}", json={"target_id": sample_target_id, "rating": 5+i%6, "text": f"Review {i}"})
        page1 = await client.get(f"/api/reviews/?target_id={sample_target_id}&page=1&page_size=5")
        page2 = await client.get(f"/api/reviews/?target_id={sample_target_id}&page=2&page_size=5")
        assert page1.status_code == 200
        assert len(page1.json()["items"]) == 5
        assert page2.status_code == 200
        assert len(page2.json()["items"]) == 5

    async def test_update_review_success(self, client, sample_review_data, sample_user_id):
        r_create = await client.post(f"/api/reviews/?user_id={sample_user_id}", json=sample_review_data)
        rid = r_create.json()["id"]
        r_update = await client.put(f"/api/reviews/{rid}?user_id={sample_user_id}", json={"rating": 7, "text": "Updated"})
        assert r_update.status_code == 200
        updated = r_update.json()
        assert updated["rating"] == 7
        assert updated["text"] == "Updated"

    async def test_delete_review_success(self, client, sample_review_data, sample_user_id):
        r_create = await client.post(f"/api/reviews/?user_id={sample_user_id}", json=sample_review_data)
        rid = r_create.json()["id"]
        r_delete = await client.delete(f"/api/reviews/{rid}?user_id={sample_user_id}")
        assert r_delete.status_code == 200
        assert r_delete.json()["status"] == "deleted"

    async def test_get_review_stats_success(self, client, sample_target_id):
        ratings = [8, 6, 9]
        for r in ratings:
            await client.post(f"/api/reviews/?user_id={uuid4()}", json={"target_id": sample_target_id, "rating": r, "text": f"Rating {r}"})
        r_stats = await client.get(f"/api/reviews/{sample_target_id}/stats")
        assert r_stats.status_code == 200
        stats = r_stats.json()
        assert stats["total_reviews"] == len(ratings)
        assert abs(stats["average_rating"] - sum(ratings)/len(ratings)) < 0.1
