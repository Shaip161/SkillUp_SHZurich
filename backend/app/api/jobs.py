from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.database import get_db
from app.models.job import Job, JobListItem, JobRead
from app.rate_limit import limiter

router = APIRouter()


@router.get("/jobs", response_model=list[JobListItem])
@limiter.limit("60/hour")
async def list_jobs(
    request: Request,
    category: str | None = Query(None),
    seniority: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[Job]:
    stmt = select(Job).where(Job.expires_at > func.now())
    if category:
        stmt = stmt.where(Job.category == category)
    if seniority:
        stmt = stmt.where(Job.seniority == seniority)
    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/jobs/{job_id}", response_model=JobRead)
async def get_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
) -> Job:
    try:
        uid = UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")
    job = await db.get(Job, uid)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
