"""Validation against System A's *documented* A->B contract: POST /gap/{job_id}.

CLAUDE.md designates ``GapResponse`` (required_skills - user_skills) as the pure
data contract the learning system consumes directly. These tests prove the
integration layer accepts that exact shape and drives System B end-to-end from
it.
"""

from __future__ import annotations

import copy

import pytest

from SkillUp_SHZurich.integration.adapter import (
    LearningObjective,
    build_learning_request_from_gap,
)
from SkillUp_SHZurich.integration.contracts import (
    ContractError,
    GapResponse,
    LearningRequest,
    TargetRoleInput,
    validate_gap_response,
)
from SkillUp_SHZurich.integration.providers import TransitionLearningEngine


def test_gap_response_matches_backend_shape(mock_gap_response):
    gap = validate_gap_response(mock_gap_response)
    assert isinstance(gap, GapResponse)
    assert gap.job_id == "aaaaaaaa-0000-0000-0000-000000001001"
    assert gap.user_id == "11111111-1111-1111-1111-111111111111"
    assert gap.missing_skills == ["Workflow automation", "Dashboard reporting", "Vendor coordination"]


def test_gap_response_required_field_missing_raises(mock_gap_response):
    payload = copy.deepcopy(mock_gap_response)
    del payload["missing_skills"]  # required list (no default-trigger but field required? has default)
    # missing_skills has a default, so removing it must NOT raise; user_id is required.
    assert validate_gap_response(payload).missing_skills == []
    del payload["user_id"]
    with pytest.raises(ContractError):
        validate_gap_response(payload)


def test_gap_to_learning_request_maps_fields(mock_gap_response):
    gap = validate_gap_response(mock_gap_response)
    objective = LearningObjective(
        target_role=TargetRoleInput(role_id="ops-analyst", title="Operations Analyst", industry="Logistics")
    )
    request = build_learning_request_from_gap(gap, objective)
    assert isinstance(request, LearningRequest)
    assert [g.skill_name for g in request.missing_skills] == [
        "Workflow automation",
        "Dashboard reporting",
        "Vendor coordination",
    ]
    # Source is tagged so downstream can tell which System A surface it came from.
    assert all(g.source == "gap_endpoint" for g in request.missing_skills)
    # user_skills become the learner's known skills; user_id is carried over.
    assert "Excel" in request.user_profile.explicit_skills
    assert request.user_profile.user_id == gap.user_id


def test_gap_aggregates_across_multiple_jobs(mock_gap_response):
    g1 = validate_gap_response(mock_gap_response)
    g2 = validate_gap_response(
        {
            "job_id": "j2",
            "user_id": g1.user_id,
            "missing_skills": ["Workflow automation", "Kubernetes"],
        }
    )
    request = build_learning_request_from_gap([g1, g2], LearningObjective())
    names = [g.skill_name for g in request.missing_skills]
    # "Workflow automation" demanded by both jobs -> top priority.
    assert names[0] == "Workflow automation"
    assert request.missing_skills[0].priority == 1
    assert "Kubernetes" in names


def test_full_gap_contract_drives_system_b_end_to_end(mock_gap_response):
    """GapResponse -> LearningRequest -> System B produces a real curriculum."""
    gap = validate_gap_response(mock_gap_response)
    request = build_learning_request_from_gap(
        gap,
        LearningObjective(
            target_role=TargetRoleInput(role_id="ops-analyst", title="Operations Analyst", industry="Logistics"),
            curriculum_id="gap-contract-demo",
        ),
    )
    result = TransitionLearningEngine().generate(request)
    assert result["status"] == "generated"
    assert result["curriculum_id"] == "gap-contract-demo"
    taught = {s["skill_name"].lower() for s in result["skills"]}
    assert taught == {"workflow automation", "dashboard reporting", "vendor coordination"}
    assert all(len(s["subskills"]) == 5 for s in result["skills"])
