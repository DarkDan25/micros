import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.main import app
import os

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
def sample_movie_data():
    return {
        "title": "Test Movie",
        "description": "A test movie",
        "duration": 120,
        "genre": "Action",
        "rating": "PG-13",
        "release_year": 2023
    }

@pytest.fixture
def sample_session_data():
    return {
        "movie_id": 1,
        "start_time": "2024-01-01T10:00:00",
        "end_time": "2024-01-01T12:00:00",
        "hall_number": 1,
        "price": 15.0,
        "available_seats": 100
    }