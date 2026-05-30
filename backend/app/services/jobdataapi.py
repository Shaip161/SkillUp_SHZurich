import logging
from html.parser import HTMLParser

import httpx

logger = logging.getLogger(__name__)

_BASE_URL = "https://jobdataapi.com/api/jobs/"

CATEGORY_KEYWORDS: dict[str, str] = {
    "it-jobs": "software engineer",
    "engineering-jobs": "mechanical engineer",
    "accounting-finance-jobs": "finance analyst",
}

CATEGORY_LABELS: dict[str, str] = {
    "it-jobs": "IT Jobs",
    "engineering-jobs": "Engineering Jobs",
    "accounting-finance-jobs": "Finance Jobs",
}


class _TagStripper(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def get_text(self) -> str:
        return " ".join(self._parts).strip()


def strip_html(text: str) -> str:
    if not text:
        return ""
    stripper = _TagStripper()
    stripper.feed(text)
    return stripper.get_text()


async def fetch_jobs_for_keyword(keyword: str, max_results: int = 0) -> list[dict]:
    jobs: list[dict] = []
    url: str | None = _BASE_URL
    is_first = True

    async with httpx.AsyncClient(timeout=30.0) as client:
        while url:
            if max_results > 0 and len(jobs) >= max_results:
                break

            if is_first:
                response = await client.get(
                    url,
                    params={"country_code": "CH", "title": keyword},
                )
                is_first = False
            else:
                response = await client.get(url)

            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])
            if not results:
                break

            jobs.extend(results)
            url = data.get("next")
            logger.info(
                "JobDataAPI '%s': %d results (%d total)",
                keyword,
                len(results),
                len(jobs),
            )

    if max_results > 0:
        jobs = jobs[:max_results]

    return jobs
