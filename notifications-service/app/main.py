from fastapi import FastAPI
from .endpoints.notification_router import notification_router
from .database import init_db

app = FastAPI(
    title="Notifications Service",
    description="Микросервис для управления уведомлениями",
    version="1.0.0"
)

@app.on_event("startup")
def startup():
    init_db()

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "notifications"}

app.include_router(notification_router, prefix='/api')