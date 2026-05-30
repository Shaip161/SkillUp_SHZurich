import pytest
from app.services.matcher import compute_gap


def test_case_insensitive_matching():
    missing, matched = compute_gap(
        ["Python", "FastAPI", "Kubernetes", "PostgreSQL"],
        ["python", "fastapi", "Docker"],
    )
    assert set(missing) == {"Kubernetes", "PostgreSQL"}
    assert set(matched) == {"Python", "FastAPI"}


def test_all_matched():
    missing, matched = compute_gap(
        ["Python", "FastAPI"],
        ["Python", "FastAPI", "ExtraSkill"],
    )
    assert missing == []
    assert set(matched) == {"Python", "FastAPI"}


def test_none_matched():
    missing, matched = compute_gap(["Python", "FastAPI"], ["Java", "Spring"])
    assert set(missing) == {"Python", "FastAPI"}
    assert matched == []


def test_empty_required_skills():
    missing, matched = compute_gap([], ["Python", "FastAPI"])
    assert missing == []
    assert matched == []


def test_empty_user_skills():
    missing, matched = compute_gap(["Python", "FastAPI"], [])
    assert set(missing) == {"Python", "FastAPI"}
    assert matched == []


def test_preserves_original_case_in_output():
    missing, matched = compute_gap(["Python", "FASTAPI"], ["python", "fastapi"])
    assert missing == []
    assert "Python" in matched
    assert "FASTAPI" in matched


def test_partial_overlap():
    missing, matched = compute_gap(
        ["Python", "FastAPI", "AWS"],
        ["Python", "GCP"],
    )
    assert set(missing) == {"FastAPI", "AWS"}
    assert matched == ["Python"]
