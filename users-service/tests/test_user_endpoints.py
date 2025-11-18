import pytest
from uuid import uuid4


@pytest.mark.integration
@pytest.mark.asyncio
class TestUserEndpoints:
    """Integration tests for user API endpoints"""

    async def test_register_user_success(self, client, sample_register_data):
        """Test successful user registration through API"""
        # Act
        response = await client.post("/users/register", json=sample_register_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert data["email"] == sample_register_data["email"]
        assert data["first_name"] == sample_register_data["first_name"]
        assert data["last_name"] == sample_register_data["last_name"]
        assert data["phone"] == sample_register_data["phone"]
        assert "created_at" in data
        assert data["updated_at"] is None
        assert "password_hash" not in data  # Password should not be exposed

    async def test_register_user_duplicate_email(self, client, sample_register_data):
        """Test registration with duplicate email"""
        # First registration should succeed
        first_response = await client.post("/users/register", json=sample_register_data)
        assert first_response.status_code == 200
        
        # Second registration with same email should fail
        second_response = await client.post("/users/register", json=sample_register_data)
        assert second_response.status_code == 400
        assert "already exists" in second_response.json()["detail"]

    async def test_register_user_invalid_data(self, client):
        """Test registration with invalid data"""
        # Test with invalid email
        invalid_email_data = {
            "email": "invalid-email",
            "password": "password123",
            "first_name": "John",
            "last_name": "Doe",
            "phone": "+1234567890"
        }
        
        response = await client.post("/users/register", json=invalid_email_data)
        assert response.status_code == 422
        
        # Test with short password
        short_password_data = {
            "email": "test@example.com",
            "password": "123",  # Too short
            "first_name": "John",
            "last_name": "Doe",
            "phone": "+1234567890"
        }
        
        response = await client.post("/users/register", json=short_password_data)
        assert response.status_code == 422
        
        # Test with missing required fields
        missing_fields_data = {
            "email": "test@example.com",
            "password": "password123"
            # Missing first_name, last_name, phone
        }
        
        response = await client.post("/users/register", json=missing_fields_data)
        assert response.status_code == 422

    async def test_login_user_success(self, client, sample_user):
        """Test successful user login"""
        # First register a user
        register_data = {
            "email": "testlogin@example.com",
            "password": "testpassword123",
            "first_name": "Test",
            "last_name": "User",
            "phone": "+1234567890"
        }
        
        register_response = await client.post("/users/register", json=register_data)
        assert register_response.status_code == 200
        
        # Now test login
        login_data = {
            "email": register_data["email"],
            "password": register_data["password"]
        }
        
        login_response = await client.post("/users/login", json=login_data)
        
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert "access_token" in login_data
        assert "refresh_token" in login_data
        assert login_data["expires_in"] == 3600
        assert login_data["token_type"] == "Bearer"
        assert login_data["access_token"] != ""
        assert login_data["refresh_token"] != ""

    async def test_login_user_invalid_credentials(self, client, sample_register_data):
        """Test login with invalid credentials"""
        # First register a user
        register_response = await client.post("/users/register", json=sample_register_data)
        assert register_response.status_code == 200
        
        # Test with wrong password
        wrong_password_data = {
            "email": sample_register_data["email"],
            "password": "wrongpassword"
        }
        
        response = await client.post("/users/login", json=wrong_password_data)
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]
        
        # Test with non-existent email
        nonexistent_email_data = {
            "email": "nonexistent@example.com",
            "password": "password123"
        }
        
        response = await client.post("/users/login", json=nonexistent_email_data)
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]

    async def test_login_user_invalid_data(self, client):
        """Test login with invalid data"""
        # Test with invalid email format
        invalid_email_data = {
            "email": "invalid-email",
            "password": "password123"
        }
        
        response = await client.post("/users/login", json=invalid_email_data)
        assert response.status_code == 422
        
        # Test with missing fields
        missing_fields_data = {
            "email": "test@example.com"
            # Missing password
        }
        
        response = await client.post("/users/login", json=missing_fields_data)
        assert response.status_code == 422

    async def test_get_profile_success(self, client, sample_register_data):
        """Test successful profile retrieval"""
        # First register and login a user
        register_response = await client.post("/users/register", json=sample_register_data)
        assert register_response.status_code == 200
        
        login_data = {
            "email": sample_register_data["email"],
            "password": sample_register_data["password"]
        }
        
        login_response = await client.post("/users/login", json=login_data)
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]
        
        # Get profile with valid token
        headers = {"Authorization": f"Bearer {access_token}"}
        profile_response = await client.get("/users/profile", headers=headers)
        
        assert profile_response.status_code == 200
        profile_data = profile_response.json()
        assert profile_data["email"] == sample_register_data["email"]
        assert profile_data["first_name"] == sample_register_data["first_name"]
        assert profile_data["last_name"] == sample_register_data["last_name"]
        assert profile_data["phone"] == sample_register_data["phone"]
        assert "user_id" in profile_data
        assert "created_at" in profile_data
        assert "updated_at" in profile_data
        assert "password_hash" not in profile_data

    async def test_get_profile_no_token(self, client):
        """Test profile retrieval without token"""
        response = await client.get("/users/profile")
        assert response.status_code == 403  # or 401 depending on implementation

    async def test_get_profile_invalid_token(self, client):
        """Test profile retrieval with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = await client.get("/users/profile", headers=headers)
        assert response.status_code == 401

    async def test_get_profile_expired_token(self, client, sample_register_data):
        """Test profile retrieval with expired token"""
        # This test would require mocking JWT expiration
        # For now, we'll test with an obviously malformed token
        headers = {"Authorization": "Bearer expired_token_format"}
        response = await client.get("/users/profile", headers=headers)
        assert response.status_code == 401

    async def test_update_profile_success(self, client, sample_register_data, sample_update_profile_data):
        """Test successful profile update"""
        # First register and login a user
        register_response = await client.post("/users/register", json=sample_register_data)
        assert register_response.status_code == 200
        
        login_data = {
            "email": sample_register_data["email"],
            "password": sample_register_data["password"]
        }
        
        login_response = await client.post("/users/login", json=login_data)
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]
        
        # Update profile with valid token
        headers = {"Authorization": f"Bearer {access_token}"}
        update_response = await client.put("/users/profile", headers=headers, json=sample_update_profile_data)
        
        assert update_response.status_code == 200
        updated_data = update_response.json()
        assert updated_data["first_name"] == sample_update_profile_data["first_name"]
        assert updated_data["last_name"] == sample_update_profile_data["last_name"]
        assert updated_data["phone"] == sample_update_profile_data["phone"]
        assert updated_data["email"] == sample_register_data["email"]  # Email should remain unchanged
        assert updated_data["updated_at"] is not None

    async def test_update_profile_no_token(self, client, sample_update_profile_data):
        """Test profile update without token"""
        response = await client.put("/users/profile", json=sample_update_profile_data)
        assert response.status_code == 403  # or 401 depending on implementation

    async def test_update_profile_invalid_data(self, client, sample_register_data):
        """Test profile update with invalid data"""
        # First register and login a user
        register_response = await client.post("/users/register", json=sample_register_data)
        assert register_response.status_code == 200
        
        login_data = {
            "email": sample_register_data["email"],
            "password": sample_register_data["password"]
        }
        
        login_response = await client.post("/users/login", json=login_data)
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]
        
        # Test with empty first name
        invalid_data = {
            "first_name": "",  # Empty
            "last_name": "UpdatedLast",
            "phone": "+1111111111"
        }
        
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await client.put("/users/profile", headers=headers, json=invalid_data)
        assert response.status_code == 422
        
        # Test with short phone number
        invalid_phone_data = {
            "first_name": "UpdatedFirst",
            "last_name": "UpdatedLast",
            "phone": "123"  # Too short
        }
        
        response = await client.put("/users/profile", headers=headers, json=invalid_phone_data)
        assert response.status_code == 422

    async def test_get_user_by_id_success(self, client, sample_register_data):
        """Test getting user by ID"""
        # First register a user
        register_response = await client.post("/users/register", json=sample_register_data)
        assert register_response.status_code == 200
        user_data = register_response.json()
        user_id = user_data["user_id"]
        
        # Get user by ID
        get_response = await client.get(f"/users/{user_id}")
        
        assert get_response.status_code == 200
        retrieved_data = get_response.json()
        assert retrieved_data["user_id"] == user_id
        assert retrieved_data["email"] == sample_register_data["email"]
        assert retrieved_data["first_name"] == sample_register_data["first_name"]
        assert retrieved_data["last_name"] == sample_register_data["last_name"]
        assert retrieved_data["phone"] == sample_register_data["phone"]
        assert "password_hash" not in retrieved_data

    async def test_get_user_by_id_not_found(self, client):
        """Test getting non-existent user by ID"""
        nonexistent_user_id = uuid4()
        response = await client.get(f"/users/{nonexistent_user_id}")
        assert response.status_code == 404

    async def test_authorization_header_formats(self, client, sample_register_data):
        """Test different authorization header formats"""
        # First register and login a user
        register_response = await client.post("/users/register", json=sample_register_data)
        assert register_response.status_code == 200
        
        login_data = {
            "email": sample_register_data["email"],
            "password": sample_register_data["password"]
        }
        
        login_response = await client.post("/users/login", json=login_data)
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]
        
        # Test with correct Bearer format
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await client.get("/users/profile", headers=headers)
        assert response.status_code == 200
        
        # Test with missing "Bearer " prefix
        invalid_headers = {"Authorization": access_token}
        response = await client.get("/users/profile", headers=invalid_headers)
        assert response.status_code == 401
        
        # Test with wrong prefix
        wrong_prefix_headers = {"Authorization": f"Token {access_token}"}
        response = await client.get("/users/profile", headers=wrong_prefix_headers)
        assert response.status_code == 401