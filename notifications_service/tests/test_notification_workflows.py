import pytest
from uuid import uuid4


@pytest.mark.component
class TestNotificationWorkflows:
    """Component tests for complete notification system workflows"""
    
    def test_complete_user_notification_workflow(self, client):
        """Test complete user notification workflow: welcome -> booking -> payment -> receipt"""
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        
        # Step 1: Send welcome notification
        welcome_data = {
            "type": "welcome",
            "user_id": user_id,
            "data": {"user_name": "John Doe"}
        }
        response = client.post("/api/notifications/trigger", json=welcome_data)
        assert response.status_code == 200
        welcome_response = response.json()
        assert welcome_response["type"] == "welcome"
        assert welcome_response["user_id"] == user_id
        
        # Step 2: Send booking confirmation
        booking_data = {
            "type": "order_confirmed",
            "user_id": user_id,
            "data": {
                "order_id": "order_12345",
                "movie_title": "Avatar 2",
                "session_time": "2024-01-01T18:00:00",
                "seats": ["A1", "A2"]
            }
        }
        response = client.post("/api/notifications/trigger", json=booking_data)
        assert response.status_code == 200
        booking_response = response.json()
        assert booking_response["type"] == "order_confirmed"
        assert booking_response["data"]["order_id"] == "order_12345"
        
        # Step 3: Send payment success notification
        payment_data = {
            "type": "payment_success",
            "user_id": user_id,
            "data": {
                "amount": 1500,
                "order_id": "order_12345",
                "payment_method": "credit_card"
            }
        }
        response = client.post("/api/notifications/trigger", json=payment_data)
        assert response.status_code == 200
        payment_response = response.json()
        assert payment_response["type"] == "payment_success"
        assert payment_response["data"]["amount"] == 1500
        
        # Step 4: Send receipt
        receipt_data = {
            "order_id": "order_12345",
            "user_id": user_id
        }
        response = client.post("/api/notifications/receipt", json=receipt_data)
        assert response.status_code == 200
        receipt_response = response.json()
        assert receipt_response["message"] == "Чек отправлен"
        
        # Step 5: Verify all notifications in user history
        response = client.get(f"/api/notifications/user/{user_id}")
        assert response.status_code == 200
        notifications_data = response.json()
        assert notifications_data["total_items"] >= 4
        
        # Verify notification types
        notification_types = [item["type"] for item in notifications_data["items"]]
        assert "welcome" in notification_types
        assert "order_confirmed" in notification_types
        assert "payment_success" in notification_types
        assert "receipt" in notification_types
    
    def test_session_reminder_workflow(self, client):
        """Test session reminder workflow with timing"""
        user_id = "660e8400-e29b-41d4-a716-446655440001"
        
        # Step 1: Send session reminder 1 hour before
        reminder_data = {
            "type": "session_reminder",
            "user_id": user_id,
            "data": {
                "movie_title": "Inception",
                "session_time": "2024-01-01T20:00:00",
                "hall_name": "Hall 1",
                "seats": ["B3", "B4"]
            }
        }
        response = client.post("/api/notifications/trigger", json=reminder_data)
        assert response.status_code == 200
        reminder_response = response.json()
        assert reminder_response["type"] == "session_reminder"
        assert "Inception" in reminder_response["data"]["movie_title"]
        
        # Step 2: Send bonus earned notification (user gets bonus for booking)
        bonus_data = {
            "type": "bonus_earned",
            "user_id": user_id,
            "data": {
                "bonus_amount": 50,
                "reason": "early_booking",
                "total_bonus_balance": 250
            }
        }
        response = client.post("/api/notifications/trigger", json=bonus_data)
        assert response.status_code == 200
        bonus_response = response.json()
        assert bonus_response["type"] == "bonus_earned"
        assert bonus_response["data"]["bonus_amount"] == 50
        
        # Step 3: Verify user notification history
        response = client.get(f"/api/notifications/user/{user_id}")
        assert response.status_code == 200
        user_notifications = response.json()
        assert user_notifications["total_items"] >= 2
    
    def test_promotional_notification_workflow(self, client):
        """Test promotional notification workflow for multiple users"""
        user_ids = [
            "770e8400-e29b-41d4-a716-446655440002",
            "880e8400-e29b-41d4-a716-446655440003",
            "990e8400-e29b-41d4-a716-446655440004"
        ]
        
        # Send promotional notifications to multiple users
        for user_id in user_ids:
            promo_data = {
                "type": "bonus_earned",  # Using bonus_earned as promotional
                "user_id": user_id,
                "data": {
                    "bonus_amount": 100,
                    "reason": "promotional_offer",
                    "offer_code": "WELCOME100",
                    "expiry_date": "2024-02-01"
                }
            }
            response = client.post("/api/notifications/trigger", json=promo_data)
            assert response.status_code == 200
            promo_response = response.json()
            assert promo_response["type"] == "bonus_earned"
            assert promo_response["data"]["bonus_amount"] == 100
        
        # Verify each user received their notification
        for user_id in user_ids:
            response = client.get(f"/api/notifications/user/{user_id}")
            assert response.status_code == 200
            user_notifications = response.json()
            assert user_notifications["total_items"] >= 1
            
            # Find the promotional notification
            promo_notifications = [
                item for item in user_notifications["items"]
                if item["data"].get("reason") == "promotional_offer"
            ]
            assert len(promo_notifications) == 1
            assert promo_notifications[0]["data"]["bonus_amount"] == 100
    
    def test_notification_error_handling_workflow(self, client):
        """Test error handling in notification workflows"""
        
        # Test 1: Invalid user ID format
        invalid_data = {
            "type": "welcome",
            "user_id": "invalid-uuid-format",
            "data": {}
        }
        response = client.post("/api/notifications/trigger", json=invalid_data)
        assert response.status_code == 422
        
        # Test 2: Invalid notification type
        invalid_type_data = {
            "type": "invalid_notification_type",
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "data": {}
        }
        response = client.post("/api/notifications/trigger", json=invalid_type_data)
        assert response.status_code == 422
        
        # Test 3: Missing required fields in receipt
        incomplete_receipt = {
            "order_id": "order_12345"
            # Missing user_id
        }
        response = client.post("/api/notifications/receipt", json=incomplete_receipt)
        assert response.status_code == 422
        
        # Test 4: Valid notification should still work after errors
        valid_data = {
            "type": "welcome",
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "data": {"user_name": "Test User"}
        }
        response = client.post("/api/notifications/trigger", json=valid_data)
        assert response.status_code == 200
    
    def test_notification_pagination_workflow(self, client):
        """Test notification pagination and history management"""
        user_id = "aa0e8400-e29b-41d4-a716-446655440005"
        
        # Create multiple notifications
        notification_types = ["welcome", "bonus_earned", "payment_success", "order_confirmed", "session_reminder"]
        for i, notif_type in enumerate(notification_types):
            notification_data = {
                "type": notif_type,
                "user_id": user_id,
                "data": {
                    "sequence_number": i + 1,
                    "test_data": f"test_{i+1}"
                }
            }
            response = client.post("/api/notifications/trigger", json=notification_data)
            assert response.status_code == 200
        
        # Test pagination - page 1
        response = client.get(f"/api/notifications/user/{user_id}?page=1&page_size=2")
        assert response.status_code == 200
        page1_data = response.json()
        assert len(page1_data["items"]) == 2
        assert page1_data["page"] == 1
        assert page1_data["page_size"] == 2
        assert page1_data["total_items"] >= 5
        
        # Test pagination - page 2
        response = client.get(f"/api/notifications/user/{user_id}?page=2&page_size=2")
        assert response.status_code == 200
        page2_data = response.json()
        assert len(page2_data["items"]) == 2
        assert page2_data["page"] == 2
        
        # Verify different items on different pages
        page1_ids = [item["notification_id"] for item in page1_data["items"]]
        page2_ids = [item["notification_id"] for item in page2_data["items"]]
        assert not any(nid in page2_ids for nid in page1_ids)  # No overlap
    
    def test_notification_data_integrity_workflow(self, client):
        """Test data integrity and consistency in notifications"""
        user_id = "bb0e8400-e29b-41d4-a716-446655440006"
        
        # Create notification with complex data
        complex_data = {
            "type": "order_confirmed",
            "user_id": user_id,
            "data": {
                "order_id": "order_67890",
                "movie_title": "The Matrix",
                "session_time": "2024-01-15T19:30:00",
                "hall_name": "IMAX Hall",
                "seats": ["A5", "A6", "A7"],
                "total_amount": 1800,
                "currency": "RUB",
                "payment_method": "credit_card",
                "booking_time": "2024-01-10T14:20:00",
                "metadata": {
                    "promo_code": "SAVE20",
                    "discount_applied": 200,
                    "final_amount": 1600
                }
            }
        }
        
        response = client.post("/api/notifications/trigger", json=complex_data)
        assert response.status_code == 200
        
        # Retrieve and verify data integrity
        response = client.get(f"/api/notifications/user/{user_id}")
        assert response.status_code == 200
        notifications_data = response.json()
        
        # Find our complex notification
        complex_notifications = [
            item for item in notifications_data["items"]
            if item["data"].get("order_id") == "order_67890"
        ]
        
        assert len(complex_notifications) == 1
        saved_notification = complex_notifications[0]
        
        # Verify all data fields are preserved correctly
        saved_data = saved_notification["data"]
        assert saved_data["movie_title"] == "The Matrix"
        assert saved_data["total_amount"] == 1800
        assert saved_data["seats"] == ["A5", "A6", "A7"]
        assert saved_data["metadata"]["promo_code"] == "SAVE20"
        assert saved_data["metadata"]["discount_applied"] == 200