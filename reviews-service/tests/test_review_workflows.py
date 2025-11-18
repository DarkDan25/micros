import pytest
import asyncio
from uuid import uuid4
from datetime import datetime, timedelta
from httpx import AsyncClient
from app.models.review import Review, ReviewStatus


@pytest.mark.component
@pytest.mark.asyncio
class TestReviewWorkflows:
    """Component tests for complete review workflows"""

    async def test_complete_review_lifecycle(self, client, sample_user_id, sample_target_id):
        """Test complete review lifecycle from creation to deletion"""
        # Step 1: Create a review
        create_request = {
            "target_id": sample_target_id,
            "rating": 8,
            "text": "Amazing movie with great acting and storyline!"
        }
        
        create_response = await client.post(
            f"/reviews/?user_id={sample_user_id}",
            json=create_request
        )
        
        assert create_response.status_code == 200
        create_data = create_response.json()
        review_id = create_data["id"]
        
        # Verify review was created with correct data
        assert create_data["user_id"] == str(sample_user_id)
        assert create_data["target_id"] == sample_target_id
        assert create_data["rating"] == 8
        assert create_data["text"] == create_request["text"]
        assert create_data["status"] == "active"
        assert create_data["created_at"] is not None
        assert create_data["updated_at"] is None
        
        # Step 2: Update the review
        update_request = {
            "rating": 9,
            "text": "Even better after second viewing!"
        }
        
        update_response = await client.put(
            f"/reviews/{review_id}?user_id={sample_user_id}",
            json=update_request
        )
        
        assert update_response.status_code == 200
        update_data = update_response.json()
        assert update_data["id"] == review_id
        assert update_data["rating"] == 9
        assert update_data["text"] == update_request["text"]
        assert update_data["updated_at"] is not None
        assert update_data["status"] == "active"
        
        # Step 3: Verify review appears in target's reviews
        target_reviews_response = await client.get(f"/reviews/?target_id={sample_target_id}")
        assert target_reviews_response.status_code == 200
        target_reviews_data = target_reviews_response.json()
        assert len(target_reviews_data["items"]) == 1
        assert target_reviews_data["items"][0]["id"] == review_id
        
        # Step 4: Delete the review
        delete_response = await client.delete(
            f"/reviews/{review_id}?user_id={sample_user_id}"
        )
        
        assert delete_response.status_code == 200
        delete_data = delete_response.json()
        assert delete_data["status"] == "deleted"

    async def test_multiple_user_reviews_workflow(self, client, sample_target_id):
        """Test workflow with multiple users reviewing the same target"""
        num_users = 5
        user_ids = [uuid4() for _ in range(num_users)]
        created_reviews = []
        
        # Create reviews from multiple users
        for i, user_id in enumerate(user_ids):
            create_request = {
                "target_id": sample_target_id,
                "rating": 6 + i,  # Ratings: 6, 7, 8, 9, 10
                "text": f"Review from user {i+1}"
            }
            
            create_response = await client.post(
                f"/reviews/?user_id={user_id}",
                json=create_request
            )
            
            assert create_response.status_code == 200
            review_data = create_response.json()
            created_reviews.append(review_data)
            
            # Verify review was created
            assert review_data["user_id"] == str(user_id)
            assert review_data["target_id"] == sample_target_id
            assert review_data["rating"] == 6 + i
        
        # Verify all reviews appear in target's reviews
        target_reviews_response = await client.get(f"/reviews/?target_id={sample_target_id}")
        assert target_reviews_response.status_code == 200
        target_reviews_data = target_reviews_response.json()
        assert len(target_reviews_data["items"]) == num_users
        
        # Verify review statistics
        stats_response = await client.get(f"/reviews/{sample_target_id}/stats")
        assert stats_response.status_code == 200
        stats_data = stats_response.json()
        assert stats_data["total_reviews"] == num_users
        assert stats_data["average_rating"] == 8.0  # (6+7+8+9+10)/5 = 8.0

    async def test_review_prevention_workflow(self, client, sample_user_id, sample_target_id):
        """Test that users cannot create multiple reviews for the same target"""
        # Create first review
        first_review_request = {
            "target_id": sample_target_id,
            "rating": 7,
            "text": "First review"
        }
        
        first_response = await client.post(
            f"/reviews/?user_id={sample_user_id}",
            json=first_review_request
        )
        
        assert first_response.status_code == 200
        first_review_data = first_response.json()
        
        # Try to create second review for same target
        second_review_request = {
            "target_id": sample_target_id,
            "rating": 9,
            "text": "Second review attempt"
        }
        
        second_response = await client.post(
            f"/reviews/?user_id={sample_user_id}",
            json=second_review_request
        )
        
        assert second_response.status_code == 400
        assert "already reviewed" in second_response.json()["detail"]
        
        # Verify only first review exists
        target_reviews_response = await client.get(f"/reviews/?target_id={sample_target_id}")
        target_reviews_data = target_reviews_response.json()
        assert len(target_reviews_data["items"]) == 1
        assert target_reviews_data["items"][0]["id"] == first_review_data["id"]

    async def test_concurrent_review_creation(self, client, sample_target_id):
        """Test concurrent review creation to ensure data consistency"""
        num_concurrent = 5
        user_ids = [uuid4() for _ in range(num_concurrent)]
        
        async def create_review(user_id, rating):
            create_request = {
                "target_id": sample_target_id,
                "rating": rating,
                "text": f"Concurrent review by user {user_id}"
            }
            
            response = await client.post(
                f"/reviews/?user_id={user_id}",
                json=create_request
            )
            return response
        
        # Run concurrent review creation
        tasks = [
            create_review(user_ids[i], 6 + i)
            for i in range(num_concurrent)
        ]
        
        responses = await asyncio.gather(*tasks)
        
        # Verify all requests were successful
        successful_reviews = 0
        for response in responses:
            if response.status_code == 200:
                successful_reviews += 1
        
        assert successful_reviews == num_concurrent
        
        # Verify all reviews appear in target's reviews
        target_reviews_response = await client.get(f"/reviews/?target_id={sample_target_id}")
        target_reviews_data = target_reviews_response.json()
        assert len(target_reviews_data["items"]) == num_concurrent

    async def test_review_permissions_workflow(self, client, sample_target_id):
        """Test review permissions - users can only edit/delete their own reviews"""
        # Create review with user1
        user1_id = uuid4()
        create_request = {
            "target_id": sample_target_id,
            "rating": 8,
            "text": "Review by user1"
        }
        
        create_response = await client.post(
            f"/reviews/?user_id={user1_id}",
            json=create_request
        )
        assert create_response.status_code == 200
        review_data = create_response.json()
        review_id = review_data["id"]
        
        # Try to update review with user2 (should fail)
        user2_id = uuid4()
        update_request = {
            "rating": 9,
            "text": "Updated by user2 (should fail)"
        }
        
        update_response = await client.put(
            f"/reviews/{review_id}?user_id={user2_id}",
            json=update_request
        )
        assert update_response.status_code == 403
        assert "can only edit their own reviews" in update_response.json()["detail"]
        
        # Try to delete review with user2 (should fail)
        delete_response = await client.delete(
            f"/reviews/{review_id}?user_id={user2_id}"
        )
        assert delete_response.status_code == 403
        assert "can only delete their own reviews" in delete_response.json()["detail"]
        
        # Verify original user can still update
        valid_update_response = await client.put(
            f"/reviews/{review_id}?user_id={user1_id}",
            json=update_request
        )
        assert valid_update_response.status_code == 200

    async def test_review_statistics_workflow(self, client):
        """Test review statistics calculation with various ratings"""
        target_id = f"stats_movie_{uuid4()}"
        
        # Create reviews with specific ratings for predictable statistics
        ratings_distribution = {
            1: 1, 2: 2, 3: 3, 4: 4, 5: 5,
            6: 4, 7: 3, 8: 2, 9: 1, 10: 1
        }
        
        for rating, count in ratings_distribution.items():
            for i in range(count):
                user_id = uuid4()
                create_request = {
                    "target_id": target_id,
                    "rating": rating,
                    "text": f"Review with rating {rating} #{i+1}"
                }
                
                create_response = await client.post(
                    f"/reviews/?user_id={user_id}",
                    json=create_request
                )
                assert create_response.status_code == 200
        
        # Get statistics
        stats_response = await client.get(f"/reviews/{target_id}/stats")
        assert stats_response.status_code == 200
        stats_data = stats_response.json()
        
        # Verify total reviews
        total_reviews = sum(ratings_distribution.values())
        assert stats_data["total_reviews"] == total_reviews
        
        # Verify average rating calculation
        total_rating_sum = sum(rating * count for rating, count in ratings_distribution.items())
        expected_average = total_rating_sum / total_reviews
        assert abs(stats_data["average_rating"] - expected_average) < 0.1
        
        # Verify rating distribution
        for rating in range(1, 11):
            expected_count = ratings_distribution.get(rating, 0)
            actual_count = stats_data["rating_distribution"][str(rating)]
            assert actual_count == expected_count

    async def test_review_pagination_workflow(self, client, sample_user_id):
        """Test review pagination functionality"""
        target_id = f"pagination_movie_{uuid4()}"
        total_reviews = 25
        
        # Create multiple reviews (with different users to avoid duplicates)
        for i in range(total_reviews):
            user_id = uuid4()
            create_request = {
                "target_id": target_id,
                "rating": 5 + (i % 6),  # Ratings from 5 to 10
                "text": f"Review {i+1} for pagination testing"
            }
            
            create_response = await client.post(
                f"/reviews/?user_id={user_id}",
                json=create_request
            )
            assert create_response.status_code == 200
        
        # Test first page
        page1_response = await client.get(f"/reviews/?target_id={target_id}&page=1&page_size=10")
        assert page1_response.status_code == 200
        page1_data = page1_response.json()
        assert len(page1_data["items"]) == 10
        assert page1_data["page"] == 1
        assert page1_data["total_items"] == total_reviews
        assert page1_data["total_pages"] == 3
        
        # Test second page
        page2_response = await client.get(f"/reviews/?target_id={target_id}&page=2&page_size=10")
        assert page2_response.status_code == 200
        page2_data = page2_response.json()
        assert len(page2_data["items"]) == 10
        assert page2_data["page"] == 2
        
        # Test last page
        page3_response = await client.get(f"/reviews/?target_id={target_id}&page=3&page_size=10")
        assert page3_response.status_code == 200
        page3_data = page3_response.json()
        assert len(page3_data["items"]) == 5  # Remaining items
        assert page3_data["page"] == 3

    async def test_review_error_handling_workflow(self, client, sample_user_id, sample_target_id):
        """Test error handling in review workflows"""
        # Test invalid rating
        invalid_rating_response = await client.post(
            f"/reviews/?user_id={sample_user_id}",
            json={"target_id": sample_target_id, "rating": 15, "text": "Invalid rating"}
        )
        assert invalid_rating_response.status_code == 422
        
        # Test missing user_id
        missing_user_response = await client.post(
            "/reviews/",
            json={"target_id": sample_target_id, "rating": 8, "text": "Missing user"}
        )
        assert missing_user_response.status_code == 422
        
        # Test update with non-existent review
        nonexistent_update_response = await client.put(
            f"/reviews/{uuid4()}?user_id={sample_user_id}",
            json={"rating": 9, "text": "Update non-existent"}
        )
        assert nonexistent_update_response.status_code == 404
        
        # Test delete with non-existent review
        nonexistent_delete_response = await client.delete(
            f"/reviews/{uuid4()}?user_id={sample_user_id}"
        )
        assert nonexistent_delete_response.status_code == 404