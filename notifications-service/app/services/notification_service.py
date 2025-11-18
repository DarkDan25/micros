from uuid import UUID, uuid4
from datetime import datetime
from ..models.notification import Notification, NotificationType, ReceiptRequest, TriggerRequest, \
    NotificationResponse, TriggerResponse
from ..repositories.db_notification_repo import NotificationRepo


class NotificationService:
    def __init__(self):
        self.notification_repo = NotificationRepo()

    def send_receipt(self, request: ReceiptRequest) -> NotificationResponse:
        notification = Notification(
            notification_id=uuid4(),
            user_id=request.user_id,
            type=NotificationType.RECEIPT,
            message="Чек отправлен",
            data={"order_id": request.order_id},
            sent_at=datetime.now(),
            status="sent"
        )

        created_notification = self.notification_repo.create_notification(notification)
        return NotificationResponse(
            message="Чек отправлен",
            notification_id=created_notification.notification_id
        )

    def trigger_notification(self, request: TriggerRequest) -> TriggerResponse:
        message = self._get_message_by_type(request.type, request.data)

        notification = Notification(
            notification_id=uuid4(),
            user_id=request.user_id,
            type=request.type,
            message=message,
            data=request.data,
            sent_at=datetime.now(),
            status="sent"
        )

        self.notification_repo.create_notification(notification)

        return TriggerResponse(
            type=request.type.value,
            user_id=request.user_id,
            data=request.data
        )

    def get_user_notifications(self, user_id: UUID, page: int = 1, page_size: int = 20):
        return self.notification_repo.get_user_notifications(user_id, page, page_size)

    def _get_message_by_type(self, notification_type: NotificationType, data: dict) -> str:
        messages = {
            NotificationType.SESSION_REMINDER: f"Напоминание о сеансе {data.get('movie_title', '')}",
            NotificationType.PAYMENT_SUCCESS: "Оплата прошла успешно",
            NotificationType.BONUS_EARNED: "Вам начислены бонусы",
            NotificationType.WELCOME: "Добро пожаловать в наш кинотеатр!",
            NotificationType.ORDER_CONFIRMED: "Ваш заказ подтвержден"
        }
        return messages.get(notification_type, "Уведомление")