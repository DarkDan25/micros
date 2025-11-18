import pytest
from uuid import uuid4
from datetime import datetime
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ..app.database import Base, get_db
from ..app.main import app
from ..app.models.user import User

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
async def client(db_session):
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def sample_user():
    """Create a sample user for testing"""
    return User(
        user_id=uuid4(),
        email="test@example.com",
        password_hash="hashed_password_123",
        first_name="John",
        last_name="Doe",
        phone="+1234567890",
        created_at=datetime.now(),
        updated_at=None
    )

@pytest.fixture
def sample_users():
    """Create multiple sample users for testing"""
    users = []
    for i in range(3):
        user = User(
            user_id=uuid4(),
            email=f"user{i+1}@example.com",
            password_hash=f"hashed_password_{i+1}",
            first_name=f"First{i+1}",
            last_name=f"Last{i+1}",
            phone=f"+123456789{i}",
            created_at=datetime.now(),
            updated_at=None
        )
        users.append(user)
    return users

@pytest.fixture
def sample_register_data():
    """Sample user registration data for API requests"""
    return {
        "email": "newuser@example.com",
        "password": "securepassword123",
        "first_name": "Jane",
        "last_name": "Smith",
        "phone": "+0987654321"
    }

@pytest.fixture
def sample_login_data():
    """Sample user login data for API requests"""
    return {
        "email": "test@example.com",
        "password": "testpassword123"
    }

@pytest.fixture
def sample_update_profile_data():
    """Sample user profile update data for API requests"""
    return {
        "first_name": "UpdatedFirst",
        "last_name": "UpdatedLast",
        "phone": "+1111111111"
    }

@pytest.fixture
def sample_user_id():
    """Sample user ID for testing"""
    return uuid4()

@pytest.fixture
def sample_auth_token():
    """Sample authentication token for testing"""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNTUwZTg0MDAtZTI5Yi00MWQ0LWE3MTYtNDQ2NjU1NDQwMDAwIiwiZXhwIjoxNzM1NzEwODAwfQ.sample_token_signature"