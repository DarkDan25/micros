from sqlalchemy import Column, String, DateTime, Integer, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from ..database import Base


class Movie(Base):
    __tablename__ = 'movies'

    film_id = Column(UUID(as_uuid=True), primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    genre = Column(ARRAY(String), nullable=False)
    poster_url = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)


class Session(Base):
    __tablename__ = 'sessions'

    session_id = Column(UUID(as_uuid=True), primary_key=True)
    movie_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    start_time = Column(DateTime, nullable=False)
    hall_name = Column(String, nullable=False)
    available_seats = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)