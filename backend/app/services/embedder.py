import asyncio
import logging

import google.generativeai as genai

from app.config import settings

logger = logging.getLogger(__name__)

genai.configure(api_key=settings.gemini_api_key)

_PRIMARY_MODEL = "models/gemini-embedding-001"
_FALLBACK_MODEL = "models/gemini-embedding-2"

# Cached after the first successful call so we never retry a 404 model.
_active_model: str | None = None


def _embed_sync(text: str, task_type: str) -> list[float]:
    global _active_model

    if _active_model is not None:
        result = genai.embed_content(
            model=_active_model, content=text, task_type=task_type
        )
        return result["embedding"]

    try:
        result = genai.embed_content(
            model=_PRIMARY_MODEL, content=text, task_type=task_type
        )
        _active_model = _PRIMARY_MODEL
        logger.info("Embedder using model: %s", _PRIMARY_MODEL)
        return result["embedding"]
    except Exception as exc:
        logger.warning(
            "Primary embedding model %s unavailable (%s), falling back to %s",
            _PRIMARY_MODEL,
            exc,
            _FALLBACK_MODEL,
        )
        result = genai.embed_content(
            model=_FALLBACK_MODEL, content=text, task_type=task_type
        )
        _active_model = _FALLBACK_MODEL
        logger.info("Embedder using model: %s", _FALLBACK_MODEL)
        return result["embedding"]


async def embed_text(text: str, task_type: str = "retrieval_document") -> list[float]:
    return await asyncio.to_thread(_embed_sync, text, task_type)


def build_job_embedding_input(
    title: str,
    seniority: str,
    required_skills: list[str],
    description: str,
) -> str:
    skills_str = ", ".join(required_skills)
    return f"{title} | {seniority} | Skills: {skills_str} | {description[:500]}"


def build_cv_embedding_input(
    seniority: str,
    skills: list[str],
    cv_text: str,
) -> str:
    skills_str = ", ".join(skills)
    return f"{seniority} professional | Skills: {skills_str} | {cv_text[:500]}"
