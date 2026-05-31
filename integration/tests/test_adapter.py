"""Tests for the System A -> System B adapter/mapper."""

from __future__ import annotations

import copy

from SkillUp_SHZurich.integration.adapter import (
    LearningObjective,
    aggregate_skill_gaps,
    build_learning_request,
)
from SkillUp_SHZurich.integration.contracts import (
    LearnerProfileInput,
    TargetRoleInput,
    validate_matchmaking_output,
)


def test_skill_gaps_aggregated_and_prioritised_by_demand(mock_match_response):
    output = validate_matchmaking_output(mock_match_response)
    gaps = aggregate_skill_gaps(output)
    names = [gap.skill_name for gap in gaps]
    # workflow automation is missing for all 3 jobs -> highest priority.
    assert names[0].lower() == "workflow automation"
    assert gaps[0].priority == 1
    # Demand counts: dashboard reporting (2) and vendor coordination (2) beat
    # kubernetes (1); ties broken alphabetically.
    assert names[:4] == [
        "Workflow automation",
        "Dashboard reporting",
        "Vendor coordination",
        "Kubernetes",
    ]
    # Deduplicated: each distinct skill appears once.
    assert len(names) == len(set(n.lower() for n in names))


def test_max_skills_truncates_lowest_priority(mock_match_response):
    output = validate_matchmaking_output(mock_match_response)
    gaps = aggregate_skill_gaps(output, max_skills=2)
    assert [g.skill_name for g in gaps] == ["Workflow automation", "Dashboard reporting"]


def test_target_role_from_objective_wins(mock_match_response):
    output = validate_matchmaking_output(mock_match_response)
    objective = LearningObjective(
        target_role=TargetRoleInput(role_id="r", title="Data Ops Lead", industry="Tech")
    )
    request = build_learning_request(output, objective)
    assert request.target_role.title == "Data Ops Lead"


def test_target_role_falls_back_to_top_match(mock_match_response):
    output = validate_matchmaking_output(mock_match_response)
    request = build_learning_request(output, LearningObjective())
    # Top match by score (0.88) is the Operations Analyst job.
    assert request.target_role.title == "Operations Analyst"
    assert request.target_role.industry == "Logistics"
    assert request.target_role.role_id == "operations-analyst"


def test_profile_uses_candidate_profile_when_present(mock_match_response):
    output = validate_matchmaking_output(mock_match_response)
    request = build_learning_request(output, LearningObjective())
    assert request.user_profile.current_role == "Operations Coordinator"
    assert "Excel" in request.user_profile.explicit_skills
    assert request.user_profile.user_id == output.user_id


def test_profile_derived_from_matches_when_no_candidate(mock_match_response):
    payload = copy.deepcopy(mock_match_response)
    payload.pop("candidate_profile")
    output = validate_matchmaking_output(payload)
    request = build_learning_request(output, LearningObjective())
    # Skills inferred from union of matched_skills across jobs.
    skills = {s.lower() for s in request.user_profile.explicit_skills}
    assert skills == {"excel", "stakeholder communication"}
    assert request.user_profile.current_role == ""  # nothing to derive it from


def test_explicit_learner_override_wins(mock_match_response):
    output = validate_matchmaking_output(mock_match_response)
    objective = LearningObjective(
        learner=LearnerProfileInput(current_role="Junior Analyst", explicit_skills=["python"]),
        preferences={"pace": "fast"},
    )
    request = build_learning_request(output, objective)
    assert request.user_profile.current_role == "Junior Analyst"
    assert request.user_profile.explicit_skills == ["python"]
    # Preferences merged; user_id backfilled from System A identity.
    assert request.user_profile.preferences == {"pace": "fast"}
    assert request.user_profile.user_id == output.user_id


def test_non_catalog_skills_passed_through_untouched(mock_match_response):
    # The adapter must not filter on value; "Kubernetes" stays in the request.
    output = validate_matchmaking_output(mock_match_response)
    request = build_learning_request(output, LearningObjective())
    assert any(g.skill_name == "Kubernetes" for g in request.missing_skills)


def test_empty_matches_produces_placeholder_role_and_no_gaps():
    output = validate_matchmaking_output({"user_id": "u", "matches": []})
    request = build_learning_request(output, LearningObjective())
    assert request.missing_skills == []
    assert request.target_role.title == "Unknown target role"
