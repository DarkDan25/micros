from uuid import UUID, uuid4
from datetime import datetime
from ..models.bonus import BonusOperation, BonusReason, EarnBonusRequest, ApplyBonusRequest, AdjustBonusRequest, \
    BalanceResponse, OperationResponse
from ..repositories.db_bonus_repo import BonusRepo


class BonusService:
    def __init__(self):
        self.bonus_repo = BonusRepo()

    def earn_bonus(self, request: EarnBonusRequest) -> OperationResponse:
        current_balance = self.bonus_repo.get_user_balance(request.user_id)
        new_balance = current_balance + request.amount

        operation = BonusOperation(
            operation_id=uuid4(),
            user_id=request.user_id,
            delta=request.amount,
            balance_after=new_balance,
            reason=request.reason,
            description=request.description,
            external_operation_id=request.external_operation_id,
            created_at=datetime.now()
        )

        created_operation = self.bonus_repo.create_operation(operation)
        return OperationResponse(**created_operation.dict())

    def apply_bonus(self, request: ApplyBonusRequest) -> OperationResponse:
        current_balance = self.bonus_repo.get_user_balance(request.user_id)

        if current_balance < request.amount:
            raise ValueError("Insufficient bonus balance")

        new_balance = current_balance - request.amount

        operation = BonusOperation(
            operation_id=uuid4(),
            user_id=request.user_id,
            delta=-request.amount,
            balance_after=new_balance,
            reason=request.reason,
            description=request.description,
            external_operation_id=request.external_operation_id,
            created_at=datetime.now()
        )

        created_operation = self.bonus_repo.create_operation(operation)
        return OperationResponse(**created_operation.dict())

    def adjust_balance(self, request: AdjustBonusRequest) -> OperationResponse:
        current_balance = self.bonus_repo.get_user_balance(request.user_id)
        new_balance = current_balance + request.delta

        if new_balance < 0:
            raise ValueError("Balance cannot be negative")

        operation = BonusOperation(
            operation_id=uuid4(),
            user_id=request.user_id,
            delta=request.delta,
            balance_after=new_balance,
            reason=request.reason,
            description=request.description,
            external_operation_id=request.external_operation_id,
            created_at=datetime.now()
        )

        created_operation = self.bonus_repo.create_operation(operation)
        return OperationResponse(**created_operation.dict())

    def get_balance(self, user_id: UUID) -> BalanceResponse:
        balance = self.bonus_repo.get_user_balance(user_id)
        last_operation = self.bonus_repo.get_last_operation(user_id)

        return BalanceResponse(
            user_id=user_id,
            balance=balance,
            updated_at=last_operation.created_at if last_operation else datetime.now()
        )

    def get_history(self, user_id: UUID, page: int = 1, page_size: int = 20):
        operations, total_items, total_pages = self.bonus_repo.get_user_history(user_id, page, page_size)

        operation_responses = [OperationResponse(**op.dict()) for op in operations]

        return {
            "items": operation_responses,
            "page": page,
            "page_size": page_size,
            "total_items": total_items,
            "total_pages": total_pages
        }