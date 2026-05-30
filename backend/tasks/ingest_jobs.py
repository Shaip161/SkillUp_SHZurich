import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import settings
from app.models.job import Job
from app.services.adzuna import CATEGORIES, fetch_jobs_for_category
from app.services.embedder import build_job_embedding_input, embed_text
from app.services.skill_extractor import extract_skills
from tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="tasks.ingest_jobs.run_ingestion")
def run_ingestion() -> None:
    asyncio.run(_run_ingestion_async())


async def _run_ingestion_async() -> None:
    # NullPool avoids asyncpg event-loop conflicts across multiple asyncio.run() calls
    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        total_inserted = 0
        async with session_factory() as session:
            for category in CATEGORIES:
                inserted = await _ingest_category(session, category)
                total_inserted += inserted

            result = await session.execute(
                delete(Job).where(Job.expires_at < datetime.now(timezone.utc))
            )
            await session.commit()
            expired = result.rowcount

        logger.info(
            "Ingestion complete — inserted: %d, expired removed: %d",
            total_inserted,
            expired,
        )
    finally:
        await engine.dispose()


async def _ingest_category(session: AsyncSession, category: str) -> int:
    raw_jobs = await fetch_jobs_for_category(
        category, max_results=settings.max_jobs_per_category
    )
    logger.info("Processing %d jobs for category '%s'", len(raw_jobs), category)
    inserted = 0

    for raw in raw_jobs:
        adzuna_id = str(raw.get("id", "")).strip()
        if not adzuna_id:
            continue

        existing = await session.execute(
            select(Job.id).where(Job.adzuna_id == adzuna_id)
        )
        if existing.scalar_one_or_none() is not None:
            continue

        title = raw.get("title", "")
        description = raw.get("description", "")

        try:
            extracted = await extract_skills(title, description)
        except Exception as exc:
            logger.warning("Extraction failed adzuna_id=%s: %s", adzuna_id, exc)
            continue

        skills = extracted.get("skills", {})
        required = skills.get("required", [])
        seniority = extracted.get("seniority", "unknown")
        cleaned_desc = extracted.get("description", description)

        embedding_text = build_job_embedding_input(
            title=extracted.get("title", title),
            seniority=seniority,
            required_skills=required,
            description=cleaned_desc,
        )

        try:
            embedding = await embed_text(embedding_text, task_type="retrieval_document")
        except Exception as exc:
            logger.warning("Embedding failed adzuna_id=%s: %s", adzuna_id, exc)
            continue

        created_raw = raw.get("created")
        try:
            created_at = (
                datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
                if created_raw
                else datetime.now(timezone.utc)
            )
        except (ValueError, AttributeError):
            created_at = datetime.now(timezone.utc)

        now = datetime.now(timezone.utc)
        session.add(
            Job(
                adzuna_id=adzuna_id,
                title=extracted.get("title", title),
                description=cleaned_desc,
                company=(raw.get("company") or {}).get("display_name"),
                location=(raw.get("location") or {}).get("display_name"),
                category=(raw.get("category") or {}).get("label"),
                seniority=seniority,
                required_skills=required,
                nice_to_have=skills.get("nice_to_have", []),
                soft_skills=skills.get("soft_skills", []),
                languages=extracted.get("languages", []),
                redirect_url=raw.get("redirect_url", ""),
                embedding=embedding,
                created_at=created_at,
                expires_at=now + timedelta(days=30),
            )
        )
        inserted += 1
        logger.info("Queued: adzuna_id=%s '%s'", adzuna_id, title[:60])

    await session.commit()
    logger.info("Committed %d new jobs for '%s'", inserted, category)
    return inserted
