import pytest
import hashlib
from uuid import uuid4
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from ..app.users_service.app.services.user_service import UserService
from ..app.users_service.app.models.user import User, RegisterRequest, LoginRequest, UpdateProfileRequest


@pytest.fixture
def user_service():
    return UserService()


@pytest.fixture
def mock_user_repo():
    return Mock()


@pytest.fixture
def sample_user():
    return User(
        user_id=uuid4(),
        email="test@example.com",
        password_hash=hashlib.sha256("password123".encode()).hexdigest(),
        first_name="John",
        last_name="Doe",
        phone="+1234567890",
        created_at=datetime.now(),
        updated_at=None
    )


@pytest.fixture
def sample_register_request():
    return RegisterRequest(
        email="newuser@example.com",
        password="securepassword123",
        first_name="Jane",
        last_name="Smith",
        phone="+0987654321"
    )


@pytest.fixture
def sample_login_request():
    return LoginRequest(
        email="test@example.com",
        password="password123"
    )


class TestUserServiceUnit:
    """Unit tests for UserService"""

    @pytest.mark.unit
    def test_hash_password(self, user_service):
        """Test password hashing"""
        password = "testpassword123"
        hashed = user_service._hash_password(password)
        
        assert isinstance(hashed, str)
        assert len(hashed) == 64  # SHA256 produces 64 character hex string
        assert hashed == hashlib.sha256(password.encode()).hexdigest()

    @pytest.mark.unit
    def test_verify_password_success(self, user_service):
        """Test successful password verification"""
        password = "testpassword123"
        hashed = user_service._hash_password(password)
        
        result = user_service._verify_password(password, hashed)
        assert result is True

    @pytest.mark.unit
    def test_verify_password_failure(self, user_service):
        """Test failed password verification"""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = user_service._hash_password(password)
        
        result = user_service._verify_password(wrong_password, hashed)
        assert result is False

    @pytest.mark.unit
    def test_register_user_success(self, user_service, sample_register_request):
        """Test successful user registration"""
        # Mock the repository
        user_service.user_repo.get_user_by_email = Mock(return_value=None)
        user_service.user_repo.create_user = Mock()
        
        # Act
        result = user_service.register_user(sample_register_request)
        
        # Assert
        assert result.email == sample_register_request.email
        assert result.first_name == sample_register_request.first_name
        assert result.last_name == sample_register_request.last_name
        assert result.phone == sample_register_request.phone
        assert result.user_id is not None
        assert result.created_at is not None
        assert result.updated_at is None
        
        # Verify password was hashed
        expected_hash = user_service._hash_password(sample_register_request.password)
        assert result.password_hash == expected_hash
        
        user_service.user_repo.get_user_by_email.assert_called_once_with(sample_register_request.email)
        user_service.user_repo.create_user.assert_called_once()

    @pytest.mark.unit
    def test_register_user_email_already_exists(self, user_service, sample_register_request):
        """Test registration with existing email"""
        # Mock existing user
        existing_user = User(
            user_id=uuid4(),
            email=sample_register_request.email,
            password_hash="existing_hash",
            first_name="Existing",
            last_name="User",
            phone="+0000000000",
            created_at=datetime.now(),
            updated_at=None
        )
        
        user_service.user_repo.get_user_by_email = Mock(return_value=existing_user)
        
        # Act & Assert
        with pytest.raises(ValueError, match="User with this email already exists"):
            user_service.register_user(sample_register_request)
        
        user_service.user_repo.get_user_by_email.assert_called_once_with(sample_register_request.email)
        user_service.user_repo.create_user.assert_not_called()

    @pytest.mark.unit
    def test_login_user_success(self, user_service, sample_user, sample_login_request):
        """Test successful user login"""
        # Mock the repository
        user_service.user_repo.get_user_by_email = Mock(return_value=sample_user)
        
        # Mock JWT generation
        with patch('users_service.app.services.user_service.jwt.encode') as mock_jwt_encode:
            mock_jwt_encode.return_value = "mocked_jwt_token"
            
            # Act
            result = user_service.login_user(sample_login_request)
            
            # Assert
            assert result.access_token == "mocked_jwt_token"
            assert result.refresh_token == "refresh_mocked_jwt_token"
            assert result.expires_in == 3600
            assert result.token_type == "Bearer"
            
            user_service.user_repo.get_user_by_email.assert_called_once_with(sample_login_request.email)
            mock_jwt_encode.assert_called_once()

    @pytest.mark.unit
    def test_login_user_invalid_email(self, user_service, sample_login_request):
        """Test login with invalid email"""
        # Mock no user found
        user_service.user_repo.get_user_by_email = Mock(return_value=None)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid email or password"):
            user_service.login_user(sample_login_request)
        
        user_service.user_repo.get_user_by_email.assert_called_once_with(sample_login_request.email)

    @pytest.mark.unit
    def test_login_user_invalid_password(self, user_service, sample_user, sample_login_request):
        """Test login with invalid password"""
        # Create login request with wrong password
        wrong_login_request = LoginRequest(
            email=sample_user.email,
            password="wrongpassword"
        )
        
        user_service.user_repo.get_user_by_email = Mock(return_value=sample_user)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid email or password"):
            user_service.login_user(wrong_login_request)
        
        user_service.user_repo.get_user_by_email.assert_called_once_with(wrong_login_request.email)

    @pytest.mark.unit
    def test_update_profile_success(self, user_service, sample_user):
        """Test successful profile update"""
        # Arrange
        update_request = UpdateProfileRequest(
            first_name="UpdatedFirst",
            last_name="UpdatedLast",
            phone="+1111111111"
        )
        
        # Mock the repository
        user_service.user_repo.get_user_by_id = Mock(return_value=sample_user)
        user_service.user_repo.update_user = Mock(return_value=sample_user)
        
        # Act
        result = user_service.update_profile(sample_user.user_id, update_request)
        
        # Assert
        assert result.first_name == update_request.first_name
        assert result.last_name == update_request.last_name
        assert result.phone == update_request.phone
        assert result.updated_at is not None
        assert result.user_id == sample_user.user_id
        assert result.email == sample_user.email  # Email should remain unchanged
        
        user_service.user_repo.get_user_by_id.assert_called_once_with(sample_user.user_id)
        user_service.user_repo.update_user.assert_called_once()

    @pytest.mark.unit
    def test_update_profile_user_not_found(self, user_service):
        """Test profile update for non-existent user"""
        # Arrange
        non_existent_user_id = uuid4()
        update_request = UpdateProfileRequest(
            first_name="UpdatedFirst",
            last_name="UpdatedLast",
            phone="+1111111111"
        )
        
        # Mock the repository
        user_service.user_repo.get_user_by_id = Mock(side_effect=KeyError("User not found"))
        
        # Act & Assert
        with pytest.raises(KeyError, match="User not found"):
            user_service.update_profile(non_existent_user_id, update_request)

    @pytest.mark.unit
    def test_get_user_profile_success(self, user_service, sample_user):
        """Test successful user profile retrieval"""
        # Mock the repository
        user_service.user_repo.get_user_by_id = Mock(return_value=sample_user)
        
        # Act
        result = user_service.get_user_profile(sample_user.user_id)
        
        # Assert
        assert result.user_id == sample_user.user_id
        assert result.email == sample_user.email
        assert result.first_name == sample_user.first_name
        assert result.last_name == sample_user.last_name
        assert result.phone == sample_user.phone
        assert result.created_at == sample_user.created_at
        assert result.updated_at == sample_user.updated_at
        assert not hasattr(result, 'password_hash')  # Password should not be exposed
        
        user_service.user_repo.get_user_by_id.assert_called_once_with(sample_user.user_id)

    @pytest.mark.unit
    def test_get_user_profile_not_found(self, user_service):
        """Test user profile retrieval for non-existent user"""
        # Arrange
        non_existent_user_id = uuid4()
        
        # Mock the repository
        user_service.user_repo.get_user_by_id = Mock(side_effect=KeyError("User not found"))
        
        # Act & Assert
        with pytest.raises(KeyError, match="User not found"):
            user_service.get_user_profile(non_existent_user_id)

    @pytest.mark.unit
    def test_verify_token_success(self, user_service):
        """Test successful token verification"""
        # Arrange
        user_id = uuid4()
        token_payload = {
            "user_id": str(user_id),
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        
        # Mock JWT decode
        with patch('users_service.app.services.user_service.jwt.decode') as mock_jwt_decode:
            mock_jwt_decode.return_value = token_payload
            
            # Act
            result = user_service.verify_token("valid_token")
            
            # Assert
            assert result == user_id
            mock_jwt_decode.assert_called_once()

    @pytest.mark.unit
    def test_verify_token_expired(self, user_service):
        """Test token verification with expired token"""
        # Mock JWT decode with expired signature error
        with patch('users_service.app.services.user_service.jwt.decode') as mock_jwt_decode:
            from jose.exceptions import ExpiredSignatureError
            mock_jwt_decode.side_effect = ExpiredSignatureError("Token expired")
            
            # Act & Assert
            with pytest.raises(ValueError, match="Token expired"):
                user_service.verify_token("expired_token")

    @pytest.mark.unit
    def test_verify_token_invalid(self, user_service):
        """Test token verification with invalid token"""
        # Mock JWT decode with JWT error
        with patch('users_service.app.services.user_service.jwt.decode') as mock_jwt_decode:
            from jose.exceptions import JWTError
            mock_jwt_decode.side_effect = JWTError("Invalid token")
            
            # Act & Assert
            with pytest.raises(ValueError, match="Invalid token"):
                user_service.verify_token("invalid_token")

    @pytest.mark.unit
    def test_generate_token_structure(self, user_service):
        """Test token generation structure"""
        user_id = uuid4()
        
        with patch('users_service.app.services.user_service.jwt.encode') as mock_jwt_encode:
            mock_jwt_encode.return_value = "mocked_token"
            
            # Act
            result = user_service._generate_token(user_id)
            
            # Assert
            assert result["access_token"] == "mocked_token"
            assert result["refresh_token"] == "refresh_mocked_token"
            assert result["expires_in"] == 3600
            assert result["token_type"] == "Bearer"
            
            # Verify JWT encode was called with correct payload
            mock_jwt_encode.assert_called_once()
            call_args = mock_jwt_encode.call_args[0][0]
            assert call_args["user_id"] == str(user_id)
            assert "exp" in call_args