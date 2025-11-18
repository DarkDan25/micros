from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional


class Movie(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    film_id: UUID
    title: str
    description: str
    duration_minutes: int = Field(gt=0)
    genre: List[str]
    poster_url: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class Session(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    session_id: UUID
    movie_id: UUID
    start_time: datetime
    hall_name: str
    available_seats: int = Field(ge=0)
    created_at: datetime
    updated_at: Optional[datetime] = None


class OrderRequest(BaseModel):
    user_id: UUID
    session_id: UUID
    selected_seats: List[str]
    ticket_count: int = Field(gt=0)


class OrderResponse(BaseModel):
    order_id: UUID
    status: str
    total_amount: float


class ScheduleUpdateRequest(BaseModel):
    start_time: datetime
    hall_name: str


class MoviesListResponse(BaseModel):
    movies: List[Movie]


class ScheduleListResponse(BaseModel):
    schedule: List[Session]


class UpdateMovieRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, gt=0)
    genre: Optional[List[str]] = None
    poster_url: Optional[str] = None