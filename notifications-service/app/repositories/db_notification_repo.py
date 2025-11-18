from uuid import UUID
from sqlalchemy.orm import Session as SASession
from sqlalchemy import desc
from ..database import get_db
from ..models.notification import Notification
from ..schemas.notification import Notification as DBNotification


class NotificationRepo:
    def __init__(self):
        self.db: SASession = next(get_db())

    def create_notification(self, notification: Notification) -> Notification:
        db_notification = DBNotification(**notification.dict())
        self.db.add(db_notification)
        self.db.commit()
        self.db.refresh(db_notification)
        return Notification.from_orm(db_notification)

    def get_notification_by_id(self, notification_id: UUID) -> Notification:
        notification = self.db.query(DBNotification).filter(
            DBNotification.notification_id == notification_id
        ).first()

        if notification is None:
            raise KeyError(f"Notification with id={notification_id} not found")

        return Notification.from_orm(notification)

    def get_user_notifications(self, user_id: UUID, page: int, page_size: int):
        query = self.db.query(DBNotification).filter(
            DBNotification.user_id == user_id
        ).order_by(desc(DBNotification.sent_at))

        total_items = query.count()
        total_pages = (total_items + page_size - 1) // page_size

        notifications = query.offset((page - 1) * page_size).limit(page_size).all()

        return [Notification.from_orm(notification) for notification in notifications], total_items, total_pages

    def mark_as_read(self, notification_id: UUID) -> Notification:
        notification = self.db.query(DBNotification).filter(
            DBNotification.notification_id == notification_id
        ).first()

        if notification is None:
            raise KeyError(f"Notification with id={notification_id} not found")

        notification.status = "read"
        self.db.commit()
        self.db.refresh(notification)

        return Notification.from_orm(notification)