from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
import enum


class PaymentStatus(enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentMethod(enum.Enum):
    ONLINE = "online"
    CARD = "card"
    BONUS = "bonus"
    CASH = "cash"


class Payment(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    payment_id: UUID
    order_id: str
    user_id: UUID
    amount: float = Field(gt=0)
    status: PaymentStatus
    payment_method: PaymentMethod
    confirmation_url: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class InitiatePaymentRequest(BaseModel):
    order_id: str
    payment_method: PaymentMethod


class InitiatePaymentResponse(BaseModel):
    payment_id: UUID
    confirmation_url: str


class WebhookRequest(BaseModel):
    payment_id: UUID


class WebhookResponse(BaseModel):
    status: str


class PaymentStatusResponse(BaseModel):
    payment_id: UUID
    status: PaymentStatus
    order_id: str
    amount: float
    payment_method: PaymentMethod
    created_at: datetime