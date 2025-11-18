from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from ..services.payment_service import PaymentService
from ..models.payment import (
    InitiatePaymentRequest, InitiatePaymentResponse,
    WebhookRequest, WebhookResponse, PaymentStatusResponse
)

payment_router = APIRouter(prefix='/payments', tags=['Payments'])

@payment_router.post('/initiate', response_model=InitiatePaymentResponse)
def initiate_payment(
    request: InitiatePaymentRequest,
    user_id: UUID = Query(..., description="ID пользователя"),
    payment_service: PaymentService = Depends(PaymentService)
):
    try:
        payment = payment_service.initiate_payment(user_id, request)
        return InitiatePaymentResponse(
            payment_id=payment.payment_id,
            confirmation_url=payment.confirmation_url
        )
    except Exception as e:
        raise HTTPException(500, f"Internal server error: {str(e)}")

@payment_router.post('/webhook/yandex', response_model=WebhookResponse)
def process_webhook(
    request: WebhookRequest,
    payment_service: PaymentService = Depends(PaymentService)
):
    try:
        result = payment_service.process_webhook(request.payment_id)
        return WebhookResponse(status=result["status"])
    except KeyError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Internal server error: {str(e)}")

@payment_router.get('/{payment_id}/status', response_model=PaymentStatusResponse)
def get_payment_status(
    payment_id: UUID,
    payment_service: PaymentService = Depends(PaymentService)
):
    try:
        return payment_service.get_payment_status(payment_id)
    except KeyError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Internal server error: {str(e)}")

@payment_router.get('/user/{user_id}')
def get_user_payments(
    user_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    payment_service: PaymentService = Depends(PaymentService)
):
    try:
        payments, total_items, total_pages = payment_service.get_user_payments(user_id, page, page_size)
        return {
            "items": payments,
            "page": page,
            "page_size": page_size,
            "total_items": total_items,
            "total_pages": total_pages
        }
    except Exception as e:
        raise HTTPException(500, f"Internal server error: {str(e)}")