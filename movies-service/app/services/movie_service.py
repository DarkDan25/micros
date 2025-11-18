from uuid import UUID, uuid4
from datetime import datetime, timedelta
from ..models.movie import Movie, Session, OrderRequest, ScheduleUpdateRequest, UpdateMovieRequest
from ..repositories.db_movie_repo import MovieRepo


class MovieService:
    def __init__(self):
        self.movie_repo = MovieRepo()

    def get_all_movies(self) -> list[Movie]:
        return self.movie_repo.get_all_movies()

    def get_movie_by_id(self, movie_id: UUID) -> Movie:
        return self.movie_repo.get_movie_by_id(movie_id)

    def get_movie_schedule(self, movie_id: UUID = None) -> list[Session]:
        return self.movie_repo.get_schedule(movie_id)

    def get_session_by_id(self, session_id: UUID) -> Session:
        return self.movie_repo.get_session_by_id(session_id)

    def update_schedule(self, session_id: UUID, request: ScheduleUpdateRequest) -> Session:
        session = self.movie_repo.get_session_by_id(session_id)
        session.start_time = request.start_time
        session.hall_name = request.hall_name
        session.updated_at = datetime.now()

        return self.movie_repo.update_session(session)

    def create_order(self, request: OrderRequest) -> dict:
        session = self.movie_repo.get_session_by_id(request.session_id)

        if session.available_seats < request.ticket_count:
            raise ValueError("Not enough available seats")

        # Обновляем доступные места
        session.available_seats -= request.ticket_count
        self.movie_repo.update_session(session)

        # Расчет стоимости
        ticket_price = 500  # Базовая цена
        total_amount = ticket_price * request.ticket_count

        return {
            "order_id": uuid4(),
            "status": "created",
            "total_amount": total_amount
        }

    def create_movie(self, movie: Movie) -> Movie:
        return self.movie_repo.create_movie(movie)

    def update_movie(self, movie_id: UUID, request: UpdateMovieRequest) -> Movie:
        movie = self.movie_repo.get_movie_by_id(movie_id)

        update_data = request.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(movie, key, value)

        movie.updated_at = datetime.now()

        return self.movie_repo.update_movie(movie)

    def add_sample_data(self):
        # Проверяем, есть ли уже данные
        existing_movies = self.movie_repo.get_all_movies()
        if existing_movies:
            return

        # Добавляем тестовые фильмы
        movies = [
            Movie(
                film_id=uuid4(),
                title="Аватар: Путь воды",
                description="Фантастический боевик о приключениях на планете Пандора",
                duration_minutes=192,
                genre=["фантастика", "боевик", "приключения"],
                poster_url="https://example.com/avatar2.jpg",
                created_at=datetime.now()
            ),
            Movie(
                film_id=uuid4(),
                title="Оппенгеймер",
                description="Биографический фильм о создателе атомной бомбы",
                duration_minutes=180,
                genre=["биография", "история", "драма"],
                poster_url="https://example.com/oppenheimer.jpg",
                created_at=datetime.now()
            )
        ]

        for movie in movies:
            self.movie_repo.create_movie(movie)

        # Добавляем тестовые сеансы
        sessions = []
        for movie in movies:
            for i in range(3):
                session = Session(
                    session_id=uuid4(),
                    movie_id=movie.film_id,
                    start_time=datetime.now() + timedelta(days=i, hours=18),
                    hall_name=f"Зал {i + 1}",
                    available_seats=100,
                    created_at=datetime.now()
                )
                sessions.append(session)
                self.movie_repo.create_session(session)