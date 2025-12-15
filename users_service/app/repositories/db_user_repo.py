from uuid import UUID
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.user import User
from ..schemas.user import User as DBUser


class UserRepo:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_id(self, user_id: UUID) -> User:
        user = self.db.query(DBUser).filter(DBUser.user_id == user_id).first()
        if user is None:
            raise KeyError(f"User with id={user_id} not found")
        return User.from_orm(user)

    def get_user_by_email(self, email: str) -> User | None:
        user = self.db.query(DBUser).filter(DBUser.email == email).first()
        if user is None:
            return None
        return User.from_orm(user)

    def create_user(self, user: User) -> User:
        db_user = DBUser(**user.dict())
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return User.from_orm(db_user)

    def update_user(self, user: User) -> User:
        db_user = self.db.query(DBUser).filter(DBUser.user_id == user.user_id).first()
        if db_user is None:
            raise KeyError(f"User with id={user.user_id} not found")

        for key, value in user.dict().items():
            setattr(db_user, key, value)

        self.db.commit()
        self.db.refresh(db_user)
        return User.from_orm(db_user)
