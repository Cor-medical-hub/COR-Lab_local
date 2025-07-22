import asyncio
import time
import uvicorn
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from fastapi import FastAPI, Request, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from prometheus_client import Counter, Histogram

from prometheus_fastapi_instrumentator import PrometheusFastApiInstrumentator

from starlette.middleware.trustedhost import TrustedHostMiddleware


from fastapi_limiter import FastAPILimiter


from cor_lab.routes import auth, person
from cor_lab.database.db import get_db, async_session_maker
from cor_lab.database.redis_db import redis_client

from cor_lab.routes import (
    auth,
    cor_id,
    admin,
    lawyer,
    doctor,
    cases,
    samples,
    cassettes,
    glasses,
    dicom_router,
    printing_device,
    printer,
    websocket_events,
    svs_router,
    lab_assistants,
)
from cor_lab.config.config import settings
from loguru import logger
from cor_lab.services.auth import auth_service
from fastapi.responses import JSONResponse
from collections import defaultdict
from jose import JWTError, jwt

from cor_lab.services.logger import setup_logging

setup_logging()


all_licenses_info = [
    {
        "name": "IP2Location LITE Database License",
        "url": "https://lite.ip2location.com/",
        "description": "Используется для IP-геолокации. Требуется указание ссылки как часть условий лицензии.",
    },
    {
        "name": "OpenSlide (LGPL v2.1)",
        "url": "https://openslide.org/license/",
        "description": "Библиотека для чтения изображений с микроскопа. Распространяется под LGPL v2.1.",
    },
    {
        "name": "Psycopg (LGPL 3.0 / Modified BSD)",
        "url": "https://www.psycopg.org/docs/license.html",
        "description": "PostgreSQL адаптер для Python. Распространяется под двойной лицензией LGPL 3.0 или Modified BSD.",
    },
    {
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
        "description": "Многие компоненты API распространяются под разрешительной лицензией MIT.",
    },
    {
        "name": "Apache License 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0",
        "description": "Некоторые компоненты API распространяются под разрешительной лицензией Apache 2.0.",
    },
    {
        "name": "BSD 3-Clause License",
        "url": "https://opensource.org/licenses/BSD-3-Clause",
        "description": "Некоторые компоненты API распространяются под разрешительной лицензией BSD 3-Clause.",
    },
    {
        "name": "BSD 2-Clause License",
        "url": "https://opensource.org/licenses/BSD-2-Clause",
        "description": "Некоторые компоненты API распространяются под разрешительной лицензией BSD 2-Clause.",
    },
]

api_description = """
**COR-Lab_local API** - API CPR-Lab для развертывания локально в лаборатории

---

### Используемые лицензии:
"""
for lic in all_licenses_info:
    api_description += f"- **{lic['name']}**: [Подробнее]({lic['url']})"
    if "description" in lic:
        api_description += f" - {lic['description']}"
    api_description += "\n"

api_description += """
---
*Все торговые марки являются собственностью их соответствующих владельцев.*
"""

app = FastAPI(
    title="COR-Lab_local API",
    description=api_description,
    version="1.0.1",
    openapi_url="/openapi.json" if settings.app_env == "development" else None,
    docs_url="/docs" if settings.app_env == "development" else None,
    redoc_url="/redoc" if settings.app_env == "development" else None,
)


app.mount("/static", StaticFiles(directory="cor_lab/static"), name="static")


origins = settings.allowed_redirect_urls


PrometheusFastApiInstrumentator().instrument(app).expose(app, "/metrics")


REQUEST_COUNT = Counter("app_requests_total", "Total number of requests")
REQUEST_LATENCY = Histogram("app_request_latency_seconds", "Request latency")

# Middleware для CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Обработчики исключений
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    logger.error("An unhandled exception occurred", exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal Server Error"},
    )


@app.exception_handler(ValueError)
async def validation_exception_handler(request: Request, exc: ValueError):
    return JSONResponse(
        # logger.error(f"Произошла ошибка валидации: {str(exc)}"),
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Произошла ошибка валидации", "error": str(exc)},
    )


# Маршруты
@app.get("/config")
def read_config():
    return {"ENV": settings.app_env}


@app.get("/", name="Корень")
def read_root(request: Request):
    REQUEST_COUNT.inc()
    with REQUEST_LATENCY.time():
        return FileResponse("cor_lab/static/COR_ID/login.html")


@app.get("/api/healthchecker")
async def healthchecker(db: AsyncSession = Depends(get_db)):
    REQUEST_COUNT.inc()
    try:
        result = await db.execute(text("SELECT 1"))
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database is not configured correctly",
            )
        return {"message": "Welcome to FastApi, database work correctly"}
    except Exception as e:
        logger.error("Database connection error", exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error connecting to the database",
        )


app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)


# Middleware для добавления заголовка времени обработки
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["My-Process-Time"] = str(process_time)
    return response


# Middleware для фиксирования активных пользователей
@app.middleware("http")
async def track_active_users(request: Request, call_next):
    user_token = request.headers.get("Authorization")
    if user_token:
        token_parts = user_token.split(" ")
        if len(token_parts) >= 2:
            try:
                decoded_token = jwt.decode(
                    token_parts[1],
                    options={"verify_signature": False},
                    key=auth_service.SECRET_KEY,
                    algorithms=[auth_service.ALGORITHM],
                )
                oid = decoded_token.get("oid")
                await redis_client.set(oid, time.time())
            except JWTError:
                pass
    response = await call_next(request)
    return response


async def custom_identifier(request: Request) -> str:
    return request.client.host


# Событие при старте приложения
@app.on_event("startup")
async def startup():
    logger.info("------------- STARTUP --------------")
    await FastAPILimiter.init(redis_client, identifier=custom_identifier)



@app.on_event("shutdown")
async def shutdown_event():
    logger.info("------------- SHUTDOWN --------------")



auth_attempts = defaultdict(list)
blocked_ips = {}

app.include_router(auth.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(person.router, prefix="/api")
app.include_router(cor_id.router, prefix="/api")
app.include_router(lawyer.router, prefix="/api")
app.include_router(doctor.router, prefix="/api")
app.include_router(cases.router, prefix="/api")
app.include_router(samples.router, prefix="/api")
app.include_router(cassettes.router, prefix="/api")
app.include_router(glasses.router, prefix="/api")
app.include_router(dicom_router.router, prefix="/api")
app.include_router(svs_router.router, prefix="/api")
app.include_router(printing_device.router, prefix="/api")
app.include_router(printer.router, prefix="/api")
app.include_router(websocket_events.router, prefix="/api")
app.include_router(lab_assistants.router, prefix="/api")

if __name__ == "__main__":
    uvicorn.run(
        app="main:app",
        host="192.168.153.203",
        port=8005,
        log_level="info",
        access_log=True,
        reload=settings.reload,
    )
# 192.168.153.203
