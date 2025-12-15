from uuid import UUID, uuid4
from datetime import datetime
from ..models.review import Review, ReviewStatus, CreateReviewRequest, UpdateReviewRequest
from ..repositories.db_review_repo import ReviewRepo


class ReviewService:
    def __init__(self, db):
        self.review_repo = ReviewRepo(db)

    def get_reviews_by_target(self, target_id: str, page: int = 1, page_size: int = 10):
        return self.review_repo.get_reviews_by_target(target_id, page, page_size)

    def create_review(self, user_id: UUID, request: CreateReviewRequest) -> Review:
        existing_reviews = self.review_repo.get_reviews_by_user_and_target(user_id, request.target_id)
        if existing_reviews:
            raise ValueError("User already reviewed this movie")

        review = Review(
            id=uuid4(),
            user_id=user_id,
            target_id=request.target_id,
            rating=request.rating,
            text=request.text,
            status=ReviewStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=None
        )
        return self.review_repo.create_review(review)

    def update_review(self, review_id: UUID, user_id: UUID, request: UpdateReviewRequest) -> Review:
        review = self.review_repo.get_review_by_id(review_id)

        if review.user_id != user_id:
            raise PermissionError("User can only edit their own reviews")

        if review.status == ReviewStatus.DELETED:
            raise ValueError("Cannot update deleted review")

        review.rating = request.rating
        review.text = request.text
        review.updated_at = datetime.now()

        return self.review_repo.update_review(review)

    def delete_review(self, review_id: UUID, user_id: UUID) -> dict:
        review = self.review_repo.get_review_by_id(review_id)

        if review.user_id != user_id:
            raise PermissionError("User can only delete their own reviews")

        review.status = ReviewStatus.DELETED
        review.updated_at = datetime.now()

        self.review_repo.update_review(review)
        return {"status": "deleted"}

    def get_review_stats(self, target_id: str) -> dict:
        return self.review_repo.get_review_stats(target_id)
