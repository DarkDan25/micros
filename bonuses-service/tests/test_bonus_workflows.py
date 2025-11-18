import pytest
from uuid import uuid4


@pytest.mark.component
class TestBonusWorkflows:
    """Component tests for complete bonus system workflows"""
    
    def test_complete_bonus_lifecycle(self, client):
        """Test complete bonus lifecycle: earn -> check balance -> apply -> check history"""
        user_id = str(uuid4())
        
        # Step 1: Earn initial bonus
        earn_data = {
            "user_id": user_id,
            "amount": 200,
            "reason": "registration",
            "description": "Welcome bonus for new user",
            "external_operation_id": "welcome_bonus_001"
        }
        response = client.post("/api/bonuses/earn", json=earn_data)
        assert response.status_code == 200
        earn_response = response.json()
        assert earn_response["delta"] == 200
        assert earn_response["balance_after"] == 200
        
        # Step 2: Check balance
        response = client.get(f"/api/bonuses/balance/{user_id}")
        assert response.status_code == 200
        balance_data = response.json()
        assert balance_data["balance"] == 200
        assert balance_data["user_id"] == user_id
        
        # Step 3: Earn more bonuses
        earn_data2 = {
            "user_id": user_id,
            "amount": 150,
            "reason": "purchase",
            "description": "Purchase bonus",
            "external_operation_id": "purchase_bonus_001"
        }
        response = client.post("/api/bonuses/earn", json=earn_data2)
        assert response.status_code == 200
        earn_response2 = response.json()
        assert earn_response2["balance_after"] == 350
        
        # Step 4: Apply bonus for order payment
        apply_data = {
            "user_id": user_id,
            "amount": 75,
            "reason": "order_payment",
            "description": "Used bonus for order payment",
            "external_operation_id": "order_payment_001"
        }
        response = client.post("/api/bonuses/apply", json=apply_data)
        assert response.status_code == 200
        apply_response = response.json()
        assert apply_response["delta"] == -75
        assert apply_response["balance_after"] == 275
        
        # Step 5: Check final balance
        response = client.get(f"/api/bonuses/balance/{user_id}")
        assert response.status_code == 200
        final_balance = response.json()
        assert final_balance["balance"] == 275
        
        # Step 6: Check history
        response = client.get(f"/api/bonuses/history/{user_id}")
        assert response.status_code == 200
        history_data = response.json()
        assert len(history_data["items"]) == 3
        assert history_data["total_items"] == 3
        
        # Verify operations order and amounts
        operations = history_data["items"]
        assert operations[0]["delta"] == 200
        assert operations[1]["delta"] == 150
        assert operations[2]["delta"] == -75
    
    def test_referral_bonus_workflow(self, client):
        """Test referral bonus workflow with multiple users"""
        referrer_id = str(uuid4())
        referred_id = str(uuid4())
        
        # Step 1: Referrer earns bonus for referring
        referrer_bonus = {
            "user_id": referrer_id,
            "amount": 100,
            "reason": "referral",
            "description": "Bonus for referring a friend",
            "external_operation_id": "referral_001_referrer"
        }
        response = client.post("/api/bonuses/earn", json=referrer_bonus)
        assert response.status_code == 200
        assert response.json()["balance_after"] == 100
        
        # Step 2: Referred user earns registration bonus
        referred_bonus = {
            "user_id": referred_id,
            "amount": 50,
            "reason": "registration",
            "description": "Welcome bonus for referred user",
            "external_operation_id": "referral_001_referred"
        }
        response = client.post("/api/bonuses/earn", json=referred_bonus)
        assert response.status_code == 200
        assert response.json()["balance_after"] == 50
        
        # Step 3: Both users check their balances
        response = client.get(f"/api/bonuses/balance/{referrer_id}")
        assert response.json()["balance"] == 100
        
        response = client.get(f"/api/bonuses/balance/{referred_id}")
        assert response.json()["balance"] == 50
    
    def test_bonus_adjustment_workflow(self, client):
        """Test admin adjustment workflow"""
        user_id = str(uuid4())
        
        # Step 1: User earns some bonuses
        earn_data = {
            "user_id": user_id,
            "amount": 100,
            "reason": "purchase",
            "description": "Purchase bonus",
            "external_operation_id": "purchase_001"
        }
        client.post("/api/bonuses/earn", json=earn_data)
        
        # Step 2: Admin adjusts balance (adds bonus)
        adjust_data = {
            "user_id": user_id,
            "delta": 50,
            "reason": "support_adjustment",
            "description": "Compensation for service issue",
            "external_operation_id": "adjustment_001"
        }
        response = client.post("/api/bonuses/adjust", json=adjust_data)
        assert response.status_code == 200
        assert response.json()["balance_after"] == 150
        
        # Step 3: Admin adjusts balance (deducts bonus)
        adjust_data2 = {
            "user_id": user_id,
            "delta": -30,
            "reason": "support_adjustment",
            "description": "Correction for billing error",
            "external_operation_id": "adjustment_002"
        }
        response = client.post("/api/bonuses/adjust", json=adjust_data2)
        assert response.status_code == 200
        assert response.json()["balance_after"] == 120
        
        # Step 4: Verify final balance and history
        response = client.get(f"/api/bonuses/balance/{user_id}")
        assert response.json()["balance"] == 120
        
        response = client.get(f"/api/bonuses/history/{user_id}")
        history = response.json()
        assert len(history["items"]) == 3
        assert history["total_items"] == 3
    
    def test_concurrent_bonus_operations(self, client):
        """Test handling of concurrent bonus operations"""
        user_id = str(uuid4())
        
        # Step 1: Earn initial bonus
        earn_data = {
            "user_id": user_id,
            "amount": 500,
            "reason": "purchase",
            "description": "Large purchase bonus",
            "external_operation_id": "large_purchase_001"
        }
        response = client.post("/api/bonuses/earn", json=earn_data)
        assert response.status_code == 200
        assert response.json()["balance_after"] == 500
        
        # Step 2: Multiple apply operations (simulating concurrent order payments)
        apply_operations = []
        for i in range(3):
            apply_data = {
                "user_id": user_id,
                "amount": 100,
                "reason": "order_payment",
                "description": f"Order payment {i+1}",
                "external_operation_id": f"order_payment_00{i+1}"
            }
            response = client.post("/api/bonuses/apply", json=apply_data)
            apply_operations.append(response)
        
        # All operations should succeed
        for i, response in enumerate(apply_operations):
            assert response.status_code == 200
            expected_balance = 500 - (100 * (i + 1))
            assert response.json()["balance_after"] == expected_balance
        
        # Final balance should be 200
        response = client.get(f"/api/bonuses/balance/{user_id}")
        assert response.json()["balance"] == 200
    
    def test_bonus_expiration_workflow(self, client):
        """Test bonus expiration handling (if implemented)"""
        user_id = str(uuid4())
        
        # This test would require bonus expiration functionality
        # For now, we'll test that bonuses don't expire unexpectedly
        earn_data = {
            "user_id": user_id,
            "amount": 100,
            "reason": "purchase",
            "description": "Bonus that should not expire",
            "external_operation_id": "non_expiring_001"
        }
        response = client.post("/api/bonuses/earn", json=earn_data)
        assert response.status_code == 200
        
        # Balance should remain the same (no automatic expiration)
        response = client.get(f"/api/bonuses/balance/{user_id}")
        assert response.json()["balance"] == 100
        
        # Should be able to apply the bonus later
        apply_data = {
            "user_id": user_id,
            "amount": 50,
            "reason": "order_payment",
            "description": "Using non-expired bonus",
            "external_operation_id": "use_non_expiring_001"
        }
        response = client.post("/api/bonuses/apply", json=apply_data)
        assert response.status_code == 200
        assert response.json()["balance_after"] == 50