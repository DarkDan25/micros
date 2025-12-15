from uuid import UUID, uuid4
from datetime import datetime
from ..models.payment import Payment, PaymentStatus, PaymentMethod, InitiatePaymentRequest, PaymentStatusResponse
from ..repositories.db_payment_repo import PaymentRepo
from sqlalchemy.orm import Session


class PaymentService:
    def __init__(self, db: Session):
        self.payment_repo = PaymentRepo(db)

    def initiate_payment(self, user_id: UUID, request: InitiatePaymentRequest) -> Payment:
        amount = self._calculate_amount(request.order_id)

        payment = Payment(
            payment_id=uuid4(),
            order_id=request.order_id,
            user_id=user_id,
            amount=amount,
            status=PaymentStatus.PENDING,
            payment_method=request.payment_method,
            confirmation_url=f"https://payment-gateway.com/confirm/{uuid4()}",
            created_at=datetime.now(),
            updated_at=None
        )

        return self.payment_repo.create_payment(payment)

    def process_webhook(self, payment_id: UUID) -> dict:
        payment = self.payment_repo.get_payment_by_id(payment_id)
        payment.status = PaymentStatus.SUCCESS
        payment.updated_at = datetime.now()
        self.payment_repo.update_payment(payment)
        return {"status": "Оплачено"}

    def get_payment_status(self, payment_id: UUID) -> PaymentStatusResponse:
        payment = self.payment_repo.get_payment_by_id(payment_id)
        return PaymentStatusResponse(**payment.dict())

    def get_user_payments(self, user_id: UUID, page: int = 1, page_size: int = 20):
        return self.payment_repo.get_user_payments(user_id, page, page_size)

    def _calculate_amount(self, order_id: str) -> float:
        return 500.0
