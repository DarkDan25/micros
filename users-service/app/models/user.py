from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional


class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    email: EmailStr
    password_hash: str
    first_name: str
    last_name: str
    phone: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    phone: str = Field(min_length=10)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UpdateProfileRequest(BaseModel):
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    phone: str = Field(min_length=10)


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str


class UserProfileResponse(BaseModel):
    user_id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    phone: str
    created_at: datetime
    updated_at: Optional[datetime] = None