import pytest
from uuid import uuid4
from datetime import datetime, timedelta


@pytest.mark.integration
class TestMovieEndpoints:
    
    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "service": "movies"}
    
    def test_get_all_movies(self, client):
        response = client.get("/api/movies")
        assert response.status_code == 200
        data = response.json()
        assert "movies" in data
        assert isinstance(data["movies"], list)
    
    def test_get_movie_by_id(self, client):
        # First get all movies to find a valid ID
        response = client.get("/api/movies")
        movies = response.json()["movies"]
        
        if movies:
            movie_id = movies[0]["film_id"]
            response = client.get(f"/api/movies/{movie_id}")
            assert response.status_code == 200
            movie = response.json()
            assert movie["film_id"] == movie_id
            assert "title" in movie
            assert "description" in movie
    
    def test_get_movie_schedule_all(self, client):
        response = client.get("/api/movies/schedule")
        assert response.status_code == 200
        data = response.json()
        assert "schedule" in data
        assert isinstance(data["schedule"], list)
    
    def test_get_movie_schedule_by_movie_id(self, client):
        # First get all movies to find a valid ID
        response = client.get("/api/movies")
        movies = response.json()["movies"]
        
        if movies:
            movie_id = movies[0]["film_id"]
            response = client.get(f"/api/movies/{movie_id}/schedule")
            assert response.status_code == 200
            data = response.json()
            assert "schedule" in data
            assert isinstance(data["schedule"], list)
    
    def test_get_session_by_id(self, client):
        # First get schedule to find a valid session ID
        response = client.get("/api/movies/schedule")
        sessions = response.json()["schedule"]
        
        if sessions:
            session_id = sessions[0]["session_id"]
            response = client.get(f"/api/movies/sessions/{session_id}")
            assert response.status_code == 200
            session = response.json()
            assert session["session_id"] == session_id
            assert "movie_id" in session
            assert "start_time" in session
    
    def test_create_order_success(self, client):
        # First get schedule to find a valid session
        response = client.get("/api/movies/schedule")
        sessions = response.json()["schedule"]
        
        if sessions:
            session_id = sessions[0]["session_id"]
            order_data = {
                "user_id": str(uuid4()),
                "session_id": session_id,
                "selected_seats": ["A1", "A2"],
                "ticket_count": 2
            }
            response = client.post("/api/movies/orders", json=order_data)
            assert response.status_code == 200
            order = response.json()
            assert "order_id" in order
            assert order["status"] == "created"
            assert "total_amount" in order
    
    def test_create_order_insufficient_seats(self, client):
        # First get schedule to find a valid session
        response = client.get("/api/movies/schedule")
        sessions = response.json()["schedule"]
        
        if sessions:
            session_id = sessions[0]["session_id"]
            order_data = {
                "user_id": str(uuid4()),
                "session_id": session_id,
                "selected_seats": ["A1", "A2", "A3", "A4", "A5"],
                "ticket_count": 1000  # More than available
            }
            response = client.post("/api/movies/orders", json=order_data)
            assert response.status_code == 400
            assert "Not enough available seats" in response.text
    
    def test_update_schedule(self, client):
        # First get schedule to find a valid session
        response = client.get("/api/movies/schedule")
        sessions = response.json()["schedule"]
        
        if sessions:
            session_id = sessions[0]["session_id"]
            update_data = {
                "start_time": (datetime.now() + timedelta(days=1)).isoformat(),
                "hall_name": "Updated Hall"
            }
            response = client.put(f"/api/movies/sessions/{session_id}/schedule", json=update_data)
            assert response.status_code == 200
            session = response.json()
            assert session["session_id"] == session_id
            assert session["hall_name"] == "Updated Hall"
    
    def test_create_movie(self, client):
        movie_data = {
            "film_id": str(uuid4()),
            "title": "Test Movie",
            "description": "A test movie for testing",
            "duration_minutes": 120,
            "genre": ["Action", "Adventure"],
            "poster_url": "https://example.com/test-movie.jpg"
        }
        response = client.post("/api/movies", json=movie_data)
        assert response.status_code == 200
        movie = response.json()
        assert movie["title"] == "Test Movie"
        assert movie["duration_minutes"] == 120
        assert "Action" in movie["genre"]
    
    def test_update_movie(self, client):
        # First get all movies to find a valid ID
        response = client.get("/api/movies")
        movies = response.json()["movies"]
        
        if movies:
            movie_id = movies[0]["film_id"]
            update_data = {
                "title": "Updated Movie Title",
                "duration_minutes": 150
            }
            response = client.put(f"/api/movies/{movie_id}", json=update_data)
            assert response.status_code == 200
            movie = response.json()
            assert movie["film_id"] == movie_id
            assert movie["title"] == "Updated Movie Title"
            assert movie["duration_minutes"] == 150
    
    def test_invalid_movie_id_format(self, client):
        response = client.get("/api/movies/invalid-uuid")
        assert response.status_code == 422  # Validation error
    
    def test_invalid_session_id_format(self, client):
        response = client.get("/api/movies/sessions/invalid-uuid")
        assert response.status_code == 422     
    
    def test_missing_required_fields_in_order(self, client):
        order_data = {
            "user_id": str(uuid4()),
            "session_id": str(uuid4())
            # Missing selected_seats and ticket_count
        }
        response = client.post("/api/movies/orders", json=order_data)
        assert response.status_code == 422
    
    def test_invalid_movie_data(self, client):
        movie_data = {
            "film_id": str(uuid4()),
            "title": "Test Movie",
            "duration_minutes": -10,  # Invalid duration
            "genre": ["Action"]
        }
        response = client.post("/api/movies", json=movie_data)
        assert response.status_code == 422