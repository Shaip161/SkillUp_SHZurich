from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class JobMatch:
    id: UUID
    title: str
    company: str | None
    location: str | None
    category: str | None
    seniority: str | None
    required_skills: list[str]
    nice_to_have: list[str]
    soft_skills: list[str]
    redirect_url: str
    score: float


async def search_jobs(
    session: AsyncSession,
    user_vector: list[float],
    k: int = 20,
    min_score: float = 0.50,
) -> list[JobMatch]:
    vector_literal = "[" + ",".join(map(str, user_vector)) + "]"

    stmt = text(
        f"""
        SELECT id, title, company, location, category, seniority,
               required_skills, nice_to_have, soft_skills, redirect_url,
               (1 - (embedding <=> '{vector_literal}'::vector))::float AS score
        FROM   jobs
        WHERE  expires_at > now()
          AND  embedding IS NOT NULL
        ORDER  BY embedding <=> '{vector_literal}'::vector
        LIMIT  :k
        """
    )

    rows = (await session.execute(stmt, {"k": k})).fetchall()

    return [
        JobMatch(
            id=row.id,
            title=row.title,
            company=row.company,
            location=row.location,
            category=row.category,
            seniority=row.seniority,
            required_skills=row.required_skills or [],
            nice_to_have=row.nice_to_have or [],
            soft_skills=row.soft_skills or [],
            redirect_url=row.redirect_url,
            score=row.score,
        )
        for row in rows
        if row.score >= min_score
    ]


def compute_gap(
    job_required_skills: list[str],
    user_skills: list[str],
) -> tuple[list[str], list[str]]:
    user_lower = {s.lower() for s in user_skills}
    missing = [s for s in job_required_skills if s.lower() not in user_lower]
    matched = [s for s in job_required_skills if s.lower() in user_lower]
    return missing, matched
