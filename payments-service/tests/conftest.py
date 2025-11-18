import pytest
from uuid import uuid4
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.main import app
from app.models.payment import Payment, PaymentStatus, PaymentMethod

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
def sample_payment_data():
    return {
        "order_id": "order_12345",
        "amount": 1500,
        "currency": "RUB",
        "payment_method": "credit_card",
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "card_number": "4111111111111111",
        "expiry_month": 12,
        "expiry_year": 2025,
        "cvv": "123"
    }

@pytest.fixture
def sample_refund_data():
    return {
        "payment_id": "payment_12345",
        "amount": 500,
        "reason": "Customer requested refund"
    }

@pytest.fixture
def sample_payment():
    """Create a sample payment for testing"""
    return Payment(
        payment_id=uuid4(),
        order_id="order_123",
        user_id=uuid4(),
        amount=500.0,
        status=PaymentStatus.PENDING,
        payment_method=PaymentMethod.ONLINE,
        confirmation_url=f"https://payment-gateway.com/confirm/{uuid4()}",
        created_at=datetime.now(),
        updated_at=None
    )

@pytest.fixture
def sample_payments():
    """Create multiple sample payments for testing"""
    user_id = uuid4()
    payments = []
    
    for i in range(3):
        payment = Payment(
            payment_id=uuid4(),
            order_id=f"order_{i}",
            user_id=user_id,
            amount=100.0 * (i + 1),
            status=PaymentStatus.SUCCESS,
            payment_method=PaymentMethod.ONLINE,
            confirmation_url=f"https://payment-gateway.com/confirm/{uuid4()}",
            created_at=datetime.now() - timedelta(days=i),
            updated_at=datetime.now()
        )
        payments.append(payment)
    
    return payments