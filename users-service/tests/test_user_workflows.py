import pytest
import asyncio


@pytest.mark.component
@pytest.mark.asyncio
class TestUserWorkflows:
    """Component tests for complete user workflows"""

    async def test_complete_user_lifecycle(self, client):
        """Test complete user lifecycle from registration to profile management"""
        # Step 1: Register a new user
        register_data = {
            "email": "testuser@example.com",
            "password": "securepassword123",
            "first_name": "Test",
            "last_name": "User",
            "phone": "+1234567890"
        }
        
        register_response = await client.post("/users/register", json=register_data)
        
        assert register_response.status_code == 200
        register_data_response = register_response.json()
        user_id = register_data_response["user_id"]
        
        # Verify registration data
        assert register_data_response["email"] == register_data["email"]
        assert register_data_response["first_name"] == register_data["first_name"]
        assert register_data_response["last_name"] == register_data["last_name"]
        assert register_data_response["phone"] == register_data["phone"]
        assert "created_at" in register_data_response
        assert register_data_response["updated_at"] is None
        assert "password_hash" not in register_data_response
        
        # Step 2: Login with the registered user
        login_data = {
            "email": register_data["email"],
            "password": register_data["password"]
        }
        
        login_response = await client.post("/users/login", json=login_data)
        
        assert login_response.status_code == 200
        login_data_response = login_response.json()
        assert "access_token" in login_data_response
        assert "refresh_token" in login_data_response
        assert login_data_response["expires_in"] == 3600
        assert login_data_response["token_type"] == "Bearer"
        
        access_token = login_data_response["access_token"]
        
        # Step 3: Get user profile with token
        headers = {"Authorization": f"Bearer {access_token}"}
        profile_response = await client.get("/users/profile", headers=headers)
        
        assert profile_response.status_code == 200
        profile_data = profile_response.json()
        assert profile_data["user_id"] == user_id
        assert profile_data["email"] == register_data["email"]
        assert profile_data["first_name"] == register_data["first_name"]
        assert profile_data["last_name"] == register_data["last_name"]
        assert profile_data["phone"] == register_data["phone"]
        
        # Step 4: Update user profile
        update_data = {
            "first_name": "UpdatedFirst",
            "last_name": "UpdatedLast",
            "phone": "+0987654321"
        }
        
        update_response = await client.put("/users/profile", headers=headers, json=update_data)
        
        assert update_response.status_code == 200
        updated_data = update_response.json()
        assert updated_data["first_name"] == update_data["first_name"]
        assert updated_data["last_name"] == update_data["last_name"]
        assert updated_data["phone"] == update_data["phone"]
        assert updated_data["email"] == register_data["email"]  # Email should remain unchanged
        assert updated_data["updated_at"] is not None
        
        # Step 5: Get user by ID
        get_user_response = await client.get(f"/users/{user_id}")
        
        assert get_user_response.status_code == 200
        user_data = get_user_response.json()
        assert user_data["user_id"] == user_id
        assert user_data["first_name"] == update_data["first_name"]
        assert user_data["last_name"] == update_data["last_name"]
        assert user_data["phone"] == update_data["phone"]

    async def test_user_registration_duplicate_prevention(self, client):
        """Test that duplicate email registration is prevented"""
        register_data = {
            "email": "duplicate@example.com",
            "password": "password123",
            "first_name": "Duplicate",
            "last_name": "Test",
            "phone": "+1111111111"
        }
        
        # First registration should succeed
        first_response = await client.post("/users/register", json=register_data)
        assert first_response.status_code == 200
        
        # Second registration with same email should fail
        second_response = await client.post("/users/register", json=register_data)
        assert second_response.status_code == 400
        assert "already exists" in second_response.json()["detail"]
        
        # Verify only one user was created by trying to login
        login_data = {
            "email": register_data["email"],
            "password": register_data["password"]
        }
        
        login_response = await client.post("/users/login", json=login_data)
        assert login_response.status_code == 200

    async def test_user_login_security(self, client):
        """Test login security - wrong credentials should not reveal user existence"""
        # Register a user
        register_data = {
            "email": "securitytest@example.com",
            "password": "correctpassword",
            "first_name": "Security",
            "last_name": "Test",
            "phone": "+2222222222"
        }
        
        register_response = await client.post("/users/register", json=register_data)
        assert register_response.status_code == 200
        
        # Test login with wrong password
        wrong_password_data = {
            "email": register_data["email"],
            "password": "wrongpassword"
        }
        
        wrong_password_response = await client.post("/users/login", json=wrong_password_data)
        assert wrong_password_response.status_code == 401
        assert "Invalid email or password" in wrong_password_response.json()["detail"]
        
        # Test login with non-existent email
        nonexistent_email_data = {
            "email": "nonexistent@example.com",
            "password": "anypassword"
        }
        
        nonexistent_response = await client.post("/users/login", json=nonexistent_email_data)
        assert nonexistent_response.status_code == 401
        assert "Invalid email or password" in nonexistent_response.json()["detail"]
        
        # Both should return the same error message (security best practice)
        assert wrong_password_response.json()["detail"] == nonexistent_response.json()["detail"]

    async def test_concurrent_user_registration(self, client):
        """Test concurrent user registration to ensure data consistency"""
        num_concurrent = 5
        base_email = "concurrent"
        
        async def register_user(i):
            register_data = {
                "email": f"{base_email}{i}@example.com",
                "password": f"password{i}",
                "first_name": f"Concurrent{i}",
                "last_name": f"Test{i}",
                "phone": f"+333333333{i}"
            }
            
            response = await client.post("/users/register", json=register_data)
            return response
        
        # Run concurrent registrations
        tasks = [register_user(i) for i in range(num_concurrent)]
        responses = await asyncio.gather(*tasks)
        
        # Verify all registrations succeeded
        successful_registrations = 0
        for response in responses:
            if response.status_code == 200:
                successful_registrations += 1
        
        assert successful_registrations == num_concurrent
        
        # Verify all users can login
        for i in range(num_concurrent):
            login_data = {
                "email": f"{base_email}{i}@example.com",
                "password": f"password{i}"
            }
            
            login_response = await client.post("/users/login", json=login_data)
            assert login_response.status_code == 200

    async def test_user_profile_permissions(self, client):
        """Test that users can only access their own profile"""
        # Register two users
        user1_data = {
            "email": "user1@example.com",
            "password": "password1",
            "first_name": "User",
            "last_name": "One",
            "phone": "+4444444441"
        }
        
        user2_data = {
            "email": "user2@example.com",
            "password": "password2",
            "first_name": "User",
            "last_name": "Two",
            "phone": "+4444444442"
        }
        
        # Register both users
        user1_register_response = await client.post("/users/register", json=user1_data)
        assert user1_register_response.status_code == 200
        user1_id = user1_register_response.json()["user_id"]
        
        user2_register_response = await client.post("/users/register", json=user2_data)
        assert user2_register_response.status_code == 200
        user2_id = user2_register_response.json()["user_id"]
        
        # Login as user1
        user1_login_data = {
            "email": user1_data["email"],
            "password": user1_data["password"]
        }
        
        user1_login_response = await client.post("/users/login", json=user1_login_data)
        assert user1_login_response.status_code == 200
        user1_token = user1_login_response.json()["access_token"]
        
        # Login as user2
        user2_login_data = {
            "email": user2_data["email"],
            "password": user2_data["password"]
        }
        
        user2_login_response = await client.post("/users/login", json=user2_login_data)
        assert user2_login_response.status_code == 200
        user2_token = user2_login_response.json()["access_token"]
        
        # Each user should only be able to access their own profile
        user1_headers = {"Authorization": f"Bearer {user1_token}"}
        user1_profile_response = await client.get("/users/profile", headers=user1_headers)
        assert user1_profile_response.status_code == 200
        assert user1_profile_response.json()["user_id"] == user1_id
        
        user2_headers = {"Authorization": f"Bearer {user2_token}"}
        user2_profile_response = await client.get("/users/profile", headers=user2_headers)
        assert user2_profile_response.status_code == 200
        assert user2_profile_response.json()["user_id"] == user2_id
        
        # Users should be able to get each other's public profiles by ID
        user1_get_user2_response = await client.get(f"/users/{user2_id}")
        assert user1_get_user2_response.status_code == 200
        assert user1_get_user2_response.json()["user_id"] == user2_id
        
        user2_get_user1_response = await client.get(f"/users/{user1_id}")
        assert user2_get_user1_response.status_code == 200
        assert user2_get_user1_response.json()["user_id"] == user1_id

    async def test_user_data_validation_workflow(self, client):
        """Test comprehensive user data validation"""
        # Test email validation
        invalid_email_data = {
            "email": "invalid-email-format",
            "password": "password123",
            "first_name": "Test",
            "last_name": "User",
            "phone": "+5555555555"
        }
        
        invalid_email_response = await client.post("/users/register", json=invalid_email_data)
        assert invalid_email_response.status_code == 422
        
        # Test password length validation
        short_password_data = {
            "email": "test@example.com",
            "password": "123",  # Too short
            "first_name": "Test",
            "last_name": "User",
            "phone": "+5555555555"
        }
        
        short_password_response = await client.post("/users/register", json=short_password_data)
        assert short_password_response.status_code == 422
        
        # Test name validation
        empty_name_data = {
            "email": "test@example.com",
            "password": "password123",
            "first_name": "",  # Empty
            "last_name": "User",
            "phone": "+5555555555"
        }
        
        empty_name_response = await client.post("/users/register", json=empty_name_data)
        assert empty_name_response.status_code == 422
        
        # Test phone validation
        short_phone_data = {
            "email": "test@example.com",
            "password": "password123",
            "first_name": "Test",
            "last_name": "User",
            "phone": "123"  # Too short
        }
        
        short_phone_response = await client.post("/users/register", json=short_phone_data)
        assert short_phone_response.status_code == 422

    async def test_user_authentication_workflow(self, client):
        """Test user authentication token workflow"""
        # Register a user
        register_data = {
            "email": "authtest@example.com",
            "password": "authpassword123",
            "first_name": "Auth",
            "last_name": "Test",
            "phone": "+6666666666"
        }
        
        register_response = await client.post("/users/register", json=register_data)
        assert register_response.status_code == 200
        
        # Login to get token
        login_data = {
            "email": register_data["email"],
            "password": register_data["password"]
        }
        
        login_response = await client.post("/users/login", json=login_data)
        assert login_response.status_code == 200
        
        login_response_data = login_response.json()
        access_token = login_response_data["access_token"]
        refresh_token = login_response_data["refresh_token"]
        
        # Verify token format
        assert access_token != ""
        assert refresh_token != ""
        assert login_response_data["expires_in"] == 3600
        assert login_response_data["token_type"] == "Bearer"
        assert access_token != refresh_token
        
        # Test accessing protected endpoint with token
        headers = {"Authorization": f"Bearer {access_token}"}
        profile_response = await client.get("/users/profile", headers=headers)
        assert profile_response.status_code == 200
        
        # Test accessing protected endpoint without token
        no_token_response = await client.get("/users/profile")
        assert no_token_response.status_code == 403
        
        # Test accessing protected endpoint with invalid token
        invalid_token_headers = {"Authorization": "Bearer invalid_token_format"}
        invalid_token_response = await client.get("/users/profile", headers=invalid_token_headers)
        assert invalid_token_response.status_code == 401