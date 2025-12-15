import pytest
from uuid import uuid4


@pytest.mark.integration
class TestNotificationEndpoints:
    
    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "service": "notifications"}
    
    def test_send_receipt(self, client):
        receipt_data = {
            "order_id": "order_12345",
            "user_id": "550e8400-e29b-41d4-a716-446655440000"
        }
        response = client.post("/api/notifications/receipt", json=receipt_data)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "Чек отправлен"
        assert "notification_id" in data
    
    def test_trigger_session_reminder(self, client):
        trigger_data = {
            "type": "session_reminder",
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "data": {"movie_title": "Avatar 2", "session_time": "2024-01-01T18:00:00"}
        }
        response = client.post("/api/notifications/trigger", json=trigger_data)
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "session_reminder"
        assert data["user_id"] == "550e8400-e29b-41d4-a716-446655440000"
        assert "movie_title" in data["data"]
    
    def test_trigger_payment_success(self, client):
        trigger_data = {
            "type": "payment_success",
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "data": {"amount": 1500, "order_id": "order_12345"}
        }
        response = client.post("/api/notifications/trigger", json=trigger_data)
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "payment_success"
        assert data["user_id"] == "550e8400-e29b-41d4-a716-446655440000"
        assert data["data"]["amount"] == 1500
    
    def test_trigger_bonus_earned(self, client):
        trigger_data = {
            "type": "bonus_earned",
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "data": {"bonus_amount": 100, "reason": "purchase"}
        }
        response = client.post("/api/notifications/trigger", json=trigger_data)
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "bonus_earned"
        assert data["data"]["bonus_amount"] == 100
    
    def test_trigger_welcome(self, client):
        trigger_data = {
            "type": "welcome",
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "data": {"user_name": "John Doe"}
        }
        response = client.post("/api/notifications/trigger", json=trigger_data)
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "welcome"
        assert data["user_id"] == "550e8400-e29b-41d4-a716-446655440000"
    
    def test_trigger_order_confirmed(self, client):
        trigger_data = {
            "type": "order_confirmed",
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "data": {"order_id": "order_12345", "movie_title": "Avatar 2"}
        }
        response = client.post("/api/notifications/trigger", json=trigger_data)
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "order_confirmed"
        assert data["data"]["order_id"] == "order_12345"
    
    def test_get_user_notifications(self, client):
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        
        # First create some notifications
        notifications = [
            {
                "type": "session_reminder",
                "user_id": user_id,
                "data": {"movie_title": "Avatar 2"}
            },
            {
                "type": "payment_success",
                "user_id": user_id,
                "data": {"amount": 1500}
            }
        ]
        
        for notification in notifications:
            client.post("/api/notifications/trigger", json=notification)
        
        # Get user notifications
        response = client.get(f"/api/notifications/user/{user_id}")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total_items" in data
        assert "page" in data
        assert len(data["items"]) > 0
    
    def test_get_user_notifications_with_pagination(self, client):
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        
        # Create multiple notifications
        for i in range(5):
            notification_data = {
                "type": "session_reminder",
                "user_id": user_id,
                "data": {"movie_title": f"Movie {i}"}
            }
            client.post("/api/notifications/trigger", json=notification_data)
        
        # Get notifications with pagination
        response = client.get(f"/api/notifications/user/{user_id}?page=1&page_size=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 2
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["total_items"] >= 5
    
    def test_invalid_user_id_format(self, client):
        response = client.get("/api/notifications/user/invalid-uuid")
        assert response.status_code == 422  # Validation error
    
    def test_invalid_notification_type(self, client):
        trigger_data = {
            "type": "invalid_type",
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "data": {}
        }
        response = client.post("/api/notifications/trigger", json=trigger_data)
        assert response.status_code == 422  # Validation error
    
    def test_missing_required_fields_in_receipt(self, client):
        receipt_data = {
            "order_id": "order_12345"
            # Missing user_id
        }
        response = client.post("/api/notifications/receipt", json=receipt_data)
        assert response.status_code == 422
    
    def test_missing_required_fields_in_trigger(self, client):
        trigger_data = {
            "type": "session_reminder",
            "data": {"movie_title": "Avatar 2"}
            # Missing user_id
        }
        response = client.post("/api/notifications/trigger", json=trigger_data)
        assert response.status_code == 422
    
    def test_empty_user_notifications(self, client):
        # Use a user ID that hasn't received any notifications
        new_user_id = "880e8400-e29b-41d4-a716-446655440003"
        response = client.get(f"/api/notifications/user/{new_user_id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 0
        assert data["total_items"] == 0
        assert data["page"] == 1