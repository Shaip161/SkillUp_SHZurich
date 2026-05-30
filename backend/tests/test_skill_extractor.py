import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.skill_extractor import extract_skills


def _mock_response(payload: dict) -> MagicMock:
    msg = MagicMock()
    msg.content = [MagicMock(text=json.dumps(payload))]
    return msg


VALID_PAYLOAD = {
    "title": "Python Developer",
    "description": "Build scalable APIs with FastAPI.",
    "skills": {
        "required": ["Python", "PostgreSQL"],
        "nice_to_have": ["dbt"],
        "soft_skills": ["Communication"],
    },
    "seniority": "mid",
    "languages": ["English"],
}


@pytest.mark.asyncio
async def test_parses_valid_json_response():
    with patch(
        "app.services.skill_extractor._client.messages.create",
        new_callable=AsyncMock,
        return_value=_mock_response(VALID_PAYLOAD),
    ):
        result = await extract_skills("Python Developer", "Build scalable APIs")

    assert result["title"] == "Python Developer"
    assert result["skills"]["required"] == ["Python", "PostgreSQL"]
    assert result["skills"]["nice_to_have"] == ["dbt"]
    assert result["seniority"] == "mid"
    assert result["languages"] == ["English"]


@pytest.mark.asyncio
async def test_strips_markdown_code_fences():
    fenced = f"```json\n{json.dumps(VALID_PAYLOAD)}\n```"
    msg = MagicMock()
    msg.content = [MagicMock(text=fenced)]

    with patch(
        "app.services.skill_extractor._client.messages.create",
        new_callable=AsyncMock,
        return_value=msg,
    ):
        result = await extract_skills("Python Developer", "Build scalable APIs")

    assert result["title"] == "Python Developer"
    assert "Python" in result["skills"]["required"]


@pytest.mark.asyncio
async def test_strips_plain_code_fences():
    fenced = f"```\n{json.dumps(VALID_PAYLOAD)}\n```"
    msg = MagicMock()
    msg.content = [MagicMock(text=fenced)]

    with patch(
        "app.services.skill_extractor._client.messages.create",
        new_callable=AsyncMock,
        return_value=msg,
    ):
        result = await extract_skills("Python Developer", "Build scalable APIs")

    assert result["seniority"] == "mid"


@pytest.mark.asyncio
async def test_raises_on_invalid_json():
    msg = MagicMock()
    msg.content = [MagicMock(text="not valid json {{ }}")]

    with patch(
        "app.services.skill_extractor._client.messages.create",
        new_callable=AsyncMock,
        return_value=msg,
    ):
        with pytest.raises(Exception):
            await extract_skills("Some Job", "Some description")
