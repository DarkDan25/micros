import pytest
from uuid import uuid4
from datetime import datetime
from ..app.models.notification import (
    Notification, NotificationType, ReceiptRequest, TriggerRequest,
    NotificationResponse, TriggerResponse
)
from ..app.services.notification_service import NotificationService
from unittest.mock import Mock


@pytest.fixture
def mock_notification_repo():
    return Mock()


@pytest.fixture
def notification_service(mock_notification_repo):
    service = NotificationService()
    service.notification_repo = mock_notification_repo
    return service


class TestNotificationService:

    @pytest.mark.unit
    def test_send_receipt_success(self, notification_service, mock_notification_repo):
        user_id = uuid4()
        order_id = "order_123"

        mock_notification = Notification(
            notification_id=uuid4(),
            user_id=user_id,
            type=NotificationType.RECEIPT,
            message="Чек отправлен",
            data={"order_id": order_id},
            sent_at=datetime.now(),
            status="sent"
        )
        mock_notification_repo.create_notification.return_value = mock_notification

        request = ReceiptRequest(order_id=order_id, user_id=user_id)
        result: NotificationResponse = notification_service.send_receipt(request)

        assert result.message == "Чек отправлен"
        assert result.notification_id == mock_notification.notification_id
        mock_notification_repo.create_notification.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.parametrize("notif_type, expected_message", [
        (NotificationType.SESSION_REMINDER, "Напоминание о сеансе Avatar 2"),
        (NotificationType.PAYMENT_SUCCESS, "Оплата прошла успешно"),
        (NotificationType.BONUS_EARNED, "Вам начислены бонусы"),
        (NotificationType.WELCOME, "Добро пожаловать в наш кинотеатр!"),
        (NotificationType.ORDER_CONFIRMED, "Ваш заказ подтвержден")
    ])
    def test_trigger_notification(self, notification_service, mock_notification_repo, notif_type, expected_message):
        user_id = uuid4()
        data = {"movie_title": "Avatar 2"} if notif_type == NotificationType.SESSION_REMINDER else {}

        request = TriggerRequest(type=notif_type, user_id=user_id, data=data)
        result: TriggerResponse = notification_service.trigger_notification(request)

        assert result.type == notif_type.value
        assert result.user_id == user_id
        if notif_type == NotificationType.SESSION_REMINDER:
            assert result.data["movie_title"] == "Avatar 2"
        mock_notification_repo.create_notification.assert_called_once()
        mock_notification_repo.create_notification.reset_mock()

    @pytest.mark.unit
    def test_get_user_notifications(self, notification_service, mock_notification_repo):
        user_id = uuid4()
        mock_notifications = [
            Notification(
                notification_id=uuid4(),
                user_id=user_id,
                type=NotificationType.SESSION_REMINDER,
                message="Напоминание о сеансе Avatar 2",
                data={"movie_title": "Avatar 2"},
                sent_at=datetime.now(),
                status="sent"
            ),
            Notification(
                notification_id=uuid4(),
                user_id=user_id,
                type=NotificationType.PAYMENT_SUCCESS,
                message="Оплата прошла успешно",
                data={},
                sent_at=datetime.now(),
                status="sent"
            )
        ]
        mock_notification_repo.get_user_notifications.return_value = (mock_notifications, 2, 1)

        notifications, total_items, total_pages = notification_service.get_user_notifications(user_id)

        assert len(notifications) == 2
        assert total_items == 2
        assert total_pages == 1
        mock_notification_repo.get_user_notifications.assert_called_once_with(user_id, 1, 20)

    @pytest.mark.unit
    def test_get_message_by_type(self, notification_service):
        cases = [
            (NotificationType.SESSION_REMINDER, {"movie_title": "Inception"}, "Напоминание о сеансе Inception"),
            (NotificationType.PAYMENT_SUCCESS, {}, "Оплата прошла успешно"),
            (NotificationType.BONUS_EARNED, {}, "Вам начислены бонусы"),
            (NotificationType.WELCOME, {}, "Добро пожаловать в наш кинотеатр!"),
            (NotificationType.ORDER_CONFIRMED, {}, "Ваш заказ подтвержден")
        ]
        for notif_type, data, expected in cases:
            result = notification_service._get_message_by_type(notif_type, data)
            assert result == expected

    @pytest.mark.unit
    def test_get_message_by_type_unknown_type(self, notification_service):
        # Передаем тип, которого нет в словаре сообщений
        class FakeType:
            value = "unknown"

        result = notification_service._get_message_by_type(FakeType(), {})
        assert result == "Уведомление"

    @pytest.mark.unit
    def test_get_message_by_type_session_reminder_no_title(self, notification_service):
        notif_type = NotificationType.SESSION_REMINDER
        data = {}  # нет movie_title
        result = notification_service._get_message_by_type(notif_type, data)
        assert result == "Напоминание о сеансе "
