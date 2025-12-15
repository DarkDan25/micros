from fastapi import FastAPI
from .endpoints.review_router import review_router
from .database import init_db

app = FastAPI(
    title="Reviews Service",
    description="Микросервис для управления отзывами о фильмах",
    version="1.0.0"
)

@app.on_event("startup")
def startup():
    init_db()

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "reviews"}

app.include_router(review_router, prefix='/api')