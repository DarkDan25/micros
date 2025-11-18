from sqlalchemy import Column, String, DateTime, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from ..database import Base
from ..models.notification import NotificationType


class Notification(Base):
    __tablename__ = 'notifications'

    notification_id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    type = Column(Enum(NotificationType), nullable=False)
    message = Column(String, nullable=False)
    data = Column(JSON, nullable=False)
    sent_at = Column(DateTime, nullable=False)
    status = Column(String, nullable=False, default="sent")