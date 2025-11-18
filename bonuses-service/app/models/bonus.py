from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
import enum


class BonusReason(enum.Enum):
    PURCHASE = "purchase"
    ORDER_PAYMENT = "order_payment"
    SUPPORT_ADJUSTMENT = "support_adjustment"
    REFERRAL = "referral"
    REGISTRATION = "registration"


class BonusOperation(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    operation_id: UUID
    user_id: UUID
    delta: int
    balance_after: int
    reason: BonusReason
    description: str
    external_operation_id: str
    created_at: datetime


class EarnBonusRequest(BaseModel):
    user_id: UUID
    amount: int = Field(gt=0, description="Amount must be positive")
    reason: BonusReason
    description: str
    external_operation_id: str


class ApplyBonusRequest(BaseModel):
    user_id: UUID
    amount: int = Field(gt=0, description="Amount must be positive")
    reason: BonusReason
    description: str
    external_operation_id: str


class AdjustBonusRequest(BaseModel):
    user_id: UUID
    delta: int
    reason: BonusReason
    description: str
    external_operation_id: str


class BalanceResponse(BaseModel):
    user_id: UUID
    balance: int
    updated_at: datetime


class OperationResponse(BaseModel):
    operation_id: UUID
    user_id: UUID
    delta: int
    balance_after: int
    created_at: datetime


class HistoryResponse(BaseModel):
    items: List[OperationResponse]
    page: int
    page_size: int
    total_items: int
    total_pages: int