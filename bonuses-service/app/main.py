from fastapi import FastAPI
from .endpoints.bonus_router import bonus_router
from .database import init_db

app = FastAPI(
    title="Bonuses Service",
    description="Микросервис для управления бонусной системой",
    version="1.0.0"
)

@app.on_event("startup")
def startup():
    init_db()

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "bonuses"}

app.include_router(bonus_router, prefix='/api')