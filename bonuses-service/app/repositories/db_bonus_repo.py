from uuid import UUID
from sqlalchemy.orm import Session as SASession
from sqlalchemy import desc, func
from ..database import get_db
from ..models.bonus import BonusOperation
from ..schemas.bonus import BonusOperation as DBBonusOperation


class BonusRepo:
    def __init__(self):
        self.db: SASession = next(get_db())

    def get_user_balance(self, user_id: UUID) -> int:
        last_operation = self.db.query(DBBonusOperation).filter(
            DBBonusOperation.user_id == user_id
        ).order_by(desc(DBBonusOperation.created_at)).first()

        return last_operation.balance_after if last_operation else 0

    def get_last_operation(self, user_id: UUID) -> BonusOperation | None:
        operation = self.db.query(DBBonusOperation).filter(
            DBBonusOperation.user_id == user_id
        ).order_by(desc(DBBonusOperation.created_at)).first()

        return BonusOperation.from_orm(operation) if operation else None

    def create_operation(self, operation: BonusOperation) -> BonusOperation:
        db_operation = DBBonusOperation(**operation.dict())
        self.db.add(db_operation)
        self.db.commit()
        self.db.refresh(db_operation)
        return BonusOperation.from_orm(db_operation)

    def get_user_history(self, user_id: UUID, page: int, page_size: int):
        query = self.db.query(DBBonusOperation).filter(
            DBBonusOperation.user_id == user_id
        ).order_by(desc(DBBonusOperation.created_at))

        total_items = query.count()
        total_pages = (total_items + page_size - 1) // page_size

        operations = query.offset((page - 1) * page_size).limit(page_size).all()

        return [BonusOperation.from_orm(op) for op in operations], total_items, total_pages

    def get_operation_by_id(self, operation_id: UUID) -> BonusOperation:
        operation = self.db.query(DBBonusOperation).filter(
            DBBonusOperation.operation_id == operation_id
        ).first()

        if operation is None:
            raise KeyError(f"Operation with id={operation_id} not found")

        return BonusOperation.from_orm(operation)