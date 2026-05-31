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
from app.services.jobdataapi import (
    CATEGORY_KEYWORDS,
    CATEGORY_LABELS,
    fetch_jobs_for_keyword,
    strip_html,
)
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
                inserted = await _ingest_from_jobdataapi(session, category)
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
    logger.info("[adzuna] Processing %d jobs for category '%s'", len(raw_jobs), category)
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
            logger.warning("[adzuna] Extraction failed adzuna_id=%s: %s", adzuna_id, exc)
            continue

        skills = extracted.get("skills", {})
        required = skills.get("required", [])
        seniority = extracted.get("seniority", "unknown")
        cleaned_desc = extracted.get("description", description)
        embedding_summary = extracted.get("embedding_summary", "")

        embedding_text = build_job_embedding_input(
            title=extracted.get("title", title),
            seniority=seniority,
            required_skills=required,
            embedding_summary=embedding_summary,
        )

        try:
            embedding = await embed_text(embedding_text, task_type="retrieval_document")
        except Exception as exc:
            logger.warning("[adzuna] Embedding failed adzuna_id=%s: %s", adzuna_id, exc)
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
                category=CATEGORY_LABELS.get(category),
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
        logger.info("[adzuna] Queued: adzuna_id=%s '%s'", adzuna_id, title[:60])

    await session.commit()
    logger.info("[adzuna] Committed %d new jobs for '%s'", inserted, category)
    return inserted


async def _ingest_from_jobdataapi(session: AsyncSession, category: str) -> int:
    keyword = CATEGORY_KEYWORDS.get(category)
    if not keyword:
        logger.warning("[jobdataapi] No keyword mapping for category '%s'", category)
        return 0

    raw_jobs = await fetch_jobs_for_keyword(
        keyword, max_results=settings.max_jobs_per_category
    )
    logger.info("[jobdataapi] Processing %d jobs for category '%s'", len(raw_jobs), category)
    inserted = 0

    for raw in raw_jobs:
        job_id = raw.get("id")
        if not job_id:
            continue
        adzuna_id = f"jdapi_{job_id}"

        existing = await session.execute(
            select(Job.id).where(Job.adzuna_id == adzuna_id)
        )
        if existing.scalar_one_or_none() is not None:
            continue

        title = raw.get("title", "")
        description = strip_html(raw.get("description", ""))

        try:
            extracted = await extract_skills(title, description)
        except Exception as exc:
            logger.warning("[jobdataapi] Extraction failed id=%s: %s", job_id, exc)
            continue

        skills = extracted.get("skills", {})
        required = skills.get("required", [])
        seniority = extracted.get("seniority", "unknown")
        cleaned_desc = extracted.get("description", description)
        embedding_summary = extracted.get("embedding_summary", "")

        embedding_text = build_job_embedding_input(
            title=extracted.get("title", title),
            seniority=seniority,
            required_skills=required,
            embedding_summary=embedding_summary,
        )

        try:
            embedding = await embed_text(embedding_text, task_type="retrieval_document")
        except Exception as exc:
            logger.warning("[jobdataapi] Embedding failed id=%s: %s", job_id, exc)
            continue

        published = raw.get("published")
        try:
            created_at = (
                datetime.fromisoformat(published.replace("Z", "+00:00"))
                if published
                else datetime.now(timezone.utc)
            )
        except (ValueError, AttributeError):
            created_at = datetime.now(timezone.utc)

        company_raw = raw.get("company") or {}
        company = company_raw.get("name") if isinstance(company_raw, dict) else None
        location_raw = raw.get("location")
        location = (
            location_raw.get("display_name") or location_raw.get("name")
            if isinstance(location_raw, dict)
            else str(location_raw) if location_raw else None
        )

        now = datetime.now(timezone.utc)
        session.add(
            Job(
                adzuna_id=adzuna_id,
                title=extracted.get("title", title),
                description=cleaned_desc,
                company=company,
                location=location,
                category=CATEGORY_LABELS.get(category),
                seniority=seniority,
                required_skills=required,
                nice_to_have=skills.get("nice_to_have", []),
                soft_skills=skills.get("soft_skills", []),
                languages=extracted.get("languages", []),
                redirect_url=raw.get("application_url", ""),
                embedding=embedding,
                created_at=created_at,
                expires_at=now + timedelta(days=30),
            )
        )
        inserted += 1
        logger.info("[jobdataapi] Queued: id=%s '%s'", job_id, title[:60])

    await session.commit()
    logger.info("[jobdataapi] Committed %d new jobs for '%s'", inserted, category)
    return inserted
