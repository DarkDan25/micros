import pytest
from uuid import uuid4
from datetime import datetime
from unittest.mock import Mock
from ..app.services.review_service import ReviewService
from ..app.models.review import Review, ReviewStatus, CreateReviewRequest, UpdateReviewRequest

# Мок сессии базы данных для конструктора сервиса
@pytest.fixture
def mock_db():
    return Mock()

# Создаём сервис с мокнутой базой и заменой review_repo на Mock
@pytest.fixture
def review_service(mock_db):
    service = ReviewService(mock_db)
    service.review_repo = Mock()
    return service

@pytest.fixture
def sample_review():
    return Review(
        id=uuid4(),
        user_id=uuid4(),
        target_id="movie_123",
        rating=8,
        text="Great movie!",
        status=ReviewStatus.ACTIVE,
        created_at=datetime.now(),
        updated_at=None
    )

class TestReviewServiceUnit:

    @pytest.mark.unit
    def test_create_review_success(self, review_service, sample_review):
        """Test successful review creation"""
        user_id = sample_review.user_id
        request = CreateReviewRequest(
            target_id=sample_review.target_id,
            rating=sample_review.rating,
            text=sample_review.text
        )

        review_service.review_repo.get_reviews_by_user_and_target.return_value = []
        review_service.review_repo.create_review.return_value = sample_review

        result = review_service.create_review(user_id, request)

        assert result.id == sample_review.id
        assert result.user_id == sample_review.user_id
        assert result.target_id == sample_review.target_id
        assert result.rating == sample_review.rating
        assert result.text == sample_review.text
        assert result.status == ReviewStatus.ACTIVE
        assert result.created_at is not None
        assert result.updated_at is None

        review_service.review_repo.get_reviews_by_user_and_target.assert_called_once_with(user_id, sample_review.target_id)
        review_service.review_repo.create_review.assert_called_once()

    @pytest.mark.unit
    def test_create_review_user_already_reviewed(self, review_service, sample_review):
        """Test review creation when user already reviewed the target"""
        user_id = sample_review.user_id
        request = CreateReviewRequest(
            target_id=sample_review.target_id,
            rating=sample_review.rating,
            text=sample_review.text
        )

        review_service.review_repo.get_reviews_by_user_and_target.return_value = [sample_review]
        review_service.review_repo.create_review.reset_mock()

        with pytest.raises(ValueError, match="User already reviewed this movie"):
            review_service.create_review(user_id, request)

        review_service.review_repo.get_reviews_by_user_and_target.assert_called_once()
        review_service.review_repo.create_review.assert_not_called()

    @pytest.mark.unit
    def test_create_review_different_ratings(self, review_service):
        user_id = uuid4()
        target_id = "movie_test"

        for rating in [1, 5, 10]:
            request = CreateReviewRequest(
                target_id=target_id,
                rating=rating,
                text=f"Review with rating {rating}"
            )

            review_service.review_repo.get_reviews_by_user_and_target.return_value = []
            review_service.review_repo.create_review.side_effect = lambda r: Review(
                id=uuid4(),
                user_id=user_id,
                target_id=r.target_id,
                rating=r.rating,
                text=r.text,
                status=ReviewStatus.ACTIVE,
                created_at=datetime.now(),
                updated_at=None
            )

            result = review_service.create_review(user_id, request)

            assert result.rating == rating
            assert result.text == f"Review with rating {rating}"
            assert result.status == ReviewStatus.ACTIVE

    @pytest.mark.unit
    def test_create_review_invalid_rating(self, review_service):
        """Test review creation with invalid ratings"""
        user_id = uuid4()
        target_id = "movie_test"

        with pytest.raises(ValueError):
            CreateReviewRequest(target_id=target_id, rating=0, text="Invalid rating")

        with pytest.raises(ValueError):
            CreateReviewRequest(target_id=target_id, rating=11, text="Invalid rating")

    @pytest.mark.unit
    def test_update_review_success(self, review_service, sample_review):
        """Test successful review update"""
        updated_rating = 9
        updated_text = "Updated review text"
        request = UpdateReviewRequest(rating=updated_rating, text=updated_text)

        review_service.review_repo.get_review_by_id.return_value = sample_review
        review_service.review_repo.update_review.return_value = Review(
            **{**sample_review.model_dump(), "rating": updated_rating, "text": updated_text, "updated_at": datetime.now()}
        )

        result = review_service.update_review(sample_review.id, sample_review.user_id, request)

        assert result.rating == updated_rating
        assert result.text == updated_text
        assert result.updated_at is not None
        assert result.status == ReviewStatus.ACTIVE

        review_service.review_repo.get_review_by_id.assert_called_once_with(sample_review.id)
        review_service.review_repo.update_review.assert_called_once()

    @pytest.mark.unit
    def test_update_review_wrong_user(self, review_service, sample_review):
        """Test review update by wrong user"""
        wrong_user_id = uuid4()
        request = UpdateReviewRequest(rating=9, text="Updated review")

        review_service.review_repo.get_review_by_id.return_value = sample_review
        review_service.review_repo.update_review.reset_mock()

        with pytest.raises(PermissionError, match="User can only edit their own reviews"):
            review_service.update_review(sample_review.id, wrong_user_id, request)

        review_service.review_repo.get_review_by_id.assert_called_once()
        review_service.review_repo.update_review.assert_not_called()

    @pytest.mark.unit
    def test_update_review_deleted_review(self, review_service, sample_review):
        """Test updating a deleted review"""
        sample_review.status = ReviewStatus.DELETED
        request = UpdateReviewRequest(rating=9, text="Updated review")

        review_service.review_repo.get_review_by_id.return_value = sample_review
        review_service.review_repo.update_review.reset_mock()

        with pytest.raises(ValueError, match="Cannot update deleted review"):
            review_service.update_review(sample_review.id, sample_review.user_id, request)

        review_service.review_repo.get_review_by_id.assert_called_once()
        review_service.review_repo.update_review.assert_not_called()

    @pytest.mark.unit
    def test_update_review_not_found(self, review_service):
        """Test updating a non-existent review"""
        non_existent_review_id = uuid4()
        user_id = uuid4()
        request = UpdateReviewRequest(rating=9, text="Updated review")

        review_service.review_repo.get_review_by_id.side_effect = KeyError("Review not found")

        with pytest.raises(KeyError, match="Review not found"):
            review_service.update_review(non_existent_review_id, user_id, request)

    @pytest.mark.unit
    def test_delete_review_success(self, review_service, sample_review):
        """Test successful review deletion"""
        review_service.review_repo.get_review_by_id.return_value = sample_review
        review_service.review_repo.update_review.side_effect = lambda r: setattr(sample_review, "status", ReviewStatus.DELETED) or setattr(sample_review, "updated_at", datetime.now()) or r

        result = review_service.delete_review(sample_review.id, sample_review.user_id)

        assert result["status"] == "deleted"
        assert sample_review.status == ReviewStatus.DELETED
        assert sample_review.updated_at is not None

        review_service.review_repo.get_review_by_id.assert_called_once_with(sample_review.id)
        review_service.review_repo.update_review.assert_called_once()

    @pytest.mark.unit
    def test_delete_review_wrong_user(self, review_service, sample_review):
        """Test review deletion by wrong user"""
        wrong_user_id = uuid4()
        review_service.review_repo.get_review_by_id.return_value = sample_review
        review_service.review_repo.update_review.reset_mock()

        with pytest.raises(PermissionError, match="User can only delete their own reviews"):
            review_service.delete_review(sample_review.id, wrong_user_id)

        review_service.review_repo.get_review_by_id.assert_called_once()
        review_service.review_repo.update_review.assert_not_called()
