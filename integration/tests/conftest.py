"""Pytest fixtures and import-path setup for the integration tests.

Inserting the parent of the project directory onto ``sys.path`` makes both
``SkillUp_SHZurich.integration.*`` and ``SkillUp_SHZurich.Agentic_learning.*``
importable, regardless of where pytest is invoked from.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# .../SkillUp_SHZurich/integration/tests -> parent of project root is [4].
_PROJECT_PARENT = Path(__file__).resolve().parents[3]
if str(_PROJECT_PARENT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_PARENT))

_MOCKS = Path(__file__).resolve().parents[1] / "mocks"


@pytest.fixture
def mock_match_response() -> dict:
    """The canned System A output used across tests."""
    return json.loads((_MOCKS / "mock_match_response.json").read_text(encoding="utf-8"))


@pytest.fixture
def mock_cv() -> dict:
    return json.loads((_MOCKS / "mock_cv.json").read_text(encoding="utf-8"))


@pytest.fixture
def mock_jobs() -> list:
    return json.loads((_MOCKS / "mock_jobs.json").read_text(encoding="utf-8"))


@pytest.fixture
def mock_gap_response() -> dict:
    """The canned System A ``/gap/{job_id}`` payload (the documented A->B contract)."""
    return json.loads((_MOCKS / "mock_gap_response.json").read_text(encoding="utf-8"))
