from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Dict, Any, Optional
import enum


class NotificationType(enum.Enum):
    RECEIPT = "receipt"
    SESSION_REMINDER = "session_reminder"
    PAYMENT_SUCCESS = "payment_success"
    BONUS_EARNED = "bonus_earned"
    WELCOME = "welcome"
    ORDER_CONFIRMED = "order_confirmed"


class Notification(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    notification_id: UUID
    user_id: UUID
    type: NotificationType
    message: str
    data: Dict[str, Any]
    sent_at: datetime
    status: str


class ReceiptRequest(BaseModel):
    order_id: str
    user_id: UUID


class TriggerRequest(BaseModel):
    type: NotificationType
    user_id: UUID
    data: Dict[str, Any]


class NotificationResponse(BaseModel):
    message: str
    notification_id: UUID


class TriggerResponse(BaseModel):
    type: str
    user_id: UUID
    data: Dict[str, Any]