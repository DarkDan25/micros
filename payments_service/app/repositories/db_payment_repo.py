from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import desc
from ..models.payment import Payment
from ..schemas.payment import Payment as DBPayment


class PaymentRepo:
    def __init__(self, db: Session):
        self.db = db

    def create_payment(self, payment: Payment) -> Payment:
        db_payment = DBPayment(**payment.dict())
        self.db.add(db_payment)
        self.db.commit()
        self.db.refresh(db_payment)
        return Payment.from_orm(db_payment)

    def get_payment_by_id(self, payment_id: UUID) -> Payment:
        payment = self.db.query(DBPayment).filter(DBPayment.payment_id == payment_id).first()
        if not payment:
            raise KeyError(f"Payment with id={payment_id} not found")
        return Payment.from_orm(payment)

    def update_payment(self, payment: Payment) -> Payment:
        db_payment = self.db.query(DBPayment).filter(DBPayment.payment_id == payment.payment_id).first()
        if not db_payment:
            raise KeyError(f"Payment with id={payment.payment_id} not found")
        for k, v in payment.dict().items():
            setattr(db_payment, k, v)
        self.db.commit()
        self.db.refresh(db_payment)
        return Payment.from_orm(db_payment)

    def get_user_payments(self, user_id: UUID, page: int, page_size: int):
        query = self.db.query(DBPayment).filter(DBPayment.user_id == user_id).order_by(desc(DBPayment.created_at))
        total_items = query.count()
        total_pages = (total_items + page_size - 1) // page_size
        payments = query.offset((page - 1) * page_size).limit(page_size).all()
        return [Payment.from_orm(p) for p in payments], total_items, total_pages
