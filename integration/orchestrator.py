"""The orchestrator: a lightweight, dependency-injected A -> B pipeline.

It owns the *sequence* of integration steps but none of the *logic* of either
system. It talks to System A and System B only through the
:mod:`integration.ports` protocols and reshapes data only through the
:mod:`integration.adapter`. That separation is what keeps orchestration logic
out of both components and lets either side be swapped or mocked.

Pipeline stages (mirrors the spec):

1. run matchmaking (via the :class:`MatchmakingProvider` port)
2. validate System A's output against the contract
3. extract + prioritise missing skills, and
4. transform into a System B :class:`LearningRequest` (the adapter does 3 & 4)
5. validate the transformed payload, then send it into the learning engine
6. capture all outputs and a structured log trace

Every stage records a structured event, so the raw matchmaking output, the
transformed payload, and the final agent input are all independently
inspectable. Schema failures raise :class:`PipelineError` with the offending
stage attached.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .adapter import LearningObjective, build_learning_request
from .contracts import (
    ContractError,
    LearningRequest,
    MatchmakingOutput,
    validate_learning_request,
    validate_matchmaking_output,
)
from .logging_utils import (
    EVENT_AGENT_INPUT,
    EVENT_AGENT_OUTPUT,
    EVENT_MATCHMAKING_RAW,
    EVENT_MATCHMAKING_VALIDATED,
    EVENT_PIPELINE_WARNING,
    EVENT_SCHEMA_MISMATCH,
    EVENT_TRANSFORMED_PAYLOAD,
    CapturingLogger,
)
from .ports import LearningEngine, MatchmakingProvider, StructuredLogger


class PipelineError(RuntimeError):
    """Raised when the end-to-end workflow fails at a known stage."""

    def __init__(self, stage: str, message: str, *, cause: Exception | None = None) -> None:
        self.stage = stage
        super().__init__(f"[{stage}] {message}")
        if cause is not None:
            self.__cause__ = cause


@dataclass
class PipelineResult:
    """Everything the workflow produced, for assertions, UIs, and debugging."""

    matchmaking_output: MatchmakingOutput
    learning_request: LearningRequest
    learning_result: dict[str, Any]
    logger: StructuredLogger

    @property
    def missing_skill_names(self) -> list[str]:
        return [gap.skill_name for gap in self.learning_request.missing_skills]

    @property
    def curriculum_skill_names(self) -> list[str]:
        return [
            str(skill.get("skill_name", ""))
            for skill in self.learning_result.get("skills", [])
        ]


def run_end_to_end(
    *,
    cv: Any,
    jobs: Any,
    matchmaking: MatchmakingProvider,
    learning_engine: LearningEngine,
    objective: LearningObjective | None = None,
    logger: StructuredLogger | None = None,
) -> PipelineResult:
    """Run the full CV -> matchmaking -> skill gaps -> learning-agents workflow.

    Parameters
    ----------
    cv, jobs:
        Raw inputs forwarded to the matchmaking provider untouched.
    matchmaking:
        System A behind the :class:`MatchmakingProvider` port.
    learning_engine:
        System B behind the :class:`LearningEngine` port.
    objective:
        The learning objective (target role + learner overrides) the adapter
        merges with System A's skill gaps.
    logger:
        Structured logger; a fresh :class:`CapturingLogger` is created if omitted.
    """
    log: StructuredLogger = logger or CapturingLogger()

    # -- 1. Run matchmaking (System A) -------------------------------------
    try:
        raw_output = matchmaking.run(cv=cv, jobs=jobs)
    except Exception as exc:  # noqa: BLE001 -- surface any provider failure uniformly
        raise PipelineError("matchmaking", f"matchmaking provider failed: {exc}", cause=exc) from exc
    log.record(EVENT_MATCHMAKING_RAW, {"output": raw_output})

    # -- 2. Validate System A's output contract ----------------------------
    try:
        matchmaking_output = validate_matchmaking_output(raw_output)
    except ContractError as exc:
        log.record(
            EVENT_SCHEMA_MISMATCH,
            {"contract": exc.contract, "errors": str(exc.validation_error)},
            level="minimal",
        )
        raise PipelineError("contract:matchmaking", str(exc), cause=exc) from exc
    log.record(
        EVENT_MATCHMAKING_VALIDATED,
        {
            "user_id": matchmaking_output.user_id,
            "match_count": len(matchmaking_output.matches),
            "has_candidate_profile": matchmaking_output.candidate_profile is not None,
        },
    )

    # -- 3 & 4. Extract skill gaps and transform into System B's input -----
    learning_request = build_learning_request(matchmaking_output, objective)
    log.record(EVENT_TRANSFORMED_PAYLOAD, {"learning_request": learning_request})

    if not learning_request.missing_skills:
        # Not fatal here (System B will reject downstream), but we make the
        # gap-less situation explicit in the trace.
        log.record(
            EVENT_PIPELINE_WARNING,
            {"message": "No missing skills extracted from matchmaking output."},
            level="minimal",
        )

    # -- 5. Re-validate the transformed payload, then invoke System B ------
    try:
        validated_request = validate_learning_request(learning_request)
    except ContractError as exc:
        log.record(
            EVENT_SCHEMA_MISMATCH,
            {"contract": exc.contract, "errors": str(exc.validation_error)},
            level="minimal",
        )
        raise PipelineError("contract:learning", str(exc), cause=exc) from exc

    log.record(EVENT_AGENT_INPUT, {"agent_input": validated_request})
    try:
        learning_result = dict(learning_engine.generate(validated_request))
    except Exception as exc:  # noqa: BLE001
        raise PipelineError("learning", f"learning engine failed: {exc}", cause=exc) from exc

    # -- 6. Capture final output -------------------------------------------
    log.record(
        EVENT_AGENT_OUTPUT,
        {
            "curriculum_id": learning_result.get("curriculum_id"),
            "status": learning_result.get("status"),
            "skill_count": len(learning_result.get("skills", [])),
        },
    )

    return PipelineResult(
        matchmaking_output=matchmaking_output,
        learning_request=validated_request,
        learning_result=learning_result,
        logger=log,
    )
