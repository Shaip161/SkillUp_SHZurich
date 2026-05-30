from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db

router = APIRouter()


@router.get("/health")
async def health(db: AsyncSession = Depends(get_db)) -> JSONResponse:
    results: dict[str, str] = {}

    try:
        await db.execute(text("SELECT 1"))
        results["db"] = "ok"
    except Exception as exc:
        results["db"] = f"error: {exc}"

    try:
        r = Redis.from_url(settings.redis_url, socket_connect_timeout=2)
        await r.ping()
        await r.aclose()
        results["redis"] = "ok"
    except Exception as exc:
        results["redis"] = f"error: {exc}"

    status = "ok" if all(v == "ok" for v in results.values()) else "degraded"
    return JSONResponse(
        content={"status": status, **results},
        status_code=200 if status == "ok" else 503,
    )
