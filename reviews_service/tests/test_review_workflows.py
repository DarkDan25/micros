import pytest
import pytest_asyncio
import asyncio
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..app.main import app
from ..app.database import Base
from ..app.services.review_service import ReviewService
from ..app.endpoints.review_router import get_review_service

# Тестовая SQLite база
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Фикстура для DB session
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

    # Override для Depends(get_review_service)
    app.dependency_overrides[get_review_service] = get_review_service_override

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# Простые фикстуры
@pytest.fixture
def sample_user_id():
    return uuid4()


@pytest.fixture
def sample_target_id():
    return "movie_test"


@pytest.mark.component
@pytest.mark.asyncio
class TestReviewWorkflows:

    async def test_complete_review_lifecycle(self, client, sample_user_id, sample_target_id):
        # Создание
        create_request = {"target_id": sample_target_id, "rating": 8, "text": "Great movie!"}
        r = await client.post(f"/api/reviews/?user_id={sample_user_id}", json=create_request)
        assert r.status_code == 200
        data = r.json()
        review_id = data["id"]
        assert data["status"] == "active"

        # Обновление
        update_request = {"rating": 9, "text": "Even better!"}
        r = await client.put(f"/api/reviews/{review_id}?user_id={sample_user_id}", json=update_request)
        assert r.status_code == 200
        updated = r.json()
        assert updated["rating"] == 9
        assert updated["text"] == "Even better!"

        # Получение списка
        r = await client.get(f"/api/reviews/?target_id={sample_target_id}")
        assert r.status_code == 200
        data = r.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == review_id

        # Удаление
        r = await client.delete(f"/api/reviews/{review_id}?user_id={sample_user_id}")
        assert r.status_code == 200
        assert r.json()["status"] == "deleted"

    async def test_multiple_user_reviews_workflow(self, client, sample_target_id):
        user_ids = [uuid4() for _ in range(5)]
        for i, uid in enumerate(user_ids):
            r = await client.post(f"/api/reviews/?user_id={uid}", json={"target_id": sample_target_id, "rating": 6+i, "text": f"Review {i}"})
            assert r.status_code == 200

        r = await client.get(f"/api/reviews/?target_id={sample_target_id}")
        assert r.status_code == 200
        data = r.json()
        assert len(data["items"]) == 5

    async def test_review_prevention_workflow(self, client, sample_user_id, sample_target_id):
        r1 = await client.post(f"/api/reviews/?user_id={sample_user_id}", json={"target_id": sample_target_id, "rating": 7, "text": "First"})
        assert r1.status_code == 200
        r2 = await client.post(f"/api/reviews/?user_id={sample_user_id}", json={"target_id": sample_target_id, "rating": 8, "text": "Second"})
        assert r2.status_code == 400
        assert "already reviewed" in r2.json()["detail"]

    async def test_concurrent_review_creation(self, client, sample_target_id):
        from ..app.main import app
        from ..app.database import Base
        from ..app.services.review_service import ReviewService
        from httpx import AsyncClient
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy import create_engine
        from uuid import uuid4

        # Новый engine и session factory для каждого запроса
        engine = create_engine("sqlite:///./test.db", connect_args={"check_same_thread": False})
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        async def create_review(uid, rating):
            db = TestingSessionLocal()
            try:
                service = ReviewService(db)
                async with AsyncClient(app=app, base_url="http://test") as client:
                    resp = await client.post(f"/api/reviews/?user_id={uid}",
                                             json={"target_id": sample_target_id, "rating": rating,
                                                   "text": f"Review {uid}"})
                    return resp
            finally:
                db.close()

        user_ids = [uuid4() for _ in range(5)]
        import asyncio
        tasks = [create_review(uid, 6 + i) for i, uid in enumerate(user_ids)]
        responses = await asyncio.gather(*tasks)
        success = [r for r in responses if r.status_code == 200]
        assert len(success) == 5

    async def test_review_permissions_workflow(self, client, sample_target_id):
        user1, user2 = uuid4(), uuid4()
        r = await client.post(f"/api/reviews/?user_id={user1}", json={"target_id": sample_target_id, "rating": 8, "text": "U1"})
        review_id = r.json()["id"]

        # user2 не может редактировать
        r_edit = await client.put(f"/api/reviews/{review_id}?user_id={user2}", json={"rating": 9, "text": "U2"})
        assert r_edit.status_code == 403

        # user2 не может удалить
        r_del = await client.delete(f"/api/reviews/{review_id}?user_id={user2}")
        assert r_del.status_code == 403

        # user1 может редактировать
        r_edit = await client.put(f"/api/reviews/{review_id}?user_id={user1}", json={"rating": 10, "text": "U1 updated"})
        assert r_edit.status_code == 200

    async def test_review_statistics_workflow(self, client):
        target_id = f"stats_{uuid4()}"
        for i in range(1, 6):
            r = await client.post(f"/api/reviews/?user_id={uuid4()}", json={"target_id": target_id, "rating": i, "text": f"{i}"})
            assert r.status_code == 200

        r_stats = await client.get(f"/api/reviews/{target_id}/stats")
        assert r_stats.status_code == 200
        data = r_stats.json()
        assert data["total_reviews"] == 5
        assert data["average_rating"] == 3.0

    async def test_review_pagination_workflow(self, client):
        target_id = f"pag_{uuid4()}"
        for i in range(25):
            r = await client.post(f"/api/reviews/?user_id={uuid4()}", json={"target_id": target_id, "rating": 5+i%6, "text": f"{i}"})
            assert r.status_code == 200

        r_page = await client.get(f"/api/reviews/?target_id={target_id}&page=1&page_size=10")
        data = r_page.json()
        assert len(data["items"]) == 10
        assert data["page"] == 1
        assert data["total_items"] == 25
        assert data["total_pages"] == 3

    async def test_review_error_handling_workflow(self, client, sample_user_id, sample_target_id):
        # Неверная оценка
        r_invalid = await client.post(f"/api/reviews/?user_id={sample_user_id}", json={"target_id": sample_target_id, "rating": 15, "text": "X"})
        assert r_invalid.status_code == 422

        # Отсутствие user_id
        r_no_user = await client.post("/api/reviews/", json={"target_id": sample_target_id, "rating": 8, "text": "X"})
        assert r_no_user.status_code == 422
