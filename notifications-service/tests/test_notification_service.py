import pytest
from uuid import uuid4
from datetime import datetime
from app.models.notification import Notification, NotificationType, ReceiptRequest, TriggerRequest
from app.services.notification_service import NotificationService
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
        # Arrange
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
        
        request = ReceiptRequest(
            order_id=order_id,
            user_id=user_id
        )
        
        # Act
        result = notification_service.send_receipt(request)
        
        # Assert
        assert result.message == "Чек отправлен"
        assert result.notification_id == mock_notification.notification_id
        mock_notification_repo.create_notification.assert_called_once()
    
    @pytest.mark.unit
    def test_trigger_notification_session_reminder(self, notification_service, mock_notification_repo):
        # Arrange
        user_id = uuid4()
        movie_title = "Avatar 2"
        
        request = TriggerRequest(
            type=NotificationType.SESSION_REMINDER,
            user_id=user_id,
            data={"movie_title": movie_title}
        )
        
        # Act
        result = notification_service.trigger_notification(request)
        
        # Assert
        assert result.type == "session_reminder"
        assert result.user_id == user_id
        assert result.data["movie_title"] == movie_title
        mock_notification_repo.create_notification.assert_called_once()
    
    @pytest.mark.unit
    def test_trigger_notification_payment_success(self, notification_service, mock_notification_repo):
        # Arrange
        user_id = uuid4()
        
        request = TriggerRequest(
            type=NotificationType.PAYMENT_SUCCESS,
            user_id=user_id,
            data={}
        )
        
        # Act
        result = notification_service.trigger_notification(request)
        
        # Assert
        assert result.type == "payment_success"
        assert result.user_id == user_id
        mock_notification_repo.create_notification.assert_called_once()
    
    @pytest.mark.unit
    def test_trigger_notification_bonus_earned(self, notification_service, mock_notification_repo):
        # Arrange
        user_id = uuid4()
        bonus_amount = 100
        
        request = TriggerRequest(
            type=NotificationType.BONUS_EARNED,
            user_id=user_id,
            data={"bonus_amount": bonus_amount}
        )
        
        # Act
        result = notification_service.trigger_notification(request)
        
        # Assert
        assert result.type == "bonus_earned"
        assert result.user_id == user_id
        assert result.data["bonus_amount"] == bonus_amount
        mock_notification_repo.create_notification.assert_called_once()
    
    @pytest.mark.unit
    def test_trigger_notification_welcome(self, notification_service, mock_notification_repo):
        # Arrange
        user_id = uuid4()
        
        request = TriggerRequest(
            type=NotificationType.WELCOME,
            user_id=user_id,
            data={}
        )
        
        # Act
        result = notification_service.trigger_notification(request)
        
        # Assert
        assert result.type == "welcome"
        assert result.user_id == user_id
        mock_notification_repo.create_notification.assert_called_once()
    
    @pytest.mark.unit
    def test_trigger_notification_order_confirmed(self, notification_service, mock_notification_repo):
        # Arrange
        user_id = uuid4()
        order_id = "order_456"
        
        request = TriggerRequest(
            type=NotificationType.ORDER_CONFIRMED,
            user_id=user_id,
            data={"order_id": order_id}
        )
        
        # Act
        result = notification_service.trigger_notification(request)
        
        # Assert
        assert result.type == "order_confirmed"
        assert result.user_id == user_id
        assert result.data["order_id"] == order_id
        mock_notification_repo.create_notification.assert_called_once()
    
    @pytest.mark.unit
    def test_get_user_notifications(self, notification_service, mock_notification_repo):
        # Arrange
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
        
        # Act
        result = notification_service.get_user_notifications(user_id)
        
        # Assert
        assert len(result[0]) == 2
        assert result[1] == 2  # total_items
        assert result[2] == 1  # total_pages
        mock_notification_repo.get_user_notifications.assert_called_once_with(user_id, 1, 20)
    
    @pytest.mark.unit
    def test_get_message_by_type_session_reminder(self, notification_service):
        # Arrange
        notification_type = NotificationType.SESSION_REMINDER
        data = {"movie_title": "Inception"}
        
        # Act
        result = notification_service._get_message_by_type(notification_type, data)
        
        # Assert
        assert result == "Напоминание о сеансе Inception"
    
    @pytest.mark.unit
    def test_get_message_by_type_payment_success(self, notification_service):
        # Arrange
        notification_type = NotificationType.PAYMENT_SUCCESS
        data = {}
        
        # Act
        result = notification_service._get_message_by_type(notification_type, data)
        
        # Assert
        assert result == "Оплата прошла успешно"
    
    @pytest.mark.unit
    def test_get_message_by_type_bonus_earned(self, notification_service):
        # Arrange
        notification_type = NotificationType.BONUS_EARNED
        data = {}
        
        # Act
        result = notification_service._get_message_by_type(notification_type, data)
        
        # Assert
        assert result == "Вам начислены бонусы"
    
    @pytest.mark.unit
    def test_get_message_by_type_welcome(self, notification_service):
        # Arrange
        notification_type = NotificationType.WELCOME
        data = {}
        
        # Act
        result = notification_service._get_message_by_type(notification_type, data)
        
        # Assert
        assert result == "Добро пожаловать в наш кинотеатр!"
    
    @pytest.mark.unit
    def test_get_message_by_type_order_confirmed(self, notification_service):
        # Arrange
        notification_type = NotificationType.ORDER_CONFIRMED
        data = {}
        
        # Act
        result = notification_service._get_message_by_type(notification_type, data)
        
        # Assert
        assert result == "Ваш заказ подтвержден"
    
    @pytest.mark.unit
    def test_get_message_by_type_unknown(self, notification_service):
        # Arrange
        notification_type = "unknown_type"
        data = {}
        
        # Act
        result = notification_service._get_message_by_type(notification_type, data)
        
        # Assert
        assert result == "Уведомление"
    
    @pytest.mark.unit
    def test_get_message_by_type_session_reminder_no_movie_title(self, notification_service):
        # Arrange
        notification_type = NotificationType.SESSION_REMINDER
        data = {}  # No movie_title in data
        
        # Act
        result = notification_service._get_message_by_type(notification_type, data)
        
        # Assert
        assert result == "Напоминание о сеансе "  # Empty movie title