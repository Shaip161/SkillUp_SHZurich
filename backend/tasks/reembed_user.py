import asyncio
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import settings
from app.models.user import UserProfile
from app.services.embedder import build_cv_embedding_input, embed_text
from tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="tasks.reembed_user.reembed_user")
def reembed_user(user_id: str) -> None:
    asyncio.run(_reembed_user_async(user_id))


async def _reembed_user_async(user_id: str) -> None:
    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with session_factory() as session:
            result = await session.execute(
                select(UserProfile).where(UserProfile.user_id == UUID(user_id))
            )
            profile = result.scalar_one_or_none()

            if not profile:
                logger.warning("reembed_user: no profile for user_id=%s", user_id)
                return

            embedding_text = build_cv_embedding_input(
                seniority=profile.seniority or "unknown",
                skills=profile.skills or [],
                cv_text=profile.cv_text or "",
            )
            profile.embedding = await embed_text(embedding_text, task_type="retrieval_query")
            await session.commit()
            logger.info("Re-embedded user_id=%s", user_id)
    finally:
        await engine.dispose()
