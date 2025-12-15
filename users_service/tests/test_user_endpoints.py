import pytest
from uuid import uuid4

pytestmark = pytest.mark.asyncio
BASE_PATH = "/api/users"


@pytest.mark.integration
class TestUserEndpoints:

    async def test_register_user_success(self, client, sample_register_data):
        sample_register_data["email"] = f"user{uuid4()}@example.com"
        response = await client.post(f"{BASE_PATH}/register", json=sample_register_data)
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert data["email"] == sample_register_data["email"]

    async def test_login_user_success(self, client, sample_register_data):
        email = f"user{uuid4()}@example.com"
        sample_register_data["email"] = email
        sample_register_data["password"] = "testpassword123"
        await client.post(f"{BASE_PATH}/register", json=sample_register_data)

        login_resp = await client.post(f"{BASE_PATH}/login", json={"email": email, "password": "testpassword123"})
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        assert token != ""

    async def test_get_profile_success(self, client, sample_register_data):
        email = f"user{uuid4()}@example.com"
        sample_register_data["email"] = email
        sample_register_data["password"] = "testpassword123"
        await client.post(f"{BASE_PATH}/register", json=sample_register_data)
        login_resp = await client.post(f"{BASE_PATH}/login", json={"email": email, "password": "testpassword123"})
        token = login_resp.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}
        resp = await client.get(f"{BASE_PATH}/profile", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == email

    async def test_update_profile_success(self, client, sample_register_data, sample_update_profile_data):
        email = f"user{uuid4()}@example.com"
        sample_register_data["email"] = email
        sample_register_data["password"] = "testpassword123"
        await client.post(f"{BASE_PATH}/register", json=sample_register_data)
        login_resp = await client.post(f"{BASE_PATH}/login", json={"email": email, "password": "testpassword123"})
        token = login_resp.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}
        resp = await client.put(f"{BASE_PATH}/profile", headers=headers, json=sample_update_profile_data)
        assert resp.status_code == 200
        data = resp.json()
        assert data["first_name"] == sample_update_profile_data["first_name"]

    async def test_get_user_by_id_success(self, client, sample_register_data):
        email = f"user{uuid4()}@example.com"
        sample_register_data["email"] = email
        sample_register_data["password"] = "testpassword123"
        reg_resp = await client.post(f"{BASE_PATH}/register", json=sample_register_data)
        user_id = reg_resp.json()["user_id"]

        resp = await client.get(f"{BASE_PATH}/{user_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == user_id
