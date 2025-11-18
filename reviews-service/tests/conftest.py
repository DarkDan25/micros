import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.main import app
from app.models.review import Review, ReviewStatus

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

@pytest.fixture(scope="function")
def client(db_session):
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def sample_review():
    """Create a sample review for testing"""
    return Review(
        id=uuid4(),
        user_id=uuid4(),
        target_id="movie_123",
        rating=8,
        text="Отличный фильм! Очень понравилась игра актеров и сюжет.",
        status=ReviewStatus.ACTIVE,
        created_at=datetime.now(),
        updated_at=None
    )

@pytest.fixture
def sample_reviews():
    """Create multiple sample reviews for testing"""
    user_id = uuid4()
    target_id = "movie_456"
    reviews = []
    
    for i in range(3):
        review = Review(
            id=uuid4(),
            user_id=user_id if i % 2 == 0 else uuid4(),  # Mix of same and different users
            target_id=target_id,
            rating=5 + i * 2,  # Ratings: 5, 7, 9
            text=f"Review text {i+1}",
            status=ReviewStatus.ACTIVE,
            created_at=datetime.now() - timedelta(days=i),
            updated_at=None
        )
        reviews.append(review)
    
    return reviews

@pytest.fixture
def sample_review_data():
    """Sample review data for API requests"""
    return {
        "target_id": "movie_789",
        "rating": 9,
        "text": "Amazing movie with great special effects and storyline!"
    }

@pytest.fixture
def sample_update_review_data():
    """Sample review update data for API requests"""
    return {
        "rating": 7,
        "text": "Updated review: Good movie but could be better."
    }

@pytest.fixture
def sample_user_id():
    """Sample user ID for testing"""
    return uuid4()

@pytest.fixture
def sample_target_id():
    """Sample target ID for testing"""
    return "movie_test_123"