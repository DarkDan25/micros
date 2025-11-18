import pytest
from uuid import uuid4
from app.models.bonus import BonusReason


@pytest.mark.integration
class TestBonusEndpoints:
    
    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "service": "bonuses"}
    
    def test_earn_bonus_endpoint(self, client):
        user_id = str(uuid4())
        bonus_data = {
            "user_id": user_id,
            "amount": 100,
            "reason": "purchase",
            "description": "Test bonus",
            "external_operation_id": "ext_123"
        }
        
        response = client.post("/api/bonuses/earn", json=bonus_data)
        assert response.status_code == 200
        data = response.json()
        assert data["delta"] == 100
        assert data["balance_after"] == 100
        assert data["user_id"] == user_id
    
    def test_apply_bonus_endpoint(self, client):
        user_id = str(uuid4())
        
        # First earn some bonuses
        earn_data = {
            "user_id": user_id,
            "amount": 200,
            "reason": "purchase",
            "description": "Earn bonus",
            "external_operation_id": "ext_earn"
        }
        client.post("/api/bonuses/earn", json=earn_data)
        
        # Then apply bonus
        apply_data = {
            "user_id": user_id,
            "amount": 50,
            "reason": "order_payment",
            "description": "Apply bonus",
            "external_operation_id": "ext_apply"
        }
        response = client.post("/api/bonuses/apply", json=apply_data)
        assert response.status_code == 200
        data = response.json()
        assert data["delta"] == -50
        assert data["balance_after"] == 150
    
    def test_apply_bonus_insufficient_funds(self, client):
        user_id = str(uuid4())
        apply_data = {
            "user_id": user_id,
            "amount": 100,
            "reason": "order_payment",
            "description": "Apply bonus",
            "external_operation_id": "ext_apply"
        }
        response = client.post("/api/bonuses/apply", json=apply_data)
        assert response.status_code == 400
        assert "Insufficient bonus balance" in response.text
    
    def test_adjust_balance_endpoint(self, client):
        user_id = str(uuid4())
        adjust_data = {
            "user_id": user_id,
            "delta": 75,
            "reason": "support_adjustment",
            "description": "Support adjustment",
            "external_operation_id": "ext_adjust"
        }
        response = client.post("/api/bonuses/adjust", json=adjust_data)
        assert response.status_code == 200
        data = response.json()
        assert data["delta"] == 75
        assert data["balance_after"] == 75
    
    def test_adjust_balance_negative_result(self, client):
        user_id = str(uuid4())
        adjust_data = {
            "user_id": user_id,
            "delta": -100,
            "reason": "support_adjustment",
            "description": "Support adjustment",
            "external_operation_id": "ext_adjust"
        }
        response = client.post("/api/bonuses/adjust", json=adjust_data)
        assert response.status_code == 400
        assert "Balance cannot be negative" in response.text
    
    def test_get_balance_endpoint(self, client):
        user_id = str(uuid4())
        
        # Earn some bonuses first
        earn_data = {
            "user_id": user_id,
            "amount": 150,
            "reason": "purchase",
            "description": "Earn bonus",
            "external_operation_id": "ext_earn"
        }
        client.post("/api/bonuses/earn", json=earn_data)
        
        # Get balance
        response = client.get(f"/api/bonuses/balance/{user_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == user_id
        assert data["balance"] == 150
        assert "updated_at" in data
    
    def test_get_history_endpoint(self, client):
        user_id = str(uuid4())
        
        # Create multiple operations
        operations = [
            {"amount": 100, "reason": "purchase", "ext_id": "ext_1"},
            {"amount": 50, "reason": "referral", "ext_id": "ext_2"},
            {"amount": 25, "reason": "order_payment", "ext_id": "ext_3"}
        ]
        
        for op in operations:
            if op["reason"] == "order_payment":
                # First earn some bonuses
                earn_data = {
                    "user_id": user_id,
                    "amount": 200,
                    "reason": "purchase",
                    "description": "Earn bonus",
                    "external_operation_id": f"earn_{op['ext_id']}"
                }
                client.post("/api/bonuses/earn", json=earn_data)
                
                # Then apply bonus
                apply_data = {
                    "user_id": user_id,
                    "amount": op["amount"],
                    "reason": op["reason"],
                    "description": "Apply bonus",
                    "external_operation_id": op["ext_id"]
                }
                client.post("/api/bonuses/apply", json=apply_data)
            else:
                earn_data = {
                    "user_id": user_id,
                    "amount": op["amount"],
                    "reason": op["reason"],
                    "description": "Earn bonus",
                    "external_operation_id": op["ext_id"]
                }
                client.post("/api/bonuses/earn", json=earn_data)
        
        # Get history
        response = client.get(f"/api/bonuses/history/{user_id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) > 0
        assert data["page"] == 1
        assert data["total_items"] > 0
    
    def test_invalid_user_id_format(self, client):
        response = client.get("/api/bonuses/balance/invalid-uuid")
        assert response.status_code == 422  # Validation error
    
    def test_missing_required_fields(self, client):
        bonus_data = {
            "amount": 100,
            "reason": "purchase",
            "description": "Test bonus"
            # Missing user_id and external_operation_id
        }
        response = client.post("/api/bonuses/earn", json=bonus_data)
        assert response.status_code == 422