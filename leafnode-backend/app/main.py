import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.auth.models import User
from app.auth.password import hash_password
from app.auth.router import router as auth_router
from app.config import settings
from app.database import AsyncSessionLocal
from app.influx_listener import influx_listener
from app.influx_client import InfluxDBManager
from app.routers import anomalies, plants, readings, commands
from app.services.mqtt_listener import mqtt_ack_listener

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers.update({
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; "
                "connect-src 'self'"
            ),
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        })
        return response


async def _ensure_admin_user() -> None:
    if not settings.ADMIN_PASSWORD:
        return
    from sqlalchemy import select
    from app.auth.password import verify_password
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.username == settings.ADMIN_USERNAME))
        user = result.scalar_one_or_none()
        if user is None:
            db.add(User(
                username=settings.ADMIN_USERNAME,
                password_hash=hash_password(settings.ADMIN_PASSWORD),
            ))
            await db.commit()
            logger.info("Created admin user '%s'", settings.ADMIN_USERNAME)
        elif not verify_password(settings.ADMIN_PASSWORD, user.password_hash):
            user.password_hash = hash_password(settings.ADMIN_PASSWORD)
            await db.commit()
            logger.info("Updated password for admin user '%s'", settings.ADMIN_USERNAME)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await _ensure_admin_user()
    task_influx = asyncio.create_task(influx_listener())
    task_mqtt = asyncio.create_task(mqtt_ack_listener())
    logger.info("InfluxDB and MQTT listeners started")
    try:
        yield
    finally:
        task_influx.cancel()
        task_mqtt.cancel()
        try:
            await asyncio.gather(task_influx, task_mqtt)
        except asyncio.CancelledError:
            pass
        logger.info("Background listeners stopped")
        await InfluxDBManager.close()
        logger.info("InfluxDB connection closed")


app = FastAPI(
    title="LeafNode",
    description="Plant monitoring backend",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
)

app.include_router(auth_router)
app.include_router(plants.router)
app.include_router(readings.router)
app.include_router(anomalies.router)
app.include_router(commands.router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error: %s %s", request.method, request.url.path)
    if settings.DEBUG:
        raise exc
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
