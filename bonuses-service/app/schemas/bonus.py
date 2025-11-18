from sqlalchemy import Column, String, DateTime, Enum, Integer
from sqlalchemy.dialects.postgresql import UUID
from ..database import Base
from ..models.bonus import BonusReason


class BonusOperation(Base):
    __tablename__ = 'bonus_operations'

    operation_id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    delta = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)
    reason = Column(Enum(BonusReason), nullable=False)
    description = Column(String, nullable=False)
    external_operation_id = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)