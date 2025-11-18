import pytest
from uuid import uuid4
from datetime import datetime, timedelta


@pytest.mark.component
class TestMovieWorkflows:
    """Component tests for complete movie system workflows"""
    
    def test_complete_movie_booking_workflow(self, client):
        """Test complete movie booking workflow: browse -> select -> book -> verify"""
        
        # Step 1: Get all movies
        response = client.get("/api/movies")
        assert response.status_code == 200
        movies_data = response.json()
        assert len(movies_data["movies"]) > 0
        
        # Select first movie
        selected_movie = movies_data["movies"][0]
        movie_id = selected_movie["film_id"]
        
        # Step 2: Get movie details
        response = client.get(f"/api/movies/{movie_id}")
        assert response.status_code == 200
        movie_details = response.json()
        assert movie_details["film_id"] == movie_id
        assert "title" in movie_details
        assert "description" in movie_details
        
        # Step 3: Get movie schedule
        response = client.get(f"/api/movies/{movie_id}/schedule")
        assert response.status_code == 200
        schedule_data = response.json()
        assert len(schedule_data["schedule"]) > 0
        
        # Select first available session
        selected_session = schedule_data["schedule"][0]
        session_id = selected_session["session_id"]
        initial_available_seats = selected_session["available_seats"]
        
        # Step 4: Get session details
        response = client.get(f"/api/movies/sessions/{session_id}")
        assert response.status_code == 200
        session_details = response.json()
        assert session_details["session_id"] == session_id
        assert session_details["movie_id"] == movie_id
        
        # Step 5: Create order
        user_id = str(uuid4())
        ticket_count = 2
        order_data = {
            "user_id": user_id,
            "session_id": session_id,
            "selected_seats": ["A1", "A2"],
            "ticket_count": ticket_count
        }
        response = client.post("/api/movies/orders", json=order_data)
        assert response.status_code == 200
        order_response = response.json()
        assert "order_id" in order_response
        assert order_response["status"] == "created"
        assert order_response["total_amount"] == 1000  # 2 tickets * 500
        
        # Step 6: Verify seats were deducted
        response = client.get(f"/api/movies/sessions/{session_id}")
        assert response.status_code == 200
        updated_session = response.json()
        assert updated_session["available_seats"] == initial_available_seats - ticket_count
    
    def test_multiple_movie_booking_workflow(self, client):
        """Test booking multiple movies for same user"""
        user_id = str(uuid4())
        
        # Get all movies and their schedules
        response = client.get("/api/movies")
        movies_data = response.json()
        movies = movies_data["movies"][:2]  # Take first 2 movies
        
        orders = []
        
        for movie in movies:
            movie_id = movie["film_id"]
            
            # Get schedule for this movie
            response = client.get(f"/api/movies/{movie_id}/schedule")
            schedule_data = response.json()
            
            if len(schedule_data["schedule"]) > 0:
                session = schedule_data["schedule"][0]
                session_id = session["session_id"]
                
                # Create order for this movie
                order_data = {
                    "user_id": user_id,
                    "session_id": session_id,
                    "selected_seats": [f"A{len(orders) + 1}"],
                    "ticket_count": 1
                }
                response = client.post("/api/movies/orders", json=order_data)
                assert response.status_code == 200
                orders.append(response.json())
        
        # Verify all orders were created successfully
        assert len(orders) > 0
        for order in orders:
            assert order["status"] == "created"
            assert "order_id" in order
    
    def test_movie_schedule_update_workflow(self, client):
        """Test updating movie schedule and verifying bookings"""
        
        # Get first available session
        response = client.get("/api/movies/schedule")
        schedule_data = response.json()
        assert len(schedule_data["schedule"]) > 0
        
        original_session = schedule_data["schedule"][0]
        session_id = original_session["session_id"]
        original_start_time = original_session["start_time"]
        original_hall_name = original_session["hall_name"]
        
        # Update session schedule
        new_start_time = (datetime.now() + timedelta(days=2)).isoformat()
        new_hall_name = "Updated Hall Name"
        
        update_data = {
            "start_time": new_start_time,
            "hall_name": new_hall_name
        }
        response = client.put(f"/api/movies/sessions/{session_id}/schedule", json=update_data)
        assert response.status_code == 200
        updated_session = response.json()
        
        # Verify update was applied
        assert updated_session["start_time"] == new_start_time
        assert updated_session["hall_name"] == new_hall_name
        assert updated_session["session_id"] == session_id
        
        # Verify booking still works with updated session
        user_id = str(uuid4())
        order_data = {
            "user_id": user_id,
            "session_id": session_id,
            "selected_seats": ["B1", "B2"],
            "ticket_count": 2
        }
        response = client.post("/api/movies/orders", json=order_data)
        assert response.status_code == 200
    
    def test_movie_creation_and_booking_workflow(self, client):
        """Test creating a new movie and booking tickets for it"""
        
        # Step 1: Create new movie
        movie_data = {
            "film_id": str(uuid4()),
            "title": "New Test Movie",
            "description": "A brand new test movie for workflow testing",
            "duration_minutes": 135,
            "genre": ["Comedy", "Romance"],
            "poster_url": "https://example.com/new-test-movie.jpg"
        }
        response = client.post("/api/movies", json=movie_data)
        assert response.status_code == 200
        created_movie = response.json()
        movie_id = created_movie["film_id"]
        
        # Step 2: Verify movie was created
        response = client.get(f"/api/movies/{movie_id}")
        assert response.status_code == 200
        retrieved_movie = response.json()
        assert retrieved_movie["title"] == "New Test Movie"
        assert retrieved_movie["duration_minutes"] == 135
        
        # Step 3: Create session for this movie (would need session creation endpoint)
        # For now, we'll assume sessions are created automatically or through admin
        
        # Step 4: Get movie schedule (should include our new movie)
        response = client.get("/api/movies/schedule")
        assert response.status_code == 200
        all_sessions = response.json()["schedule"]
        
        # Find sessions for our new movie
        movie_sessions = [s for s in all_sessions if s["movie_id"] == movie_id]
        
        if len(movie_sessions) > 0:
            # Step 5: Book tickets for the new movie
            session_id = movie_sessions[0]["session_id"]
            user_id = str(uuid4())
            order_data = {
                "user_id": user_id,
                "session_id": session_id,
                "selected_seats": ["C1", "C2"],
                "ticket_count": 2
            }
            response = client.post("/api/movies/orders", json=order_data)
            assert response.status_code == 200
    
    def test_seat_availability_workflow(self, client):
        """Test seat availability management during bookings"""
        
        # Get first available session
        response = client.get("/api/movies/schedule")
        schedule_data = response.json()
        assert len(schedule_data["schedule"]) > 0
        
        session = schedule_data["schedule"][0]
        session_id = session["session_id"]
        initial_seats = session["available_seats"]
        
        # Create multiple orders to test seat deduction
        user_ids = [str(uuid4()) for _ in range(3)]
        orders = []
        
        for i, user_id in enumerate(user_ids):
            order_data = {
                "user_id": user_id,
                "session_id": session_id,
                "selected_seats": [f"D{i+1}"],
                "ticket_count": 1
            }
            response = client.post("/api/movies/orders", json=order_data)
            assert response.status_code == 200
            orders.append(response.json())
        
        # Verify all orders were created
        assert len(orders) == 3
        
        # Check final seat availability
        response = client.get(f"/api/movies/sessions/{session_id}")
        final_session = response.json()
        assert final_session["available_seats"] == initial_seats - 3
    
    def test_error_handling_workflow(self, client):
        """Test error handling in various scenarios"""
        
        # Test 1: Invalid movie ID
        invalid_movie_id = "invalid-uuid-format"
        response = client.get(f"/api/movies/{invalid_movie_id}")
        assert response.status_code == 422
        
        # Test 2: Invalid session ID
        invalid_session_id = "invalid-uuid-format"
        response = client.get(f"/api/movies/sessions/{invalid_session_id}")
        assert response.status_code == 422
        
        # Test 3: Order with insufficient seats
        response = client.get("/api/movies/schedule")
        schedule_data = response.json()
        
        if len(schedule_data["schedule"]) > 0:
            session = schedule_data["schedule"][0]
            session_id = session["session_id"]
            
            # Try to book more seats than available
            order_data = {
                "user_id": str(uuid4()),
                "session_id": session_id,
                "selected_seats": ["A1"] * 1000,  # Too many seats
                "ticket_count": 1000
            }
            response = client.post("/api/movies/orders", json=order_data)
            assert response.status_code == 400
            assert "Not enough available seats" in response.text
        
        # Test 4: Invalid movie data for creation
        invalid_movie_data = {
            "film_id": str(uuid4()),
            "title": "Test Movie",
            "duration_minutes": -10,  # Invalid duration
            "genre": ["Action"]
        }
        response = client.post("/api/movies", json=invalid_movie_data)
        assert response.status_code == 422