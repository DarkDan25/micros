import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from app.models.movie import Movie, Session, OrderRequest, ScheduleUpdateRequest, UpdateMovieRequest
from app.services.movie_service import MovieService
from unittest.mock import Mock


@pytest.fixture
def mock_movie_repo():
    return Mock()


@pytest.fixture
def movie_service(mock_movie_repo):
    service = MovieService()
    service.movie_repo = mock_movie_repo
    return service


class TestMovieService:
    
    @pytest.mark.unit
    def test_get_all_movies(self, movie_service, mock_movie_repo):
        # Arrange
        mock_movies = [
            Movie(
                film_id=uuid4(),
                title="Movie 1",
                description="Description 1",
                duration_minutes=120,
                genre=["Action"],
                poster_url="https://example.com/movie1.jpg",
                created_at=datetime.now()
            ),
            Movie(
                film_id=uuid4(),
                title="Movie 2",
                description="Description 2",
                duration_minutes=150,
                genre=["Drama"],
                poster_url="https://example.com/movie2.jpg",
                created_at=datetime.now()
            )
        ]
        mock_movie_repo.get_all_movies.return_value = mock_movies
        
        # Act
        result = movie_service.get_all_movies()
        
        # Assert
        assert len(result) == 2
        assert result[0].title == "Movie 1"
        assert result[1].title == "Movie 2"
        mock_movie_repo.get_all_movies.assert_called_once()
    
    @pytest.mark.unit
    def test_get_movie_by_id_success(self, movie_service, mock_movie_repo):
        # Arrange
        movie_id = uuid4()
        mock_movie = Movie(
            film_id=movie_id,
            title="Test Movie",
            description="Test Description",
            duration_minutes=120,
            genre=["Action"],
            poster_url="https://example.com/test.jpg",
            created_at=datetime.now()
        )
        mock_movie_repo.get_movie_by_id.return_value = mock_movie
        
        # Act
        result = movie_service.get_movie_by_id(movie_id)
        
        # Assert
        assert result.film_id == movie_id
        assert result.title == "Test Movie"
        mock_movie_repo.get_movie_by_id.assert_called_once_with(movie_id)
    
    @pytest.mark.unit
    def test_get_movie_schedule_all(self, movie_service, mock_movie_repo):
        # Arrange
        mock_sessions = [
            Session(
                session_id=uuid4(),
                movie_id=uuid4(),
                start_time=datetime.now() + timedelta(hours=1),
                hall_name="Hall 1",
                available_seats=100,
                created_at=datetime.now()
            ),
            Session(
                session_id=uuid4(),
                movie_id=uuid4(),
                start_time=datetime.now() + timedelta(hours=2),
                hall_name="Hall 2",
                available_seats=80,
                created_at=datetime.now()
            )
        ]
        mock_movie_repo.get_schedule.return_value = mock_sessions
        
        # Act
        result = movie_service.get_movie_schedule()
        
        # Assert
        assert len(result) == 2
        mock_movie_repo.get_schedule.assert_called_once_with(None)
    
    @pytest.mark.unit
    def test_get_movie_schedule_by_movie_id(self, movie_service, mock_movie_repo):
        # Arrange
        movie_id = uuid4()
        mock_sessions = [
            Session(
                session_id=uuid4(),
                movie_id=movie_id,
                start_time=datetime.now() + timedelta(hours=1),
                hall_name="Hall 1",
                available_seats=100,
                created_at=datetime.now()
            )
        ]
        mock_movie_repo.get_schedule.return_value = mock_sessions
        
        # Act
        result = movie_service.get_movie_schedule(movie_id)
        
        # Assert
        assert len(result) == 1
        assert result[0].movie_id == movie_id
        mock_movie_repo.get_schedule.assert_called_once_with(movie_id)
    
    @pytest.mark.unit
    def test_get_session_by_id(self, movie_service, mock_movie_repo):
        # Arrange
        session_id = uuid4()
        mock_session = Session(
            session_id=session_id,
            movie_id=uuid4(),
            start_time=datetime.now() + timedelta(hours=1),
            hall_name="Hall 1",
            available_seats=100,
            created_at=datetime.now()
        )
        mock_movie_repo.get_session_by_id.return_value = mock_session
        
        # Act
        result = movie_service.get_session_by_id(session_id)
        
        # Assert
        assert result.session_id == session_id
        mock_movie_repo.get_session_by_id.assert_called_once_with(session_id)
    
    @pytest.mark.unit
    def test_update_schedule_success(self, movie_service, mock_movie_repo):
        # Arrange
        session_id = uuid4()
        mock_session = Session(
            session_id=session_id,
            movie_id=uuid4(),
            start_time=datetime.now() + timedelta(hours=1),
            hall_name="Old Hall",
            available_seats=100,
            created_at=datetime.now()
        )
        mock_movie_repo.get_session_by_id.return_value = mock_session
        mock_movie_repo.update_session.return_value = mock_session
        
        new_start_time = datetime.now() + timedelta(hours=2)
        request = ScheduleUpdateRequest(
            start_time=new_start_time,
            hall_name="New Hall"
        )
        
        # Act
        result = movie_service.update_schedule(session_id, request)
        
        # Assert
        assert result.start_time == new_start_time
        assert result.hall_name == "New Hall"
        assert result.updated_at is not None
        mock_movie_repo.get_session_by_id.assert_called_once_with(session_id)
        mock_movie_repo.update_session.assert_called_once()
    
    @pytest.mark.unit
    def test_create_order_success(self, movie_service, mock_movie_repo):
        # Arrange
        session_id = uuid4()
        user_id = uuid4()
        mock_session = Session(
            session_id=session_id,
            movie_id=uuid4(),
            start_time=datetime.now() + timedelta(hours=1),
            hall_name="Hall 1",
            available_seats=10,
            created_at=datetime.now()
        )
        mock_movie_repo.get_session_by_id.return_value = mock_session
        mock_movie_repo.update_session.return_value = mock_session
        
        request = OrderRequest(
            user_id=user_id,
            session_id=session_id,
            selected_seats=["A1", "A2"],
            ticket_count=2
        )
        
        # Act
        result = movie_service.create_order(request)
        
        # Assert
        assert result["status"] == "created"
        assert "order_id" in result
        assert result["total_amount"] == 1000  # 2 tickets * 500
        assert mock_session.available_seats == 8  # 10 - 2
        mock_movie_repo.get_session_by_id.assert_called_once_with(session_id)
        mock_movie_repo.update_session.assert_called_once()
    
    @pytest.mark.unit
    def test_create_order_insufficient_seats(self, movie_service, mock_movie_repo):
        # Arrange
        session_id = uuid4()
        user_id = uuid4()
        mock_session = Session(
            session_id=session_id,
            movie_id=uuid4(),
            start_time=datetime.now() + timedelta(hours=1),
            hall_name="Hall 1",
            available_seats=1,
            created_at=datetime.now()
        )
        mock_movie_repo.get_session_by_id.return_value = mock_session
        
        request = OrderRequest(
            user_id=user_id,
            session_id=session_id,
            selected_seats=["A1", "A2"],
            ticket_count=2
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Not enough available seats"):
            movie_service.create_order(request)
    
    @pytest.mark.unit
    def test_create_movie(self, movie_service, mock_movie_repo):
        # Arrange
        movie_id = uuid4()
        new_movie = Movie(
            film_id=movie_id,
            title="New Movie",
            description="New Description",
            duration_minutes=120,
            genre=["Comedy"],
            poster_url="https://example.com/new.jpg",
            created_at=datetime.now()
        )
        mock_movie_repo.create_movie.return_value = new_movie
        
        # Act
        result = movie_service.create_movie(new_movie)
        
        # Assert
        assert result.film_id == movie_id
        assert result.title == "New Movie"
        mock_movie_repo.create_movie.assert_called_once_with(new_movie)
    
    @pytest.mark.unit
    def test_update_movie_success(self, movie_service, mock_movie_repo):
        # Arrange
        movie_id = uuid4()
        mock_movie = Movie(
            film_id=movie_id,
            title="Old Title",
            description="Old Description",
            duration_minutes=120,
            genre=["Action"],
            poster_url="https://example.com/old.jpg",
            created_at=datetime.now()
        )
        mock_movie_repo.get_movie_by_id.return_value = mock_movie
        mock_movie_repo.update_movie.return_value = mock_movie
        
        request = UpdateMovieRequest(
            title="New Title",
            description="New Description"
        )
        
        # Act
        result = movie_service.update_movie(movie_id, request)
        
        # Assert
        assert result.title == "New Title"
        assert result.description == "New Description"
        assert result.updated_at is not None
        mock_movie_repo.get_movie_by_id.assert_called_once_with(movie_id)
        mock_movie_repo.update_movie.assert_called_once()
    
    @pytest.mark.unit
    def test_update_movie_partial(self, movie_service, mock_movie_repo):
        # Arrange
        movie_id = uuid4()
        mock_movie = Movie(
            film_id=movie_id,
            title="Old Title",
            description="Old Description",
            duration_minutes=120,
            genre=["Action"],
            poster_url="https://example.com/old.jpg",
            created_at=datetime.now()
        )
        mock_movie_repo.get_movie_by_id.return_value = mock_movie
        mock_movie_repo.update_movie.return_value = mock_movie
        
        request = UpdateMovieRequest(duration_minutes=150)
        
        # Act
        result = movie_service.update_movie(movie_id, request)
        
        # Assert
        assert result.duration_minutes == 150
        assert result.title == "Old Title"  # Should remain unchanged
        assert result.updated_at is not None
        mock_movie_repo.get_movie_by_id.assert_called_once_with(movie_id)
        mock_movie_repo.update_movie.assert_called_once()