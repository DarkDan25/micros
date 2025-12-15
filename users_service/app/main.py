from fastapi import FastAPI
from .endpoints.user_router import user_router
from .database import init_db
app = FastAPI(
    title="Users Service",
    description="Микросервис для управления пользователями и аутентификацией",
    version="1.0.0"
)

@app.on_event("startup")
def startup():
    init_db()

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "users"}

app.include_router(user_router, prefix='/api')