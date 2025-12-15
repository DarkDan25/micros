import logging

from fastapi import FastAPI, Request
from prometheus_client import Counter, Histogram, make_asgi_app
from .endpoints.user_router import user_router
from .database import init_db
import time

app = FastAPI(
    title="Users Service",
    description="Микросервис для управления пользователями и аутентификацией",
    version="1.1.0"
)

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"]
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"]
)

APP_INFO = Counter(
    "app_info",
    "Application information",
    ["app_name", "version"]
)
APP_INFO.labels(app_name="users-service", version="1.1.0").inc(0)

logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
def startup():
    init_db()

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "users"}

@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)

    route = request.scope.get("route")
    endpoint = route.path if route else request.url.path

    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=endpoint
    ).observe(time.time() - start_time)

    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=endpoint,
        status_code=str(response.status_code)
    ).inc()

    return response

async def log_requests(request: Request, call_next):
    body = await request.body()  # опционально, если нужен payload
    logger.info(f"Запрос: {request.method} {request.url.path} | Тело: {body.decode()}")
    response = await call_next(request)
    logger.info(f"Ответ: {response.status_code} для {request.method} {request.url.path}")
    return response

app.include_router(user_router, prefix="/api")

# 🔥 ВОТ ЭТО РЕШАЕТ 404
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
