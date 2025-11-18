from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from ..services.bonus_service import BonusService
from ..models.bonus import (
    EarnBonusRequest, ApplyBonusRequest, AdjustBonusRequest,
    BalanceResponse, OperationResponse, HistoryResponse
)

bonus_router = APIRouter(prefix='/bonuses', tags=['Bonuses'])

@bonus_router.post('/earn', response_model=OperationResponse)
def earn_bonus(
    request: EarnBonusRequest,
    bonus_service: BonusService = Depends(BonusService)
):
    try:
        return bonus_service.earn_bonus(request)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Internal server error: {str(e)}")

@bonus_router.post('/apply', response_model=OperationResponse)
def apply_bonus(
    request: ApplyBonusRequest,
    bonus_service: BonusService = Depends(BonusService)
):
    try:
        return bonus_service.apply_bonus(request)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Internal server error: {str(e)}")

@bonus_router.post('/adjust', response_model=OperationResponse)
def adjust_balance(
    request: AdjustBonusRequest,
    bonus_service: BonusService = Depends(BonusService)
):
    try:
        return bonus_service.adjust_balance(request)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Internal server error: {str(e)}")

@bonus_router.get('/{user_id}/balance', response_model=BalanceResponse)
def get_balance(
    user_id: UUID,
    bonus_service: BonusService = Depends(BonusService)
):
    try:
        return bonus_service.get_balance(user_id)
    except Exception as e:
        raise HTTPException(500, f"Internal server error: {str(e)}")

@bonus_router.get('/{user_id}/history', response_model=HistoryResponse)
def get_history(
    user_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    bonus_service: BonusService = Depends(BonusService)
):
    try:
        return bonus_service.get_history(user_id, page, page_size)
    except Exception as e:
        raise HTTPException(500, f"Internal server error: {str(e)}")

@bonus_router.get('/operations/{operation_id}', response_model=OperationResponse)
def get_operation(
    operation_id: UUID,
    bonus_service: BonusService = Depends(BonusService)
):
    try:
        return bonus_service.bonus_repo.get_operation_by_id(operation_id)
    except KeyError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Internal server error: {str(e)}")