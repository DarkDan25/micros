from uuid import UUID
from sqlalchemy.orm import Session as SASession
from sqlalchemy import func
from ..database import get_db
from ..models.review import Review, ReviewStatus
from ..schemas.review import Review as DBReview


class ReviewRepo:
    def __init__(self):
        self.db: SASession = next(get_db())

    def get_reviews_by_target(self, target_id: str, page: int, page_size: int):
        query = self.db.query(DBReview).filter(
            DBReview.target_id == target_id,
            DBReview.status == ReviewStatus.ACTIVE
        ).order_by(DBReview.created_at.desc())

        total_items = query.count()
        total_pages = (total_items + page_size - 1) // page_size

        reviews = query.offset((page - 1) * page_size).limit(page_size).all()

        return [Review.from_orm(review) for review in reviews], total_items, total_pages

    def get_review_by_id(self, id: UUID) -> Review:
        review = self.db.query(DBReview).filter(DBReview.id == id).first()
        if review is None:
            raise KeyError(f"Review with id={id} not found")
        return Review.from_orm(review)

    def get_reviews_by_user_and_target(self, user_id: UUID, target_id: str):
        reviews = self.db.query(DBReview).filter(
            DBReview.user_id == user_id,
            DBReview.target_id == target_id,
            DBReview.status == ReviewStatus.ACTIVE
        ).all()
        return [Review.from_orm(review) for review in reviews]

    def create_review(self, review: Review) -> Review:
        db_review = DBReview(**review.dict())
        self.db.add(db_review)
        self.db.commit()
        self.db.refresh(db_review)
        return Review.from_orm(db_review)

    def update_review(self, review: Review) -> Review:
        db_review = self.db.query(DBReview).filter(DBReview.id == review.id).first()
        if db_review is None:
            raise KeyError(f"Review with id={review.id} not found")

        for key, value in review.dict().items():
            setattr(db_review, key, value)

        self.db.commit()
        self.db.refresh(db_review)
        return Review.from_orm(db_review)

    def get_review_stats(self, target_id: str) -> dict:
        stats = self.db.query(
            func.count(DBReview.id).label('total_reviews'),
            func.avg(DBReview.rating).label('average_rating')
        ).filter(
            DBReview.target_id == target_id,
            DBReview.status == ReviewStatus.ACTIVE
        ).first()

        return {
            'target_id': target_id,
            'total_reviews': stats.total_reviews or 0,
            'average_rating': round(float(stats.average_rating or 0), 2)
        }