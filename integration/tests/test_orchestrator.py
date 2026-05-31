"""End-to-end workflow tests for the orchestrator.

Covers both:
* the *real* end-to-end path (mock System A + real System B), and
* isolated orchestrator wiring using test doubles for both ports.
"""

from __future__ import annotations

import copy

import pytest

from SkillUp_SHZurich.integration.adapter import LearningObjective
from SkillUp_SHZurich.integration.contracts import LearningRequest, TargetRoleInput
from SkillUp_SHZurich.integration.logging_utils import (
    EVENT_AGENT_INPUT,
    EVENT_AGENT_OUTPUT,
    EVENT_MATCHMAKING_RAW,
    EVENT_TRANSFORMED_PAYLOAD,
    CapturingLogger,
)
from SkillUp_SHZurich.integration.orchestrator import PipelineError, run_end_to_end
from SkillUp_SHZurich.integration.providers import (
    MockMatchmakingProvider,
    TransitionLearningEngine,
)


# --- Test doubles ----------------------------------------------------------


class _RecordingLearningEngine:
    """A LearningEngine double that records the request and returns a stub."""

    def __init__(self) -> None:
        self.received: LearningRequest | None = None

    def generate(self, request: LearningRequest) -> dict:
        self.received = request
        return {
            "curriculum_id": "stub",
            "status": "generated",
            "skills": [{"skill_name": g.skill_name} for g in request.missing_skills],
        }


class _ExplodingMatchmaking:
    def run(self, *, cv, jobs):
        raise RuntimeError("backend unreachable")


# --- Full end-to-end (mock System A + real System B) -----------------------


def test_full_workflow_cv_to_curriculum(mock_cv, mock_jobs, mock_match_response):
    """CV -> matchmaking -> skill gaps -> learning agents, no manual steps."""
    matchmaking = MockMatchmakingProvider(mock_match_response)
    engine = TransitionLearningEngine()
    objective = LearningObjective(
        target_role=TargetRoleInput(
            role_id="operations-analyst", title="Operations Analyst", industry="Logistics"
        ),
        curriculum_id="test-curriculum",
    )
    logger = CapturingLogger()

    result = run_end_to_end(
        cv=mock_cv,
        jobs=mock_jobs,
        matchmaking=matchmaking,
        learning_engine=engine,
        objective=objective,
        logger=logger,
    )

    assert result.learning_result["status"] == "generated"
    assert result.learning_result["curriculum_id"] == "test-curriculum"
    # System B only teaches catalog skills; "Kubernetes" is dropped by System B
    # but was still forwarded by the adapter (decoupling preserved).
    taught = {s.lower() for s in result.curriculum_skill_names}
    assert taught == {"workflow automation", "dashboard reporting", "vendor coordination"}
    assert "Kubernetes" in result.missing_skill_names
    # Each taught skill keeps System B's fixed 5-subskill structure.
    assert all(len(s["subskills"]) == 5 for s in result.learning_result["skills"])


def test_workflow_captures_all_boundary_payloads(mock_cv, mock_jobs, mock_match_response):
    logger = CapturingLogger()
    # Sharing one logger across the orchestrator AND System B yields a single
    # unified trace spanning both layers.
    run_end_to_end(
        cv=mock_cv,
        jobs=mock_jobs,
        matchmaking=MockMatchmakingProvider(mock_match_response),
        learning_engine=TransitionLearningEngine(logger=logger),
        objective=LearningObjective(
            target_role=TargetRoleInput(role_id="r", title="Operations Analyst", industry="Logistics")
        ),
        logger=logger,
    )
    # The three payloads we explicitly want visibility into are all present.
    assert logger.raw_matchmaking_payload is not None
    assert logger.transformed_payload is not None
    assert logger.agent_input_payload is not None
    # And System B's own workflow events were captured on the shared logger.
    assert any(e.event_type.startswith("workflow.") for e in logger.events)


# --- Orchestrator wiring with doubles (no System B) ------------------------


def test_orchestrator_passes_validated_request_to_engine(mock_match_response):
    engine = _RecordingLearningEngine()
    result = run_end_to_end(
        cv=None,
        jobs=None,
        matchmaking=MockMatchmakingProvider(mock_match_response),
        learning_engine=engine,
        objective=LearningObjective(
            target_role=TargetRoleInput(role_id="r", title="Analyst", industry="Ops")
        ),
    )
    # The engine received a fully validated LearningRequest, not a raw dict.
    assert isinstance(engine.received, LearningRequest)
    assert engine.received.target_role.title == "Analyst"
    assert result.learning_result["status"] == "generated"


def test_event_ordering(mock_match_response):
    logger = CapturingLogger()
    run_end_to_end(
        cv=None,
        jobs=None,
        matchmaking=MockMatchmakingProvider(mock_match_response),
        learning_engine=_RecordingLearningEngine(),
        logger=logger,
    )
    types = [e.event_type for e in logger.events]
    # Raw comes before transformed comes before agent input comes before output.
    assert types.index(EVENT_MATCHMAKING_RAW) < types.index(EVENT_TRANSFORMED_PAYLOAD)
    assert types.index(EVENT_TRANSFORMED_PAYLOAD) < types.index(EVENT_AGENT_INPUT)
    assert types.index(EVENT_AGENT_INPUT) < types.index(EVENT_AGENT_OUTPUT)


# --- Failure modes ---------------------------------------------------------


def test_malformed_matchmaking_output_raises_pipeline_error(mock_match_response):
    payload = copy.deepcopy(mock_match_response)
    payload["matches"][0]["score"] = "definitely not a float"
    logger = CapturingLogger()
    with pytest.raises(PipelineError) as exc:
        run_end_to_end(
            cv=None,
            jobs=None,
            matchmaking=MockMatchmakingProvider(payload),
            learning_engine=_RecordingLearningEngine(),
            logger=logger,
        )
    assert exc.value.stage == "contract:matchmaking"
    # A schema-mismatch event was recorded for debugging.
    assert logger.events_of_type("integration.error.schema_mismatch")


def test_matchmaking_provider_failure_surfaces_as_pipeline_error():
    with pytest.raises(PipelineError) as exc:
        run_end_to_end(
            cv=None,
            jobs=None,
            matchmaking=_ExplodingMatchmaking(),
            learning_engine=_RecordingLearningEngine(),
        )
    assert exc.value.stage == "matchmaking"
