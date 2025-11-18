import enum
from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ReviewStatus(enum.Enum):
    ACTIVE = 'active'
    DELETED = 'deleted'


class Review(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    target_id: str
    rating: int
    text: str
    status: ReviewStatus
    created_at: datetime
    updated_at: Optional[datetime] = None


class CreateReviewRequest(BaseModel):
    target_id: str
    rating: int = Field(ge=1, le=10)
    text: str


class UpdateReviewRequest(BaseModel):
    rating: int = Field(ge=1, le=10)
    text: str


class ReviewResponse(BaseModel):
    id: UUID
    user_id: UUID
    target_id: str
    rating: int
    text: str
    status: ReviewStatus
    created_at: datetime
    updated_at: Optional[datetime] = None


class ReviewListResponse(BaseModel):
    items: list[ReviewResponse]
    page: int
    page_size: int
    total_items: int
    total_pages: int