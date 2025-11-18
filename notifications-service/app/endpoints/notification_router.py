from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from ..services.notification_service import NotificationService
from ..models.notification import (
    ReceiptRequest, TriggerRequest,
    NotificationResponse, TriggerResponse
)

notification_router = APIRouter(prefix='/notifications', tags=['Notifications'])

@notification_router.post('/receipt', response_model=NotificationResponse)
def send_receipt(
    request: ReceiptRequest,
    notification_service: NotificationService = Depends(NotificationService)
):
    try:
        return notification_service.send_receipt(request)
    except Exception as e:
        raise HTTPException(500, f"Internal server error: {str(e)}")

@notification_router.post('/trigger', response_model=TriggerResponse)
def trigger_notification(
    request: TriggerRequest,
    notification_service: NotificationService = Depends(NotificationService)
):
    try:
        return notification_service.trigger_notification(request)
    except Exception as e:
        raise HTTPException(500, f"Internal server error: {str(e)}")

@notification_router.get('/user/{user_id}')
def get_user_notifications(
    user_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    notification_service: NotificationService = Depends(NotificationService)
):
    try:
        notifications, total_items, total_pages = notification_service.get_user_notifications(user_id, page, page_size)
        return {
            "items": notifications,
            "page": page,
            "page_size": page_size,
            "total_items": total_items,
            "total_pages": total_pages
        }
    except Exception as e:
        raise HTTPException(500, f"Internal server error: {str(e)}")

@notification_router.post('/{notification_id}/read')
def mark_as_read(
    notification_id: UUID,
    notification_service: NotificationService = Depends(NotificationService)
):
    try:
        notification = notification_service.notification_repo.mark_as_read(notification_id)
        return {"status": "marked as read", "notification_id": notification_id}
    except KeyError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Internal server error: {str(e)}")