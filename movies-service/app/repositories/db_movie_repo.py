from uuid import UUID
from sqlalchemy.orm import Session as SASession
from ..database import get_db
from ..models.movie import Movie, Session
from ..schemas.movie import Movie as DBMovie, Session as DBSession


class MovieRepo:
    def __init__(self):
        self.db: SASession = next(get_db())

    def get_all_movies(self) -> list[Movie]:
        movies = self.db.query(DBMovie).all()
        return [Movie.from_orm(movie) for movie in movies]

    def get_movie_by_id(self, movie_id: UUID) -> Movie:
        movie = self.db.query(DBMovie).filter(DBMovie.film_id == movie_id).first()
        if movie is None:
            raise KeyError(f"Movie with id={movie_id} not found")
        return Movie.from_orm(movie)

    def get_schedule(self, movie_id: UUID = None) -> list[Session]:
        query = self.db.query(DBSession)
        if movie_id:
            query = query.filter(DBSession.movie_id == movie_id)

        sessions = query.all()
        return [Session.from_orm(session) for session in sessions]

    def get_session_by_id(self, session_id: UUID) -> Session:
        session = self.db.query(DBSession).filter(DBSession.session_id == session_id).first()
        if session is None:
            raise KeyError(f"Session with id={session_id} not found")
        return Session.from_orm(session)

    def create_movie(self, movie: Movie) -> Movie:
        db_movie = DBMovie(**movie.dict())
        self.db.add(db_movie)
        self.db.commit()
        self.db.refresh(db_movie)
        return Movie.from_orm(db_movie)

    def create_session(self, session: Session) -> Session:
        db_session = DBSession(**session.dict())
        self.db.add(db_session)
        self.db.commit()
        self.db.refresh(db_session)
        return Session.from_orm(db_session)

    def update_movie(self, movie: Movie) -> Movie:
        db_movie = self.db.query(DBMovie).filter(DBMovie.film_id == movie.film_id).first()
        if db_movie is None:
            raise KeyError(f"Movie with id={movie.film_id} not found")

        for key, value in movie.dict().items():
            setattr(db_movie, key, value)

        self.db.commit()
        self.db.refresh(db_movie)
        return Movie.from_orm(db_movie)

    def update_session(self, session: Session) -> Session:
        db_session = self.db.query(DBSession).filter(DBSession.session_id == session.session_id).first()
        if db_session is None:
            raise KeyError(f"Session with id={session.session_id} not found")

        for key, value in session.dict().items():
            setattr(db_session, key, value)

        self.db.commit()
        self.db.refresh(db_session)
        return Session.from_orm(db_session)