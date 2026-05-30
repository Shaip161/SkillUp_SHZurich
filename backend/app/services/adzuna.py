import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

CATEGORIES = ["it-jobs", "engineering-jobs", "accounting-finance-jobs"]

_BASE_URL = "https://api.adzuna.com/v1/api/jobs/ch/search"
_RESULTS_PER_PAGE = 50
_MAX_PAGES = 20  # safety cap


async def fetch_jobs_for_category(
    category: str, max_results: int = 0
) -> list[dict]:
    jobs: list[dict] = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        for page in range(1, _MAX_PAGES + 1):
            results_per_page = _RESULTS_PER_PAGE
            if max_results > 0:
                remaining = max_results - len(jobs)
                if remaining <= 0:
                    break
                results_per_page = min(_RESULTS_PER_PAGE, remaining)

            response = await client.get(
                f"{_BASE_URL}/{page}",
                params={
                    "app_id": settings.adzuna_app_id,
                    "app_key": settings.adzuna_app_key,
                    "results_per_page": results_per_page,
                    "category": category,
                },
            )
            response.raise_for_status()
            results = response.json().get("results", [])
            if not results:
                break
            jobs.extend(results)
            logger.info(
                "Adzuna page %d for '%s': %d results (%d total)",
                page,
                category,
                len(results),
                len(jobs),
            )
            if max_results > 0 and len(jobs) >= max_results:
                break
    return jobs
