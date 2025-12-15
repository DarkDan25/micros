from fastapi import FastAPI
from .endpoints.payment_router import payment_router
from .database import init_db

app = FastAPI(
    title="Payments Service",
    description="Микросервис для управления оплатами",
    version="1.0.0"
)

@app.on_event("startup")
def startup():
    init_db()

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "payments"}

app.include_router(payment_router, prefix='/api')