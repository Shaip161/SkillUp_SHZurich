import uuid as _uuid
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.job import JobListItem
from app.models.user import User, UserProfile
from app.services.cv_parser import parse_cv
from app.services.embedder import build_cv_embedding_input, embed_text
from app.services.matcher import compute_gap, search_jobs
from app.services.skill_extractor import extract_skills

router = APIRouter()


class JobMatchResult(BaseModel):
    job: JobListItem
    score: float
    matched_skills: list[str]
    missing_skills: list[str]


class MatchResponse(BaseModel):
    user_id: str
    matches: list[JobMatchResult]


@router.post("/match", response_model=MatchResponse)
async def match_cv(
    cv: UploadFile = File(...),
    user_id: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
) -> MatchResponse:
    # --- Parse ---
    data = await cv.read()
    try:
        cv_text = parse_cv(data, cv.filename or "upload.pdf")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # --- Extract skills ---
    try:
        extracted = await extract_skills("CV", cv_text)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Skill extraction failed: {exc}")

    skills = extracted.get("skills", {})
    all_skills = (
        skills.get("required", [])
        + skills.get("nice_to_have", [])
        + skills.get("soft_skills", [])
    )
    seniority = extracted.get("seniority", "unknown")
    languages = extracted.get("languages", [])
    embedding_summary = extracted.get("embedding_summary", "")

    # --- Embed ---
    try:
        embedding = await embed_text(
            build_cv_embedding_input(seniority, all_skills, embedding_summary),
            task_type="retrieval_query",
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Embedding failed: {exc}")

    # --- Resolve / create user ---
    effective_uid: UUID
    if user_id and user_id.strip():
        try:
            effective_uid = UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user ID format")
        if not await db.get(User, effective_uid):
            raise HTTPException(status_code=404, detail="User not found")
    else:
        new_user = User(email=f"anon-{_uuid.uuid4()}@jobmatcher.local")
        db.add(new_user)
        await db.flush()
        effective_uid = new_user.id

    # --- Upsert profile ---
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == effective_uid)
    )
    profile = result.scalar_one_or_none()
    if profile:
        profile.cv_text = cv_text
        profile.skills = all_skills
        profile.seniority = seniority
        profile.languages = languages
        profile.embedding = embedding
    else:
        db.add(UserProfile(
            user_id=effective_uid,
            cv_text=cv_text,
            skills=all_skills,
            seniority=seniority,
            languages=languages,
            embedding=embedding,
        ))

    await db.commit()

    # --- Search ---
    matches = await search_jobs(db, embedding, k=20, min_score=0.50)

    return MatchResponse(
        user_id=str(effective_uid),
        matches=[
            JobMatchResult(
                job=JobListItem(
                    id=m.id,
                    title=m.title,
                    company=m.company,
                    location=m.location,
                    category=m.category,
                    seniority=m.seniority,
                    required_skills=m.required_skills,
                    redirect_url=m.redirect_url,
                ),
                score=m.score,
                matched_skills=compute_gap(m.required_skills, all_skills)[1],
                missing_skills=compute_gap(m.required_skills, all_skills)[0],
            )
            for m in matches
        ],
    )
