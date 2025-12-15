from uuid import UUID, uuid4
from datetime import datetime, timedelta
import hashlib
import os
from fastapi import Depends
from jose import jwt, JWTError, ExpiredSignatureError
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.user import (
    User, RegisterRequest, LoginRequest, UpdateProfileRequest,
    LoginResponse, UserProfileResponse
)
from ..repositories.db_user_repo import UserRepo


class UserService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
        self.user_repo = UserRepo(db=self.db)
        self.jwt_secret = os.getenv("JWT_SECRET", "fallback-secret-key")
        self.jwt_algorithm = "HS256"

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self._hash_password(plain_password) == hashed_password

    def _generate_token(self, user_id: UUID) -> dict:
        payload = {
            "user_id": str(user_id),
            "exp": datetime.utcnow() + timedelta(hours=24)
        }
        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        return {
            "access_token": token,
            "refresh_token": f"refresh_{token}",
            "expires_in": 3600,
            "token_type": "Bearer"
        }

    def register_user(self, request: RegisterRequest) -> User:
        if self.user_repo.get_user_by_email(request.email):
            raise ValueError("User with this email already exists")

        user = User(
            user_id=uuid4(),
            email=request.email,
            password_hash=self._hash_password(request.password),
            first_name=request.first_name,
            last_name=request.last_name,
            phone=request.phone,
            created_at=datetime.utcnow(),
            updated_at=None
        )
        return self.user_repo.create_user(user)

    def login_user(self, request: LoginRequest) -> LoginResponse:
        user = self.user_repo.get_user_by_email(request.email)
        if not user or not self._verify_password(request.password, user.password_hash):
            raise ValueError("Invalid email or password")

        token_data = self._generate_token(user.user_id)
        return LoginResponse(**token_data)

    def update_profile(self, user_id: UUID, request: UpdateProfileRequest) -> User:
        user = self.user_repo.get_user_by_id(user_id)
        user.first_name = request.first_name
        user.last_name = request.last_name
        user.phone = request.phone
        user.updated_at = datetime.utcnow()
        return self.user_repo.update_user(user)

    def get_user_profile(self, user_id: UUID) -> UserProfileResponse:
        user = self.user_repo.get_user_by_id(user_id)
        return UserProfileResponse(**user.dict())

    def verify_token(self, token: str) -> UUID:
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return UUID(payload["user_id"])
        except ExpiredSignatureError:
            raise ValueError("Token expired")
        except JWTError:
            raise ValueError("Invalid token!")
