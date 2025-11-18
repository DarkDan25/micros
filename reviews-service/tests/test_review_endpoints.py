import pytest
from uuid import uuid4
from httpx import AsyncClient
from app.models.review import Review, ReviewStatus


@pytest.mark.integration
@pytest.mark.asyncio
class TestReviewEndpoints:
    """Integration tests for review API endpoints"""

    async def test_create_review_success(self, client, sample_review_data, sample_user_id):
        """Test successful review creation through API"""
        # Arrange
        request_data = sample_review_data
        
        # Act
        response = await client.post(
            f"/reviews/?user_id={sample_user_id}",
            json=request_data
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["user_id"] == str(sample_user_id)
        assert data["target_id"] == request_data["target_id"]
        assert data["rating"] == request_data["rating"]
        assert data["text"] == request_data["text"]
        assert data["status"] == "active"
        assert "created_at" in data
        assert data["updated_at"] is None

    async def test_create_review_duplicate(self, client, sample_review_data, sample_user_id):
        """Test creating duplicate review by same user for same target"""
        # Create first review
        first_response = await client.post(
            f"/reviews/?user_id={sample_user_id}",
            json=sample_review_data
        )
        assert first_response.status_code == 200
        
        # Try to create second review for same target
        second_response = await client.post(
            f"/reviews/?user_id={sample_user_id}",
            json=sample_review_data
        )
        
        assert second_response.status_code == 400
        assert "already reviewed" in second_response.json()["detail"]

    async def test_create_review_invalid_rating(self, client, sample_user_id):
        """Test creating review with invalid rating"""
        # Test rating too low
        invalid_data_low = {
            "target_id": "movie_test",
            "rating": 0,
            "text": "Invalid rating"
        }
        
        response = await client.post(
            f"/reviews/?user_id={sample_user_id}",
            json=invalid_data_low
        )
        
        assert response.status_code == 422
        
        # Test rating too high
        invalid_data_high = {
            "target_id": "movie_test",
            "rating": 11,
            "text": "Invalid rating"
        }
        
        response = await client.post(
            f"/reviews/?user_id={sample_user_id}",
            json=invalid_data_high
        )
        
        assert response.status_code == 422

    async def test_create_review_missing_user_id(self, client, sample_review_data):
        """Test creating review without user_id parameter"""
        response = await client.post(
            "/reviews/",
            json=sample_review_data
        )
        
        assert response.status_code == 422

    async def test_get_reviews_by_target_success(self, client, sample_user_id, sample_target_id):
        """Test getting reviews by target ID"""
        # Create multiple reviews for the same target
        reviews_data = [
            {"target_id": sample_target_id, "rating": 8, "text": "Great movie!"},
            {"target_id": sample_target_id, "rating": 6, "text": "Good movie"},
            {"target_id": sample_target_id, "rating": 9, "text": "Excellent!"}
        ]
        
        # Create reviews with different users to avoid duplicates
        for i, review_data in enumerate(reviews_data):
            user_id = uuid4()
            create_response = await client.post(
                f"/reviews/?user_id={user_id}",
                json=review_data
            )
            assert create_response.status_code == 200
        
        # Get reviews by target
        response = await client.get(f"/reviews/?target_id={sample_target_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) == 3
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert data["total_items"] == 3
        assert data["total_pages"] == 1
        
        # Verify all reviews have correct target_id
        for review in data["items"]:
            assert review["target_id"] == sample_target_id

    async def test_get_reviews_pagination(self, client, sample_user_id, sample_target_id):
        """Test pagination for reviews by target"""
        # Create 15 reviews for the same target (with different users)
        for i in range(15):
            user_id = uuid4()
            review_data = {
                "target_id": sample_target_id,
                "rating": 5 + (i % 6),
                "text": f"Review {i+1}"
            }
            
            create_response = await client.post(
                f"/reviews/?user_id={user_id}",
                json=review_data
            )
            assert create_response.status_code == 200
        
        # Test first page
        page1_response = await client.get(f"/reviews/?target_id={sample_target_id}&page=1&page_size=5")
        assert page1_response.status_code == 200
        page1_data = page1_response.json()
        assert len(page1_data["items"]) == 5
        assert page1_data["page"] == 1
        assert page1_data["total_items"] == 15
        assert page1_data["total_pages"] == 3
        
        # Test second page
        page2_response = await client.get(f"/reviews/?target_id={sample_target_id}&page=2&page_size=5")
        assert page2_response.status_code == 200
        page2_data = page2_response.json()
        assert len(page2_data["items"]) == 5
        assert page2_data["page"] == 2

    async def test_get_reviews_no_reviews(self, client):
        """Test getting reviews for target with no reviews"""
        target_id = "non_existent_movie"
        
        response = await client.get(f"/reviews/?target_id={target_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total_items"] == 0
        assert data["total_pages"] == 0

    async def test_update_review_success(self, client, sample_review_data, sample_user_id):
        """Test successful review update"""
        # First create a review
        create_response = await client.post(
            f"/reviews/?user_id={sample_user_id}",
            json=sample_review_data
        )
        assert create_response.status_code == 200
        review_data = create_response.json()
        review_id = review_data["id"]
        
        # Update the review
        update_data = {
            "rating": 7,
            "text": "Updated review text"
        }
        
        update_response = await client.put(
            f"/reviews/{review_id}?user_id={sample_user_id}",
            json=update_data
        )
        
        assert update_response.status_code == 200
        updated_data = update_response.json()
        assert updated_data["id"] == review_id
        assert updated_data["rating"] == update_data["rating"]
        assert updated_data["text"] == update_data["text"]
        assert updated_data["updated_at"] is not None
        assert updated_data["user_id"] == str(sample_user_id)

    async def test_update_review_wrong_user(self, client, sample_review_data, sample_user_id):
        """Test updating review by wrong user"""
        # First create a review
        create_response = await client.post(
            f"/reviews/?user_id={sample_user_id}",
            json=sample_review_data
        )
        assert create_response.status_code == 200
        review_data = create_response.json()
        review_id = review_data["id"]
        
        # Try to update with different user
        wrong_user_id = uuid4()
        update_data = {
            "rating": 7,
            "text": "Updated review text"
        }
        
        update_response = await client.put(
            f"/reviews/{review_id}?user_id={wrong_user_id}",
            json=update_data
        )
        
        assert update_response.status_code == 403
        assert "can only edit their own reviews" in update_response.json()["detail"]

    async def test_update_review_invalid_rating(self, client, sample_review_data, sample_user_id):
        """Test updating review with invalid rating"""
        # First create a review
        create_response = await client.post(
            f"/reviews/?user_id={sample_user_id}",
            json=sample_review_data
        )
        assert create_response.status_code == 200
        review_data = create_response.json()
        review_id = review_data["id"]
        
        # Try to update with invalid rating
        invalid_update_data = {
            "rating": 15,
            "text": "Updated review text"
        }
        
        update_response = await client.put(
            f"/reviews/{review_id}?user_id={sample_user_id}",
            json=invalid_update_data
        )
        
        assert update_response.status_code == 422

    async def test_update_nonexistent_review(self, client, sample_user_id):
        """Test updating non-existent review"""
        nonexistent_review_id = uuid4()
        update_data = {
            "rating": 7,
            "text": "Updated review text"
        }
        
        update_response = await client.put(
            f"/reviews/{nonexistent_review_id}?user_id={sample_user_id}",
            json=update_data
        )
        
        assert update_response.status_code == 404

    async def test_delete_review_success(self, client, sample_review_data, sample_user_id):
        """Test successful review deletion"""
        # First create a review
        create_response = await client.post(
            f"/reviews/?user_id={sample_user_id}",
            json=sample_review_data
        )
        assert create_response.status_code == 200
        review_data = create_response.json()
        review_id = review_data["id"]
        
        # Delete the review
        delete_response = await client.delete(
            f"/reviews/{review_id}?user_id={sample_user_id}"
        )
        
        assert delete_response.status_code == 200
        delete_data = delete_response.json()
        assert delete_data["status"] == "deleted"
        
        # Verify review is deleted by checking status
        # Note: In a real implementation, you might want to check if the review is actually soft-deleted

    async def test_delete_review_wrong_user(self, client, sample_review_data, sample_user_id):
        """Test deleting review by wrong user"""
        # First create a review
        create_response = await client.post(
            f"/reviews/?user_id={sample_user_id}",
            json=sample_review_data
        )
        assert create_response.status_code == 200
        review_data = create_response.json()
        review_id = review_data["id"]
        
        # Try to delete with different user
        wrong_user_id = uuid4()
        delete_response = await client.delete(
            f"/reviews/{review_id}?user_id={wrong_user_id}"
        )
        
        assert delete_response.status_code == 403
        assert "can only delete their own reviews" in delete_response.json()["detail"]

    async def test_delete_nonexistent_review(self, client, sample_user_id):
        """Test deleting non-existent review"""
        nonexistent_review_id = uuid4()
        
        delete_response = await client.delete(
            f"/reviews/{nonexistent_review_id}?user_id={sample_user_id}"
        )
        
        assert delete_response.status_code == 404

    async def test_get_review_stats_success(self, client, sample_user_id, sample_target_id):
        """Test getting review statistics"""
        # Create multiple reviews with different ratings
        ratings = [8, 6, 9, 7, 8, 5, 9, 8, 7, 6]
        for rating in ratings:
            user_id = uuid4()  # Different user for each review
            review_data = {
                "target_id": sample_target_id,
                "rating": rating,
                "text": f"Review with rating {rating}"
            }
            
            create_response = await client.post(
                f"/reviews/?user_id={user_id}",
                json=review_data
            )
            assert create_response.status_code == 200
        
        # Get review statistics
        stats_response = await client.get(f"/reviews/{sample_target_id}/stats")
        
        assert stats_response.status_code == 200
        stats_data = stats_response.json()
        assert "average_rating" in stats_data
        assert "total_reviews" in stats_data
        assert stats_data["total_reviews"] == len(ratings)
        assert "rating_distribution" in stats_data
        
        # Verify average rating calculation
        expected_average = sum(ratings) / len(ratings)
        assert abs(stats_data["average_rating"] - expected_average) < 0.1

    async def test_get_review_stats_no_reviews(self, client):
        """Test getting review statistics for target with no reviews"""
        target_id = "non_existent_movie"
        
        stats_response = await client.get(f"/reviews/{target_id}/stats")
        
        assert stats_response.status_code == 200
        stats_data = stats_response.json()
        assert stats_data["average_rating"] == 0
        assert stats_data["total_reviews"] == 0
        assert all(count == 0 for count in stats_data["rating_distribution"].values())