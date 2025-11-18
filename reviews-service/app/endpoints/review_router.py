from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from ..services.review_service import ReviewService
from ..models.review import CreateReviewRequest, UpdateReviewRequest, ReviewListResponse, ReviewResponse

review_router = APIRouter(prefix='/reviews', tags=['Reviews'])

@review_router.get('/', response_model=ReviewListResponse)
def get_reviews(
    target_id: str = Query(..., description="ID фильма"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    review_service: ReviewService = Depends(ReviewService)
):
    try:
        reviews, total_items, total_pages = review_service.get_reviews_by_target(
            target_id, page, page_size
        )
        return ReviewListResponse(
            items=reviews,
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages
        )
    except Exception as e:
        raise HTTPException(500, f"Internal server error: {str(e)}")

@review_router.post('/', response_model=ReviewResponse)
def create_review(
    request: CreateReviewRequest,
    user_id: UUID = Query(..., description="ID пользователя"),  # В реальном приложении из JWT
    review_service: ReviewService = Depends(ReviewService)
):
    try:
        return review_service.create_review(user_id, request)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Internal server error: {str(e)}")

@review_router.put('/{review_id}', response_model=ReviewResponse)
def update_review(
    review_id: UUID,
    request: UpdateReviewRequest,
    user_id: UUID = Query(..., description="ID пользователя"),
    review_service: ReviewService = Depends(ReviewService)
):
    try:
        return review_service.update_review(review_id, user_id, request)
    except PermissionError as e:
        raise HTTPException(403, str(e))
    except ValueError as e:
        raise HTTPException(400, str(e))
    except KeyError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Internal server error: {str(e)}")

@review_router.delete('/{review_id}')
def delete_review(
    review_id: UUID,
    user_id: UUID = Query(..., description="ID пользователя"),
    review_service: ReviewService = Depends(ReviewService)
):
    try:
        return review_service.delete_review(review_id, user_id)
    except PermissionError as e:
        raise HTTPException(403, str(e))
    except KeyError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Internal server error: {str(e)}")

@review_router.get('/{target_id}/stats')
def get_review_stats(
    target_id: str,
    review_service: ReviewService = Depends(ReviewService)
):
    try:
        return review_service.get_review_stats(target_id)
    except Exception as e:
        raise HTTPException(500, f"Internal server error: {str(e)}")