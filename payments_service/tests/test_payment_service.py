import pytest
from uuid import uuid4
from datetime import datetime
from unittest.mock import Mock
from ..app.services.payment_service import PaymentService
from ..app.models.payment import Payment, PaymentStatus, PaymentMethod, InitiatePaymentRequest


@pytest.fixture
def payment_service():
    return PaymentService()


@pytest.fixture
def mock_payment_repo():
    return Mock()


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


class TestPaymentServiceUnit:
    """Unit tests for PaymentService"""

    @pytest.mark.unit
    def test_initiate_payment_success(self, payment_service, sample_payment):
        """Test successful payment initiation"""
        # Arrange
        user_id = sample_payment.user_id
        request = InitiatePaymentRequest(
            order_id=sample_payment.order_id,
            payment_method=sample_payment.payment_method
        )
        
        # Mock the repository
        payment_service.payment_repo.create_payment = Mock(return_value=sample_payment)
        
        # Act
        result = payment_service.initiate_payment(user_id, request)
        
        # Assert
        assert result.payment_id == sample_payment.payment_id
        assert result.order_id == sample_payment.order_id
        assert result.user_id == sample_payment.user_id
        assert result.amount == 500.0
        assert result.status == PaymentStatus.PENDING
        assert result.payment_method == PaymentMethod.ONLINE
        assert result.confirmation_url is not None
        assert result.created_at is not None
        
        payment_service.payment_repo.create_payment.assert_called_once()

    @pytest.mark.unit
    def test_initiate_payment_different_methods(self, payment_service):
        """Test payment initiation with different payment methods"""
        user_id = uuid4()
        
        for method in [PaymentMethod.ONLINE, PaymentMethod.CARD, PaymentMethod.BONUS, PaymentMethod.CASH]:
            request = InitiatePaymentRequest(
                order_id=f"order_{method.value}",
                payment_method=method
            )
            
            payment_service.payment_repo.create_payment = Mock()
            
            result = payment_service.initiate_payment(user_id, request)
            
            assert result.payment_method == method
            assert result.status == PaymentStatus.PENDING
            assert result.amount == 500.0  # Default amount from _calculate_amount

    @pytest.mark.unit
    def test_process_webhook_success(self, payment_service, sample_payment):
        """Test successful webhook processing"""
        # Arrange
        payment_service.payment_repo.get_payment_by_id = Mock(return_value=sample_payment)
        payment_service.payment_repo.update_payment = Mock()
        
        # Act
        result = payment_service.process_webhook(sample_payment.payment_id)
        
        # Assert
        assert result["status"] == "Оплачено"
        assert sample_payment.status == PaymentStatus.SUCCESS
        assert sample_payment.updated_at is not None
        
        payment_service.payment_repo.get_payment_by_id.assert_called_once_with(sample_payment.payment_id)
        payment_service.payment_repo.update_payment.assert_called_once_with(sample_payment)

    @pytest.mark.unit
    def test_process_webhook_payment_not_found(self, payment_service):
        """Test webhook processing when payment not found"""
        # Arrange
        payment_id = uuid4()
        payment_service.payment_repo.get_payment_by_id = Mock(side_effect=KeyError("Payment not found"))
        
        # Act & Assert
        with pytest.raises(KeyError, match="Payment not found"):
            payment_service.process_webhook(payment_id)

    @pytest.mark.unit
    def test_get_payment_status_success(self, payment_service, sample_payment):
        """Test successful payment status retrieval"""
        # Arrange
        payment_service.payment_repo.get_payment_by_id = Mock(return_value=sample_payment)
        
        # Act
        result = payment_service.get_payment_status(sample_payment.payment_id)
        
        # Assert
        assert result.payment_id == sample_payment.payment_id
        assert result.status == sample_payment.status
        assert result.order_id == sample_payment.order_id
        assert result.amount == sample_payment.amount
        assert result.payment_method == sample_payment.payment_method
        assert result.created_at == sample_payment.created_at

    @pytest.mark.unit
    def test_get_payment_status_not_found(self, payment_service):
        """Test payment status retrieval when payment not found"""
        # Arrange
        payment_id = uuid4()
        payment_service.payment_repo.get_payment_by_id = Mock(side_effect=KeyError("Payment not found"))
        
        # Act & Assert
        with pytest.raises(KeyError, match="Payment not found"):
            payment_service.get_payment_status(payment_id)

    @pytest.mark.unit
    def test_get_user_payments_success(self, payment_service):
        """Test successful retrieval of user payments"""
        # Arrange
        user_id = uuid4()
        page = 1
        page_size = 20
        
        sample_payments = [
            Payment(
                payment_id=uuid4(),
                order_id=f"order_{i}",
                user_id=user_id,
                amount=100.0 * i,
                status=PaymentStatus.SUCCESS,
                payment_method=PaymentMethod.ONLINE,
                confirmation_url=f"https://payment-gateway.com/confirm/{uuid4()}",
                created_at=datetime.now(),
                updated_at=datetime.now()
            ) for i in range(1, 4)
        ]
        
        payment_service.payment_repo.get_user_payments = Mock(return_value=(sample_payments, len(sample_payments), 1))
        
        # Act
        result = payment_service.get_user_payments(user_id, page, page_size)
        
        # Assert
        assert result[0] == sample_payments
        assert result[1] == len(sample_payments)  # total_items
        assert result[2] == 1  # total_pages
        
        payment_service.payment_repo.get_user_payments.assert_called_once_with(user_id, page, page_size)

    @pytest.mark.unit
    def test_calculate_amount_default(self, payment_service):
        """Test default amount calculation"""
        # Act
        result = payment_service._calculate_amount("any_order_id")
        
        # Assert
        assert result == 500.0  # Default amount from the method

    @pytest.mark.unit
    def test_calculate_amount_different_orders(self, payment_service):
        """Test that amount calculation is consistent for different order IDs"""
        # The current implementation always returns 500.0
        # This test ensures consistency
        order_ids = ["order_1", "order_2", "order_123", "order_abc"]
        
        for order_id in order_ids:
            result = payment_service._calculate_amount(order_id)
            assert result == 500.0

    @pytest.mark.unit
    def test_payment_status_transitions(self, payment_service, sample_payment):
        """Test payment status transitions through webhook processing"""
        # Initial state
        assert sample_payment.status == PaymentStatus.PENDING
        
        # Process webhook
        payment_service.payment_repo.get_payment_by_id = Mock(return_value=sample_payment)
        payment_service.payment_repo.update_payment = Mock()
        
        payment_service.process_webhook(sample_payment.payment_id)
        
        # After webhook processing
        assert sample_payment.status == PaymentStatus.SUCCESS
        assert sample_payment.updated_at is not None