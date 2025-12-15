import pytest
import asyncio
from uuid import uuid4
from datetime import datetime, timedelta
from httpx import AsyncClient
from app.models.payment import Payment, PaymentStatus, PaymentMethod


@pytest.mark.component
@pytest.mark.asyncio
class TestPaymentWorkflows:
    """Component tests for complete payment workflows"""

    async def test_complete_payment_lifecycle(self, client, sample_payment_data):
        """Test complete payment lifecycle from initiation to completion"""
        user_id = uuid4()
        order_id = sample_payment_data["order_id"]
        
        # Step 1: Initiate payment
        initiate_request = {
            "order_id": order_id,
            "payment_method": "online"
        }
        
        initiate_response = await client.post(
            f"/payments/initiate?user_id={user_id}",
            json=initiate_request
        )
        
        assert initiate_response.status_code == 200
        initiate_data = initiate_response.json()
        payment_id = initiate_data["payment_id"]
        confirmation_url = initiate_data["confirmation_url"]
        
        # Verify payment was created with correct initial state
        status_response = await client.get(f"/payments/{payment_id}/status")
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["status"] == "pending"
        assert status_data["order_id"] == order_id
        assert status_data["payment_method"] == "online"
        
        # Step 2: Simulate payment confirmation (webhook)
        webhook_response = await client.post(
            "/payments/webhook/yandex",
            json={"payment_id": payment_id}
        )
        
        assert webhook_response.status_code == 200
        webhook_data = webhook_response.json()
        assert webhook_data["status"] == "Оплачено"
        
        # Step 3: Verify payment status after confirmation
        final_status_response = await client.get(f"/payments/{payment_id}/status")
        assert final_status_response.status_code == 200
        final_status_data = final_status_response.json()
        assert final_status_data["status"] == "success"
        
        # Step 4: Verify payment appears in user's payment history
        user_payments_response = await client.get(f"/payments/user/{user_id}")
        assert user_payments_response.status_code == 200
        user_payments_data = user_payments_response.json()
        assert len(user_payments_data["items"]) == 1
        assert user_payments_data["items"][0]["payment_id"] == payment_id
        assert user_payments_data["items"][0]["status"] == "success"

    async def test_multiple_payment_methods_workflow(self, client):
        """Test payment workflows with different payment methods"""
        user_id = uuid4()
        payment_methods = ["online", "card", "bonus", "cash"]
        payment_ids = []
        
        # Create payments with different methods
        for i, method in enumerate(payment_methods):
            order_id = f"order_{method}_{i}"
            
            # Initiate payment
            initiate_request = {
                "order_id": order_id,
                "payment_method": method
            }
            
            initiate_response = await client.post(
                f"/payments/initiate?user_id={user_id}",
                json=initiate_request
            )
            
            assert initiate_response.status_code == 200
            initiate_data = initiate_response.json()
            payment_id = initiate_data["payment_id"]
            payment_ids.append(payment_id)
            
            # Process webhook for each payment
            webhook_response = await client.post(
                "/payments/webhook/yandex",
                json={"payment_id": payment_id}
            )
            
            assert webhook_response.status_code == 200
        
        # Verify all payments are in user's history
        user_payments_response = await client.get(f"/payments/user/{user_id}")
        assert user_payments_response.status_code == 200
        user_payments_data = user_payments_response.json()
        assert len(user_payments_data["items"]) == len(payment_methods)
        
        # Verify each payment has correct method and status
        methods_found = set()
        for payment in user_payments_data["items"]:
            assert payment["status"] == "success"
            methods_found.add(payment["payment_method"])
        
        assert methods_found == set(payment_methods)

    async def test_concurrent_payment_processing(self, client):
        """Test concurrent payment processing to ensure data consistency"""
        user_id = uuid4()
        num_payments = 5
        
        # Create multiple payments concurrently
        async def create_and_process_payment(order_id):
            # Initiate payment
            initiate_request = {
                "order_id": order_id,
                "payment_method": "online"
            }
            
            initiate_response = await client.post(
                f"/payments/initiate?user_id={user_id}",
                json=initiate_request
            )
            
            assert initiate_response.status_code == 200
            payment_id = initiate_response.json()["payment_id"]
            
            # Process webhook
            webhook_response = await client.post(
                "/payments/webhook/yandex",
                json={"payment_id": payment_id}
            )
            
            assert webhook_response.status_code == 200
            return payment_id
        
        # Run concurrent payment processing
        tasks = [
            create_and_process_payment(f"concurrent_order_{i}")
            for i in range(num_payments)
        ]
        
        payment_ids = await asyncio.gather(*tasks)
        
        # Verify all payments were processed successfully
        user_payments_response = await client.get(f"/payments/user/{user_id}")
        assert user_payments_response.status_code == 200
        user_payments_data = user_payments_response.json()
        assert len(user_payments_data["items"]) == num_payments
        
        # Verify all payments have success status
        for payment in user_payments_data["items"]:
            assert payment["status"] == "success"
            assert payment["payment_method"] == "online"

    async def test_payment_failure_and_retry_workflow(self, client, sample_payment_data):
        """Test payment failure and retry scenario"""
        user_id = uuid4()
        order_id = sample_payment_data["order_id"]
        
        # Step 1: Initiate payment
        initiate_request = {
            "order_id": order_id,
            "payment_method": "online"
        }
        
        initiate_response = await client.post(
            f"/payments/initiate?user_id={user_id}",
            json=initiate_request
        )
        
        assert initiate_response.status_code == 200
        payment_id = initiate_response.json()["payment_id"]
        
        # Step 2: Verify initial status
        status_response = await client.get(f"/payments/{payment_id}/status")
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["status"] == "pending"
        
        # Step 3: Process webhook (simulate successful payment)
        webhook_response = await client.post(
            "/payments/webhook/yandex",
            json={"payment_id": payment_id}
        )
        
        assert webhook_response.status_code == 200
        
        # Step 4: Verify final status
        final_status_response = await client.get(f"/payments/{payment_id}/status")
        assert final_status_response.status_code == 200
        final_status_data = final_status_response.json()
        assert final_status_data["status"] == "success"
        
        # Step 5: Try to process webhook again (should still work)
        retry_webhook_response = await client.post(
            "/payments/webhook/yandex",
            json={"payment_id": payment_id}
        )
        
        assert retry_webhook_response.status_code == 200

    async def test_payment_data_integrity(self, client):
        """Test data integrity across payment operations"""
        user_id = uuid4()
        order_id = f"integrity_test_{uuid4()}"
        
        # Create payment
        initiate_request = {
            "order_id": order_id,
            "payment_method": "card"
        }
        
        initiate_response = await client.post(
            f"/payments/initiate?user_id={user_id}",
            json=initiate_request
        )
        
        assert initiate_response.status_code == 200
        payment_data = initiate_response.json()
        payment_id = payment_data["payment_id"]
        
        # Store initial data
        initial_status_response = await client.get(f"/payments/{payment_id}/status")
        initial_data = initial_status_response.json()
        
        # Process webhook
        await client.post(
            "/payments/webhook/yandex",
            json={"payment_id": payment_id}
        )
        
        # Verify data consistency
        final_status_response = await client.get(f"/payments/{payment_id}/status")
        final_data = final_status_response.json()
        
        # Check that core data remains unchanged
        assert final_data["payment_id"] == initial_data["payment_id"]
        assert final_data["order_id"] == initial_data["order_id"]
        assert final_data["amount"] == initial_data["amount"]
        assert final_data["payment_method"] == initial_data["payment_method"]
        assert final_data["created_at"] == initial_data["created_at"]
        
        # Check that status and updated_at changed
        assert final_data["status"] == "success"
        assert final_data["status"] != initial_data["status"]
        assert "updated_at" in final_data

    async def test_payment_pagination_workflow(self, client):
        """Test payment pagination functionality"""
        user_id = uuid4()
        total_payments = 25
        
        # Create multiple payments
        for i in range(total_payments):
            initiate_request = {
                "order_id": f"pagination_order_{i}",
                "payment_method": "online"
            }
            
            initiate_response = await client.post(
                f"/payments/initiate?user_id={user_id}",
                json=initiate_request
            )
            
            assert initiate_response.status_code == 200
            payment_id = initiate_response.json()["payment_id"]
            
            # Process webhook
            await client.post(
                "/payments/webhook/yandex",
                json={"payment_id": payment_id}
            )
        
        # Test first page
        page1_response = await client.get(f"/payments/user/{user_id}?page=1&page_size=10")
        assert page1_response.status_code == 200
        page1_data = page1_response.json()
        assert len(page1_data["items"]) == 10
        assert page1_data["page"] == 1
        assert page1_data["total_items"] == total_payments
        assert page1_data["total_pages"] == 3
        
        # Test second page
        page2_response = await client.get(f"/payments/user/{user_id}?page=2&page_size=10")
        assert page2_response.status_code == 200
        page2_data = page2_response.json()
        assert len(page2_data["items"]) == 10
        assert page2_data["page"] == 2
        
        # Test last page
        page3_response = await client.get(f"/payments/user/{user_id}?page=3&page_size=10")
        assert page3_response.status_code == 200
        page3_data = page3_response.json()
        assert len(page3_data["items"]) == 5  # Remaining items
        assert page3_data["page"] == 3

    async def test_payment_error_handling_workflow(self, client):
        """Test error handling in payment workflows"""
        user_id = uuid4()
        
        # Test invalid payment method
        invalid_method_response = await client.post(
            f"/payments/initiate?user_id={user_id}",
            json={"order_id": "test_order", "payment_method": "invalid"}
        )
        assert invalid_method_response.status_code == 422
        
        # Test missing user_id
        missing_user_response = await client.post(
            "/payments/initiate",
            json={"order_id": "test_order", "payment_method": "online"}
        )
        assert missing_user_response.status_code == 422
        
        # Test webhook with invalid payment ID
        invalid_webhook_response = await client.post(
            "/payments/webhook/yandex",
            json={"payment_id": str(uuid4())}
        )
        assert invalid_webhook_response.status_code == 404
        
        # Test status check with invalid payment ID
        invalid_status_response = await client.get(f"/payments/{uuid4()}/status")
        assert invalid_status_response.status_code == 404