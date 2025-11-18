from fastapi import FastAPI
from .endpoints.movie_router import movie_router
from .database import init_db

app = FastAPI(
    title="Movies Service",
    description="Микросервис для управления фильмами и расписанием",
    version="1.0.0"
)

@app.on_event("startup")
def startup():
    init_db()
    # Добавляем тестовые данные
    from .services.movie_service import MovieService
    movie_service = MovieService()
    movie_service.add_sample_data()

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "movies"}

app.include_router(movie_router, prefix='/api')