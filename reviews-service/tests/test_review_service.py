import pytest
from uuid import uuid4
from datetime import datetime
from unittest.mock import Mock
from app.services.review_service import ReviewService
from app.models.review import Review, ReviewStatus, CreateReviewRequest, UpdateReviewRequest


@pytest.fixture
def review_service():
    return ReviewService()


@pytest.fixture
def mock_review_repo():
    return Mock()


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
    """Unit tests for ReviewService"""

    @pytest.mark.unit
    def test_create_review_success(self, review_service, sample_review):
        """Test successful review creation"""
        # Arrange
        user_id = sample_review.user_id
        request = CreateReviewRequest(
            target_id=sample_review.target_id,
            rating=sample_review.rating,
            text=sample_review.text
        )
        
        # Mock the repository
        review_service.review_repo.get_reviews_by_user_and_target = Mock(return_value=[])
        review_service.review_repo.create_review = Mock(return_value=sample_review)
        
        # Act
        result = review_service.create_review(user_id, request)
        
        # Assert
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
        # Arrange
        user_id = sample_review.user_id
        request = CreateReviewRequest(
            target_id=sample_review.target_id,
            rating=sample_review.rating,
            text=sample_review.text
        )
        
        # Mock existing review
        existing_reviews = [sample_review]
        review_service.review_repo.get_reviews_by_user_and_target = Mock(return_value=existing_reviews)
        
        # Act & Assert
        with pytest.raises(ValueError, match="User already reviewed this movie"):
            review_service.create_review(user_id, request)
        
        review_service.review_repo.get_reviews_by_user_and_target.assert_called_once()
        review_service.review_repo.create_review.assert_not_called()

    @pytest.mark.unit
    def test_create_review_different_ratings(self, review_service):
        """Test review creation with different ratings"""
        user_id = uuid4()
        target_id = "movie_test"
        
        for rating in [1, 5, 10]:
            request = CreateReviewRequest(
                target_id=target_id,
                rating=rating,
                text=f"Review with rating {rating}"
            )
            
            review_service.review_repo.get_reviews_by_user_and_target = Mock(return_value=[])
            review_service.review_repo.create_review = Mock()
            
            result = review_service.create_review(user_id, request)
            
            assert result.rating == rating
            assert result.text == f"Review with rating {rating}"
            assert result.status == ReviewStatus.ACTIVE

    @pytest.mark.unit
    def test_create_review_invalid_rating(self, review_service):
        """Test review creation with invalid ratings"""
        user_id = uuid4()
        target_id = "movie_test"
        
        # Test rating too low
        with pytest.raises(ValueError):
            CreateReviewRequest(
                target_id=target_id,
                rating=0,  # Below minimum
                text="Invalid rating"
            )
        
        # Test rating too high
        with pytest.raises(ValueError):
            CreateReviewRequest(
                target_id=target_id,
                rating=11,  # Above maximum
                text="Invalid rating"
            )

    @pytest.mark.unit
    def test_update_review_success(self, review_service, sample_review):
        """Test successful review update"""
        # Arrange
        updated_rating = 9
        updated_text = "Updated review text"
        request = UpdateReviewRequest(
            rating=updated_rating,
            text=updated_text
        )
        
        # Mock the repository
        review_service.review_repo.get_review_by_id = Mock(return_value=sample_review)
        review_service.review_repo.update_review = Mock(return_value=sample_review)
        
        # Act
        result = review_service.update_review(sample_review.id, sample_review.user_id, request)
        
        # Assert
        assert result.rating == updated_rating
        assert result.text == updated_text
        assert result.updated_at is not None
        assert result.status == ReviewStatus.ACTIVE
        
        review_service.review_repo.get_review_by_id.assert_called_once_with(sample_review.id)
        review_service.review_repo.update_review.assert_called_once()

    @pytest.mark.unit
    def test_update_review_wrong_user(self, review_service, sample_review):
        """Test review update by wrong user"""
        # Arrange
        wrong_user_id = uuid4()
        request = UpdateReviewRequest(
            rating=9,
            text="Updated review"
        )
        
        # Mock the repository
        review_service.review_repo.get_review_by_id = Mock(return_value=sample_review)
        
        # Act & Assert
        with pytest.raises(PermissionError, match="User can only edit their own reviews"):
            review_service.update_review(sample_review.id, wrong_user_id, request)
        
        review_service.review_repo.get_review_by_id.assert_called_once()
        review_service.review_repo.update_review.assert_not_called()

    @pytest.mark.unit
    def test_update_review_deleted_review(self, review_service, sample_review):
        """Test updating a deleted review"""
        # Arrange
        sample_review.status = ReviewStatus.DELETED
        request = UpdateReviewRequest(
            rating=9,
            text="Updated review"
        )
        
        # Mock the repository
        review_service.review_repo.get_review_by_id = Mock(return_value=sample_review)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Cannot update deleted review"):
            review_service.update_review(sample_review.id, sample_review.user_id, request)
        
        review_service.review_repo.get_review_by_id.assert_called_once()
        review_service.review_repo.update_review.assert_not_called()

    @pytest.mark.unit
    def test_update_review_not_found(self, review_service):
        """Test updating a non-existent review"""
        # Arrange
        non_existent_review_id = uuid4()
        user_id = uuid4()
        request = UpdateReviewRequest(
            rating=9,
            text="Updated review"
        )
        
        # Mock the repository
        review_service.review_repo.get_review_by_id = Mock(side_effect=KeyError("Review not found"))
        
        # Act & Assert
        with pytest.raises(KeyError, match="Review not found"):
            review_service.update_review(non_existent_review_id, user_id, request)

    @pytest.mark.unit
    def test_delete_review_success(self, review_service, sample_review):
        """Test successful review deletion"""
        # Arrange
        # Mock the repository
        review_service.review_repo.get_review_by_id = Mock(return_value=sample_review)
        review_service.review_repo.update_review = Mock(return_value=sample_review)
        
        # Act
        result = review_service.delete_review(sample_review.id, sample_review.user_id)
        
        # Assert
        assert result["status"] == "deleted"
        assert sample_review.status == ReviewStatus.DELETED
        assert sample_review.updated_at is not None
        
        review_service.review_repo.get_review_by_id.assert_called_once_with(sample_review.id)
        review_service.review_repo.update_review.assert_called_once()

    @pytest.mark.unit
    def test_delete_review_wrong_user(self, review_service, sample_review):
        """Test review deletion by wrong user"""
        # Arrange
        wrong_user_id = uuid4()
        
        # Mock the repository
        review_service.review_repo.get_review_by_id = Mock(return_value=sample_review)
        
        # Act & Assert
        with pytest.raises(PermissionError, match="User can only delete their own reviews"):
            review_service.delete_review(sample_review.id, wrong_user_id)
        
        review_service.review_repo.get_review_by_id.assert_called_once()
        review_service.review_repo.update_review.assert_not_called()

    @pytest.mark.unit
    def test_delete_review_not_found(self, review_service):
        """Test deleting a non-existent review"""
        # Arrange
        non_existent_review_id = uuid4()
        user_id = uuid4()
        
        # Mock the repository
        review_service.review_repo.get_review_by_id = Mock(side_effect=KeyError("Review not found"))
        
        # Act & Assert
        with pytest.raises(KeyError, match="Review not found"):
            review_service.delete_review(non_existent_review_id, user_id)

    @pytest.mark.unit
    def test_get_reviews_by_target(self, review_service):
        """Test getting reviews by target ID"""
        # Arrange
        target_id = "movie_123"
        page = 1
        page_size = 10
        
        sample_reviews = [
            Review(
                id=uuid4(),
                user_id=uuid4(),
                target_id=target_id,
                rating=8,
                text="Great movie!",
                status=ReviewStatus.ACTIVE,
                created_at=datetime.now(),
                updated_at=None
            ),
            Review(
                id=uuid4(),
                user_id=uuid4(),
                target_id=target_id,
                rating=6,
                text="Good movie",
                status=ReviewStatus.ACTIVE,
                created_at=datetime.now(),
                updated_at=None
            )
        ]
        
        # Mock the repository
        review_service.review_repo.get_reviews_by_target = Mock(return_value=(sample_reviews, len(sample_reviews), 1))
        
        # Act
        result = review_service.get_reviews_by_target(target_id, page, page_size)
        
        # Assert
        assert result[0] == sample_reviews
        assert result[1] == len(sample_reviews)  # total_items
        assert result[2] == 1  # total_pages
        
        review_service.review_repo.get_reviews_by_target.assert_called_once_with(target_id, page, page_size)

    @pytest.mark.unit
    def test_get_review_stats(self, review_service):
        """Test getting review statistics"""
        # Arrange
        target_id = "movie_123"
        expected_stats = {
            "average_rating": 7.5,
            "total_reviews": 10,
            "rating_distribution": {
                "1": 0, "2": 1, "3": 2, "4": 1, "5": 3,
                "6": 1, "7": 1, "8": 1, "9": 0, "10": 0
            }
        }
        
        # Mock the repository
        review_service.review_repo.get_review_stats = Mock(return_value=expected_stats)
        
        # Act
        result = review_service.get_review_stats(target_id)
        
        # Assert
        assert result == expected_stats
        review_service.review_repo.get_review_stats.assert_called_once_with(target_id)

    @pytest.mark.unit
    def test_review_status_transitions(self, review_service, sample_review):
        """Test review status transitions"""
        # Initial state
        assert sample_review.status == ReviewStatus.ACTIVE
        
        # Mock the repository for deletion
        review_service.review_repo.get_review_by_id = Mock(return_value=sample_review)
        review_service.review_repo.update_review = Mock()
        
        # Delete the review
        result = review_service.delete_review(sample_review.id, sample_review.user_id)
        
        # After deletion
        assert result["status"] == "deleted"
        assert sample_review.status == ReviewStatus.DELETED
        assert sample_review.updated_at is not None