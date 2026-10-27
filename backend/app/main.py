import logging
from typing import Any

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.confirmations import router as confirmations_router
from app.api.discussions import router as discussions_router
from app.api.models import router as models_router
from app.api.projects import router as projects_router
from app.api.providers import router as providers_router
from app.api.roles import router as roles_router
from app.core.config import settings
from app.db.session import check_db_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(auth_router, prefix="/api")
app.include_router(projects_router, prefix="/api")
app.include_router(providers_router, prefix="/api")
app.include_router(models_router, prefix="/api")
app.include_router(roles_router, prefix="/api")
app.include_router(discussions_router, prefix="/api")
app.include_router(confirmations_router, prefix="/api")


async def check_redis_connection() -> bool:
    """Check whether Redis is reachable."""
    try:
        client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        pong = await client.ping()
        await client.aclose()
        return bool(pong)
    except Exception as exc:
        logger.warning("Redis connection check failed: %s", exc)
        return False


@app.get("/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint reporting database and redis connectivity."""
    db_ok = await check_db_connection()
    redis_ok = await check_redis_connection()
    status_str = "ok" if (db_ok and redis_ok) else "degraded"

    return {
        "status": status_str,
        "database": "connected" if db_ok else "disconnected",
        "redis": "connected" if redis_ok else "disconnected",
    }


@app.get("/version")
async def get_version() -> dict[str, str]:
    """Return backend service name and version."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
    }
