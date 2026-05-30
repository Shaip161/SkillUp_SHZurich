import asyncio
import json
import logging

from anthropic import AsyncAnthropic

from app.config import settings

logger = logging.getLogger(__name__)

_client = AsyncAnthropic(api_key=settings.anthropic_api_key)
_MODEL = "claude-sonnet-4-6"

_SYSTEM_PROMPT = """\
Extract structured information from a job posting or CV.

Return ONLY valid JSON — no markdown fences, no explanation:
{
  "title": "cleaned job title",
  "description": "cleaned description with boilerplate removed",
  "skills": {
    "required":     ["skill1", "skill2"],
    "nice_to_have": ["skill3"],
    "soft_skills":  ["skill4"]
  },
  "seniority": "junior | mid | senior | lead | unknown",
  "languages": ["English", "German"]
}

Rules:
- Normalise skill names: ReactJS→React, ML→Machine Learning, JS→JavaScript,
  NodeJS→Node.js, Postgres→PostgreSQL, K8s→Kubernetes
- No duplicates across any skill bucket
- languages = spoken human languages ONLY (not programming languages)
- Strip boilerplate: equal opportunity statements, legal disclaimers,
  excessive "about us" paragraphs
- seniority must be exactly one of: junior, mid, senior, lead, unknown\
"""


async def extract_skills(title: str, description: str) -> dict:
    response = await _client.messages.create(
        model=_MODEL,
        max_tokens=1024,
        system=_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Title: {title}\n\nDescription:\n{description}",
            }
        ],
    )
    raw = response.content[0].text.strip()
    # Strip accidental markdown fences the model might still emit
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


async def extract_skills_batch(
    items: list[tuple[str, str]],
    concurrency: int = 5,
) -> list[dict | None]:
    semaphore = asyncio.Semaphore(concurrency)

    async def _guarded(title: str, description: str) -> dict | None:
        async with semaphore:
            try:
                return await extract_skills(title, description)
            except Exception as exc:
                logger.warning("Batch extraction failed for '%s': %s", title, exc)
                return None

    return list(
        await asyncio.gather(*[_guarded(t, d) for t, d in items])
    )
