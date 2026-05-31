"""Contract validation tests for the A -> B boundary schemas."""

from __future__ import annotations

import copy

import pytest

from SkillUp_SHZurich.integration.contracts import (
    ContractError,
    LearningRequest,
    MatchmakingOutput,
    validate_learning_request,
    validate_matchmaking_output,
)


def test_valid_matchmaking_output_parses(mock_match_response):
    output = validate_matchmaking_output(mock_match_response)
    assert isinstance(output, MatchmakingOutput)
    assert output.user_id == "11111111-1111-1111-1111-111111111111"
    assert len(output.matches) == 3
    assert output.candidate_profile is not None
    assert output.candidate_profile.current_role == "Operations Coordinator"


def test_required_field_missing_raises(mock_match_response):
    payload = copy.deepcopy(mock_match_response)
    del payload["matches"][0]["job"]["redirect_url"]  # required on MatchedJob
    with pytest.raises(ContractError) as exc:
        validate_matchmaking_output(payload)
    assert exc.value.contract == "MatchmakingOutput"


def test_wrong_type_raises(mock_match_response):
    payload = copy.deepcopy(mock_match_response)
    payload["matches"][0]["score"] = "not-a-number"
    with pytest.raises(ContractError):
        validate_matchmaking_output(payload)


def test_malformed_matches_not_a_list_raises(mock_match_response):
    payload = copy.deepcopy(mock_match_response)
    payload["matches"] = {"oops": "wrong shape"}
    with pytest.raises(ContractError):
        validate_matchmaking_output(payload)


def test_negative_or_nan_score_rejected(mock_match_response):
    payload = copy.deepcopy(mock_match_response)
    payload["matches"][0]["score"] = -0.5
    with pytest.raises(ContractError):
        validate_matchmaking_output(payload)


def test_optional_fields_default_when_absent():
    # Minimal but valid: candidate_profile and per-match skill lists omitted.
    payload = {
        "user_id": "u-1",
        "matches": [
            {
                "job": {"id": "j-1", "title": "Analyst", "redirect_url": "https://x/y"},
                "score": 0.7,
            }
        ],
    }
    output = validate_matchmaking_output(payload)
    assert output.candidate_profile is None
    assert output.matches[0].matched_skills == []
    assert output.matches[0].missing_skills == []
    assert output.matches[0].job.required_skills == []


def test_extra_keys_are_ignored_for_forward_compat(mock_match_response):
    payload = copy.deepcopy(mock_match_response)
    payload["some_future_field"] = {"anything": True}
    payload["matches"][0]["another_new_field"] = 123
    output = validate_matchmaking_output(payload)  # must not raise
    assert len(output.matches) == 3


def test_id_coercion_accepts_non_string():
    payload = {
        "user_id": 12345,
        "matches": [
            {"job": {"id": 999, "title": "X", "redirect_url": "https://x"}, "score": 0.5}
        ],
    }
    output = validate_matchmaking_output(payload)
    assert output.user_id == "12345"
    assert output.matches[0].job.id == "999"


def test_learning_request_round_trips():
    request = validate_learning_request(
        {
            "user_profile": {"current_role": "Coordinator"},
            "target_role": {"role_id": "r1", "title": "Analyst", "industry": "Ops"},
            "missing_skills": [{"skill_name": "workflow automation"}],
        }
    )
    assert isinstance(request, LearningRequest)
    assert request.missing_skills[0].priority == 1
    assert request.missing_skills[0].source == "matching"


def test_learning_request_empty_skill_name_rejected():
    with pytest.raises(ContractError):
        validate_learning_request(
            {
                "user_profile": {},
                "target_role": {"role_id": "r1", "title": "Analyst"},
                "missing_skills": [{"skill_name": "   "}],
            }
        )
