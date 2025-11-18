import pytest
from uuid import uuid4
from datetime import datetime
from httpx import AsyncClient
from app.models.payment import Payment, PaymentStatus, PaymentMethod, InitiatePaymentRequest


@pytest.mark.integration
@pytest.mark.asyncio
class TestPaymentEndpoints:
    """Integration tests for payment API endpoints"""

    async def test_initiate_payment_success(self, client, sample_payment_data):
        """Test successful payment initiation through API"""
        # Arrange
        user_id = uuid4()
        request_data = {
            "order_id": sample_payment_data["order_id"],
            "payment_method": "online"
        }
        
        # Act
        response = await client.post(
            f"/payments/initiate?user_id={user_id}",
            json=request_data
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "payment_id" in data
        assert "confirmation_url" in data
        assert data["confirmation_url"].startswith("https://payment-gateway.com/confirm/")

    async def test_initiate_payment_different_methods(self, client):
        """Test payment initiation with different payment methods"""
        user_id = uuid4()
        methods = ["online", "card", "bonus", "cash"]
        
        for method in methods:
            request_data = {
                "order_id": f"order_{method}",
                "payment_method": method
            }
            
            response = await client.post(
                f"/payments/initiate?user_id={user_id}",
                json=request_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "payment_id" in data
            assert "confirmation_url" in data

    async def test_initiate_payment_invalid_method(self, client):
        """Test payment initiation with invalid payment method"""
        user_id = uuid4()
        request_data = {
            "order_id": "order_123",
            "payment_method": "invalid_method"
        }
        
        response = await client.post(
            f"/payments/initiate?user_id={user_id}",
            json=request_data
        )
        
        assert response.status_code == 422  # Validation error

    async def test_initiate_payment_missing_user_id(self, client):
        """Test payment initiation without user_id parameter"""
        request_data = {
            "order_id": "order_123",
            "payment_method": "online"
        }
        
        response = await client.post(
            "/payments/initiate",
            json=request_data
        )
        
        assert response.status_code == 422  # Missing required parameter

    async def test_process_webhook_success(self, client, sample_payment):
        """Test successful webhook processing"""
        # First create a payment
        user_id = sample_payment.user_id
        request_data = {
            "order_id": sample_payment.order_id,
            "payment_method": sample_payment.payment_method.value
        }
        
        initiate_response = await client.post(
            f"/payments/initiate?user_id={user_id}",
            json=request_data
        )
        
        assert initiate_response.status_code == 200
        payment_data = initiate_response.json()
        payment_id = payment_data["payment_id"]
        
        # Process webhook
        webhook_data = {"payment_id": payment_id}
        
        response = await client.post(
            "/payments/webhook/yandex",
            json=webhook_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Оплачено"

    async def test_process_webhook_invalid_payment_id(self, client):
        """Test webhook processing with invalid payment ID"""
        webhook_data = {"payment_id": str(uuid4())}
        
        response = await client.post(
            "/payments/webhook/yandex",
            json=webhook_data
        )
        
        assert response.status_code == 404

    async def test_process_webhook_missing_payment_id(self, client):
        """Test webhook processing without payment ID"""
        webhook_data = {}
        
        response = await client.post(
            "/payments/webhook/yandex",
            json=webhook_data
        )
        
        assert response.status_code == 422  # Validation error

    async def test_get_payment_status_success(self, client, sample_payment):
        """Test successful payment status retrieval"""
        # First create a payment
        user_id = sample_payment.user_id
        request_data = {
            "order_id": sample_payment.order_id,
            "payment_method": sample_payment.payment_method.value
        }
        
        initiate_response = await client.post(
            f"/payments/initiate?user_id={user_id}",
            json=request_data
        )
        
        assert initiate_response.status_code == 200
        payment_data = initiate_response.json()
        payment_id = payment_data["payment_id"]
        
        # Get payment status
        response = await client.get(f"/payments/{payment_id}/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["payment_id"] == payment_id
        assert data["status"] == "pending"  # Initial status
        assert data["order_id"] == sample_payment.order_id
        assert data["amount"] == 500.0  # Default amount
        assert data["payment_method"] == sample_payment.payment_method.value
        assert "created_at" in data

    async def test_get_payment_status_after_webhook(self, client, sample_payment):
        """Test payment status after webhook processing"""
        # First create a payment
        user_id = sample_payment.user_id
        request_data = {
            "order_id": sample_payment.order_id,
            "payment_method": sample_payment.payment_method.value
        }
        
        initiate_response = await client.post(
            f"/payments/initiate?user_id={user_id}",
            json=request_data
        )
        
        assert initiate_response.status_code == 200
        payment_data = initiate_response.json()
        payment_id = payment_data["payment_id"]
        
        # Process webhook
        webhook_data = {"payment_id": payment_id}
        webhook_response = await client.post(
            "/payments/webhook/yandex",
            json=webhook_data
        )
        
        assert webhook_response.status_code == 200
        
        # Get payment status after webhook
        response = await client.get(f"/payments/{payment_id}/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"  # Status should be success after webhook

    async def test_get_payment_status_invalid_id(self, client):
        """Test payment status retrieval with invalid payment ID"""
        invalid_payment_id = uuid4()
        
        response = await client.get(f"/payments/{invalid_payment_id}/status")
        
        assert response.status_code == 404

    async def test_get_user_payments_success(self, client):
        """Test successful retrieval of user payments"""
        user_id = uuid4()
        
        # Create multiple payments for the user
        for i in range(3):
            request_data = {
                "order_id": f"order_{i}",
                "payment_method": "online"
            }
            
            response = await client.post(
                f"/payments/initiate?user_id={user_id}",
                json=request_data
            )
            assert response.status_code == 200
        
        # Get user payments
        response = await client.get(f"/payments/user/{user_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) == 3
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert data["total_items"] == 3
        assert data["total_pages"] == 1

    async def test_get_user_payments_pagination(self, client):
        """Test pagination for user payments"""
        user_id = uuid4()
        
        # Create multiple payments for the user
        for i in range(5):
            request_data = {
                "order_id": f"order_{i}",
                "payment_method": "online"
            }
            
            response = await client.post(
                f"/payments/initiate?user_id={user_id}",
                json=request_data
            )
            assert response.status_code == 200
        
        # Test different page sizes
        response = await client.get(f"/payments/user/{user_id}?page=1&page_size=2")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["total_items"] == 5
        assert data["total_pages"] == 3

    async def test_get_user_payments_invalid_pagination(self, client):
        """Test pagination with invalid parameters"""
        user_id = uuid4()
        
        # Test invalid page number
        response = await client.get(f"/payments/user/{user_id}?page=0&page_size=20")
        assert response.status_code == 422
        
        # Test invalid page size
        response = await client.get(f"/payments/user/{user_id}?page=1&page_size=0")
        assert response.status_code == 422
        
        # Test page size too large
        response = await client.get(f"/payments/user/{user_id}?page=1&page_size=200")
        assert response.status_code == 422

    async def test_get_user_payments_no_payments(self, client):
        """Test user payments when user has no payments"""
        user_id = uuid4()
        
        response = await client.get(f"/payments/user/{user_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total_items"] == 0
        assert data["total_pages"] == 0