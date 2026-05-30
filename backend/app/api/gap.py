from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.job import Job
from app.models.user import UserProfile
from app.services.matcher import compute_gap

router = APIRouter()


class GapRequest(BaseModel):
    user_id: str


class GapResponse(BaseModel):
    job_id: str
    user_id: str
    required_skills: list[str]
    user_skills: list[str]
    missing_skills: list[str]
    matched_skills: list[str]


@router.post("/gap/{job_id}", response_model=GapResponse)
async def get_skill_gap(
    job_id: str,
    body: GapRequest,
    db: AsyncSession = Depends(get_db),
) -> GapResponse:
    try:
        job_uuid = UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")
    try:
        user_uuid = UUID(body.user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    job = await db.get(Job, job_uuid)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_uuid)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")

    required = job.required_skills or []
    user_skills = profile.skills or []
    missing, matched = compute_gap(required, user_skills)

    return GapResponse(
        job_id=job_id,
        user_id=body.user_id,
        required_skills=required,
        user_skills=user_skills,
        missing_skills=missing,
        matched_skills=matched,
    )
