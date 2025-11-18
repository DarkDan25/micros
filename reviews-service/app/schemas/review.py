from sqlalchemy import Column, String, DateTime, Enum, Integer
from sqlalchemy.dialects.postgresql import UUID
from ..database import Base
from ..models.review import ReviewStatus


class Review(Base):
    __tablename__ = 'reviews'

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    target_id = Column(String, nullable=False)
    rating = Column(Integer, nullable=False)
    text = Column(String, nullable=False)
    status = Column(Enum(ReviewStatus), nullable=False, default=ReviewStatus.ACTIVE)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)