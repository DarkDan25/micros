from uuid import uuid4

import pytest
import asyncio

@pytest.mark.component
@pytest.mark.asyncio
class TestUserWorkflows:
    """Component tests for complete user workflows"""

    BASE_PATH = "/api/users"

    async def test_complete_user_lifecycle(self, client):
        register_data = {
            "email": "testuser@example.com",
            "password": "securepassword123",
            "first_name": "Test",
            "last_name": "User",
            "phone": "+1234567890"
        }
        # Регистрация
        register_response = await client.post(f"{self.BASE_PATH}/register", json=register_data)
        assert register_response.status_code == 200
        user_id = register_response.json()["user_id"]

        # Логин
        login_response = await client.post(f"{self.BASE_PATH}/login", json={
            "email": register_data["email"], "password": register_data["password"]
        })
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]

        headers = {"Authorization": f"Bearer {access_token}"}

        # Получение профиля
        profile_response = await client.get(f"{self.BASE_PATH}/profile", headers=headers)
        assert profile_response.status_code == 200
        assert profile_response.json()["user_id"] == user_id

        # Обновление профиля
        update_data = {"first_name": "UpdatedFirst", "last_name": "UpdatedLast", "phone": "+0987654321"}
        update_response = await client.put(f"{self.BASE_PATH}/profile", headers=headers, json=update_data)
        assert update_response.status_code == 200
        updated_data = update_response.json()
        assert updated_data["first_name"] == update_data["first_name"]

        # Получение пользователя по ID
        get_user_response = await client.get(f"{self.BASE_PATH}/{user_id}")
        assert get_user_response.status_code == 200
        assert get_user_response.json()["user_id"] == user_id

    async def test_user_registration_duplicate_prevention(self, client):
        email = f"dup{uuid4()}@example.com"
        register_data = {
            "email": email, "password": "password123",
            "first_name": "Duplicate", "last_name": "Test", "phone": "+1111111111"
        }

        first_response = await client.post(f"{self.BASE_PATH}/register", json=register_data)
        assert first_response.status_code == 200

        second_response = await client.post(f"{self.BASE_PATH}/register", json=register_data)
        assert second_response.status_code == 400
        assert "already exists" in second_response.json()["detail"]

    async def test_user_login_security(self, client):
        email = f"security{uuid4()}@example.com"
        register_data = {
            "email": email, "password": "correctpassword",
            "first_name": "Security", "last_name": "Test", "phone": "+2222222222"
        }
        await client.post(f"{self.BASE_PATH}/register", json=register_data)

        wrong_password_response = await client.post(f"{self.BASE_PATH}/login", json={
            "email": email, "password": "wrongpassword"
        })
        nonexistent_response = await client.post(f"{self.BASE_PATH}/login", json={
            "email": "nonexistent@example.com", "password": "anypassword"
        })

        assert wrong_password_response.status_code == 401
        assert nonexistent_response.status_code == 401
        assert wrong_password_response.json()["detail"] == nonexistent_response.json()["detail"]

    async def test_concurrent_user_registration(self, client):
        num_concurrent = 5
        base_email = f"concurrent{uuid4()}"

        async def register_user(i):
            data = {
                "email": f"{base_email}{i}@example.com",
                "password": f"password{i}",
                "first_name": f"Concurrent{i}",
                "last_name": f"Test{i}",
                "phone": f"+333333333{i}"
            }
            return await client.post(f"{self.BASE_PATH}/register", json=data)

        responses = await asyncio.gather(*[register_user(i) for i in range(num_concurrent)])
        successful = sum(1 for r in responses if r.status_code == 200)
        assert successful == num_concurrent

    async def test_user_profile_permissions(self, client):
        user1_email = f"user1{uuid4()}@example.com"
        user2_email = f"user2{uuid4()}@example.com"

        user1_data = {"email": user1_email, "password": "password1", "first_name": "User", "last_name": "One", "phone": "+4444444441"}
        user2_data = {"email": user2_email, "password": "password2", "first_name": "User", "last_name": "Two", "phone": "+4444444442"}

        user1_id = (await client.post(f"{self.BASE_PATH}/register", json=user1_data)).json()["user_id"]
        user2_id = (await client.post(f"{self.BASE_PATH}/register", json=user2_data)).json()["user_id"]

        user1_token = (await client.post(f"{self.BASE_PATH}/login", json={"email": user1_email, "password": "password1"})).json()["access_token"]
        user2_token = (await client.post(f"{self.BASE_PATH}/login", json={"email": user2_email, "password": "password2"})).json()["access_token"]

        headers1 = {"Authorization": f"Bearer {user1_token}"}
        headers2 = {"Authorization": f"Bearer {user2_token}"}

        resp1 = await client.get(f"{self.BASE_PATH}/profile", headers=headers1)
        resp2 = await client.get(f"{self.BASE_PATH}/profile", headers=headers2)

        assert resp1.json()["user_id"] == user1_id
        assert resp2.json()["user_id"] == user2_id

    async def test_user_data_validation_workflow(self, client):
        invalid_data = [
            {"email": "invalid", "password": "123456", "first_name": "A", "last_name": "B", "phone": "+123"},
            {"email": "test@example.com", "password": "123", "first_name": "A", "last_name": "B", "phone": "+123456"},
            {"email": "test@example.com", "password": "123456", "first_name": "", "last_name": "B", "phone": "+123456"},
        ]
        for data in invalid_data:
            response = await client.post(f"{self.BASE_PATH}/register", json=data)
            assert response.status_code == 422

    async def test_user_authentication_workflow(self, client):
        email = f"auth{uuid4()}@example.com"
        register_data = {
            "email": email, "password": "authpassword123",
            "first_name": "Auth", "last_name": "Test", "phone": "+6666666666"
        }
        await client.post(f"{self.BASE_PATH}/register", json=register_data)
        login_resp = await client.post(f"{self.BASE_PATH}/login", json={"email": email, "password": "authpassword123"})
        token_data = login_resp.json()
        access_token = token_data["access_token"]

        headers = {"Authorization": f"Bearer {access_token}"}
        resp = await client.get(f"{self.BASE_PATH}/profile", headers=headers)
        assert resp.status_code == 200

        no_token_resp = await client.get(f"{self.BASE_PATH}/profile")
        assert no_token_resp.status_code == 403

        invalid_headers = {"Authorization": "Bearer invalid_token"}
        invalid_resp = await client.get(f"{self.BASE_PATH}/profile", headers=invalid_headers)
        assert invalid_resp.status_code == 401
