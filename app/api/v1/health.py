import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db


router = APIRouter()


@router.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
    }


@router.get("/health/deep", tags=["System"])
async def deep_health_check(db: AsyncSession = Depends(get_db)):
    db_status = "unhealthy"
    redis_status = "unhealthy"

    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as error:
        db_status = f"error: {error}"

    redis_client = aioredis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
    try:
        if await redis_client.ping():
            redis_status = "connected"
    except Exception as error:
        redis_status = f"error: {error}"
    finally:
        await redis_client.aclose()

    all_ok = db_status == "connected" and redis_status == "connected"
    http_code = status.HTTP_200_OK if all_ok else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=http_code,
        content={
            "status": "operational" if all_ok else "degraded",
            "database": db_status,
            "redis": redis_status,
            "version": settings.VERSION,
        },
    )