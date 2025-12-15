import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from ..app.database import Base, get_db
from ..app.main import app
from ..app.models.payment import Payment, PaymentStatus, PaymentMethod
from ..app.services.payment_service import PaymentService

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def payment_service(db_session):
    return PaymentService(db_session)


@pytest.fixture(scope="function")
def client(db_session):
    # override get_db for FastAPI
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_payment():
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
    user_id = uuid4()
    payments = []
    for i in range(3):
        payments.append(
            Payment(
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
        )
    return payments
