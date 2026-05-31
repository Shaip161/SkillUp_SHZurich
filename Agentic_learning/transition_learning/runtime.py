"""Deterministic online runtime for persisted TransitionAI curricula."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

from SkillUp_SHZurich.Agentic_learning.starter_kit.state import utc_now
from SkillUp_SHZurich.Agentic_learning.starter_kit.state import init_state
from SkillUp_SHZurich.Agentic_learning.starter_kit.workflow import NodeResult, WorkflowNode, WorkflowRunner, WorkflowServices
from SkillUp_SHZurich.Agentic_learning.transition_learning.contracts import (
    CurriculumSkill,
    CurriculumSubskill,
    ErrorRecord,
    EvaluationResult,
    GeneratedCurriculum,
    ProgressState,
    StagePayload,
)
from SkillUp_SHZurich.Agentic_learning.transition_learning.integrations import (
    aggregate_final_with_llm,
    evaluate_conceptual_with_llm,
    evaluate_practical_with_llm,
    generate_remediation_with_llm,
)
from SkillUp_SHZurich.Agentic_learning.transition_learning.knowledge_base import STAGE_SEQUENCE


SUBMISSION_REQUIRED_STAGES = {"conceptual", "practical", "evaluation"}
_TEXT_STOPWORDS = {
    "about",
    "again",
    "also",
    "and",
    "around",
    "because",
    "before",
    "being",
    "between",
    "can",
    "clear",
    "clearly",
    "core",
    "define",
    "design",
    "does",
    "each",
    "explain",
    "explains",
    "from",
    "have",
    "into",
    "more",
    "must",
    "need",
    "operational",
    "part",
    "produc",
    "produce",
    "reasoning",
    "recogniz",
    "ready",
    "should",
    "show",
    "that",
    "their",
    "them",
    "then",
    "they",
    "this",
    "through",
    "using",
    "with",
    "workflow",
    "workflows",
    "map",
}


@dataclass(frozen=True)
class RuntimeSkillProgress:
    skill_id: str
    skill_name: str
    subskill_id: str
    subskill_name: str
    mastery_status: str
    progress_percent: float
    unlocked: bool


@dataclass(frozen=True)
class RuntimeSnapshot:
    curriculum_id: str
    user_id: str
    current_skill_id: str | None
    current_subskill_id: str | None
    current_stage_type: str | None
    current_stage: StagePayload | None
    progress: ProgressState | None
    skill_overview: list[RuntimeSkillProgress] = field(default_factory=list)
    next_step: dict[str, str] | None = None
    requires_submission: bool = False
    remediation_required: bool = False
    evaluation_result: EvaluationResult | None = None
    error_record: ErrorRecord | None = None
    completed: bool = False


def _normalize_text(value: Any) -> str:
    text = str(value or "").lower()
    return "".join(character if character.isalnum() else " " for character in text)


def _keyword_tokens(value: Any) -> set[str]:
    tokens: set[str] = set()
    for raw_token in _normalize_text(value).split():
        if len(raw_token) < 4:
            continue
        normalized_token = raw_token
        for suffix in ("ing", "ed", "es", "s"):
            if normalized_token.endswith(suffix) and len(normalized_token) - len(suffix) >= 4:
                normalized_token = normalized_token[: -len(suffix)]
                break
        if normalized_token in _TEXT_STOPWORDS:
            continue
        tokens.add(normalized_token)
    return tokens


def _phrase_coverage(answer_text: str, phrase: str) -> float:
    expected_tokens = _keyword_tokens(phrase)
    if not expected_tokens:
        return 1.0 if str(phrase).strip().lower() in _normalize_text(answer_text) else 0.0
    answer_tokens = _keyword_tokens(answer_text)
    if not answer_tokens:
        return 0.0
    hits = 0
    for expected_token in expected_tokens:
        if any(
            answer_token.startswith(expected_token)
            or expected_token.startswith(answer_token)
            or answer_token[:5] == expected_token[:5]
            for answer_token in answer_tokens
        ):
            hits += 1
    return round(hits / len(expected_tokens), 3)


def _unique_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    items: list[str] = []
    for value in values:
        normalized = str(value).strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        items.append(normalized)
    return items


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _threshold_from_stage(stage: StagePayload, key: str, default: float) -> float:
    thresholds = dict(stage.expected_output.get("thresholds", {}) or {})
    if key in thresholds:
        return _safe_float(thresholds.get(key), default)
    return _safe_float(stage.expected_output.get("passing_threshold", default), default)


def _weights_from_stage(stage: StagePayload) -> dict[str, float]:
    weights = dict(stage.expected_output.get("weights", {}) or {})
    return {
        "conceptual": _safe_float(weights.get("conceptual"), 0.45),
        "practical": _safe_float(weights.get("practical"), 0.45),
        "integration": _safe_float(weights.get("integration"), 0.10),
    }


def _record_runtime_event(
    services: WorkflowServices,
    event_type: str,
    payload: dict[str, Any],
    *,
    level: str = "debug",
) -> None:
    if services.logger is None:
        return
    services.logger.record(event_type, payload, level=level)


def _record_deterministic_trace(
    services: WorkflowServices,
    prompt_name: str,
    input_payload: dict[str, Any],
    parsed_output: dict[str, Any],
) -> None:
    _record_runtime_event(services, "learning.input", {
                          "prompt_name": prompt_name, "input": input_payload})
    _record_runtime_event(
        services,
        "learning.prompt",
        {"prompt_name": prompt_name,
            "prompt": "deterministic evaluator", "input": input_payload},
    )
    _record_runtime_event(
        services,
        "learning.raw_output",
        {"prompt_name": prompt_name, "raw_output": parsed_output},
    )
    _record_runtime_event(
        services,
        "learning.parsed_output",
        {"prompt_name": prompt_name, "parsed_output": parsed_output},
    )


def _subskill_records(
    evaluations: list[EvaluationResult],
    errors: list[ErrorRecord],
    *,
    skill_id: str,
    subskill_id: str,
) -> tuple[list[EvaluationResult], list[ErrorRecord]]:
    return (
        [
            item
            for item in evaluations
            if item.skill_id == skill_id and item.subskill_id == subskill_id
        ],
        [
            item
            for item in errors
            if item.skill_id == skill_id and item.subskill_id == subskill_id
        ],
    )


def _latest_stage_evaluation(
    evaluations: list[EvaluationResult],
    stage_name: str,
) -> EvaluationResult | None:
    candidates = [item for item in evaluations if item.stage == stage_name]
    if not candidates:
        return None
    return max(candidates, key=lambda item: (item.created_at, item.evaluation_id))


def _build_profile_context(
    curriculum: GeneratedCurriculum,
    *,
    skill: CurriculumSkill,
    subskill: CurriculumSubskill,
    evaluations: list[EvaluationResult],
    errors: list[ErrorRecord],
) -> dict[str, Any]:
    profile = curriculum.user_profile
    prior_scores = {item.stage: item.score for item in evaluations}
    prior_mistakes = _unique_strings(
        [
            *[mistake for item in evaluations for mistake in item.errors],
            *[mistake for item in evaluations for mistake in item.misconceptions],
            *[mistake for item in errors for mistake in item.main_errors],
            *[item.error_type for item in errors],
        ]
    )
    return {
        "current_role": profile.current_role,
        "industry_background": profile.industry_background,
        "previous_roles": list(profile.previous_roles),
        "previous_tasks": list(profile.previous_tasks),
        "previous_workflows": list(profile.previous_workflows),
        "analogous_experiences": list(profile.analogous_experiences),
        "known_tools": list(profile.known_tools),
        "certifications": list(profile.certifications),
        "prior_scores": prior_scores,
        "prior_mistakes": prior_mistakes,
        "skill_name": skill.skill_name,
        "subskill_name": subskill.subskill_name,
        "example_workflows": list(subskill.example_workflows),
    }


def _hydrate_runtime_stage(
    stage: StagePayload,
    *,
    curriculum: GeneratedCurriculum,
    skill: CurriculumSkill,
    subskill: CurriculumSubskill,
    evaluations: list[EvaluationResult],
    errors: list[ErrorRecord],
) -> StagePayload:
    profile_context = _build_profile_context(
        curriculum,
        skill=skill,
        subskill=subskill,
        evaluations=evaluations,
        errors=errors,
    )
    instructions = stage.instructions
    if profile_context["previous_workflows"]:
        instructions = (
            f"{instructions} Anchor the explanation in the learner's prior workflow '{profile_context['previous_workflows'][0]}'."
        )
    elif profile_context["previous_tasks"]:
        instructions = (
            f"{instructions} Connect it to the learner's prior task '{profile_context['previous_tasks'][0]}'."
        )
    if profile_context["prior_mistakes"]:
        instructions = (
            f"{instructions} Watch for previous mistakes such as {', '.join(profile_context['prior_mistakes'][:2])}."
        )
    if stage.stage_type == "reflection" and errors:
        latest_error = max(errors, key=lambda item: (
            item.timestamp, item.error_id))
        instructions = (
            f"{instructions} Focus the retry on {', '.join(latest_error.retry_focus[:2]) or latest_error.error_type}. "
            f"Use this reinforcement task: {latest_error.reinforcement_task or latest_error.description}."
        )
    context = {**dict(stage.context), **profile_context}
    if stage.stage_type == "reflection" and errors:
        latest_error = max(errors, key=lambda item: (
            item.timestamp, item.error_id))
        context["latest_error"] = latest_error.to_dict()
    expected_output = {
        **dict(stage.expected_output),
        "prior_scores": profile_context["prior_scores"],
        "prior_mistakes": profile_context["prior_mistakes"],
    }
    metadata = {**dict(stage.metadata), "runtime_hydrated": True}
    return replace(
        stage,
        instructions=instructions,
        context=context,
        expected_output=expected_output,
        metadata=metadata,
    )


def _build_unlock_state(
    completed_steps: list[str],
    current_stage: str,
    mastery_status: str,
) -> dict[str, bool]:
    unlock_state = {"introduction": True}
    unlock_state["conceptual"] = (
        "introduction" in completed_steps or current_stage in {
            "conceptual", "practical", "evaluation", "reflection"}
    )
    unlock_state["practical"] = (
        "conceptual" in completed_steps or current_stage in {
            "practical", "evaluation", "reflection"}
    )
    unlock_state["evaluation"] = (
        "practical" in completed_steps or current_stage in {
            "evaluation", "reflection"} or mastery_status == "completed"
    )
    unlock_state["reflection"] = (
        current_stage == "reflection" or "reflection" in completed_steps or mastery_status in {
            "needs_remediation", "retry_ready"}
    )
    unlock_state["next_subskill"] = mastery_status == "completed"
    return unlock_state


def _progress_collection_with_update(
    progress_states: list[ProgressState],
    updated_progress: ProgressState,
) -> list[ProgressState]:
    updated: list[ProgressState] = []
    replaced = False
    for progress in progress_states:
        if progress.skill_id == updated_progress.skill_id and progress.subskill_id == updated_progress.subskill_id:
            updated.append(updated_progress)
            replaced = True
            continue
        updated.append(progress)
    if not replaced:
        updated.append(updated_progress)
    return updated


def _completed_subskills(progress_states: list[ProgressState], skill_id: str) -> list[str]:
    return sorted(
        {
            progress.subskill_id
            for progress in progress_states
            if progress.skill_id == skill_id and progress.mastery_status == "completed"
        }
    )


def _build_progress_state(
    previous_progress: ProgressState,
    *,
    current_stage: str,
    completed_steps: list[str],
    mastery_status: str,
    progress_percent: float,
    retry_count: int,
    remediation_state: dict[str, Any],
    latest_scores: dict[str, float],
    latest_errors: list[str],
    completed_subskills: list[str],
) -> ProgressState:
    return ProgressState(
        user_id=previous_progress.user_id,
        skill_id=previous_progress.skill_id,
        subskill_id=previous_progress.subskill_id,
        completed_steps=completed_steps,
        current_step=current_stage,
        progress_percent=progress_percent,
        mastery_status=mastery_status,
        current_skill_id=previous_progress.skill_id,
        current_subskill_id=previous_progress.subskill_id,
        current_stage=current_stage,
        completed_subskills=completed_subskills,
        retry_count=retry_count,
        remediation_state=remediation_state,
        latest_scores=latest_scores,
        latest_errors=latest_errors,
        unlock_state=_build_unlock_state(
            completed_steps, current_stage, mastery_status),
    )


def _deterministic_conceptual_assessment(
    stage: StagePayload,
    subskill: CurriculumSubskill,
    submission: Any,
    *,
    services: WorkflowServices,
) -> dict[str, Any]:
    answer_text = str(submission.get("answer", submission or "")).strip(
    ) if isinstance(submission, dict) else str(submission or "").strip()
    expected_concepts = list(stage.expected_output.get(
        "expected_concepts", [])) or list(subskill.conceptual_criteria)
    criteria_results = {
        concept: _phrase_coverage(answer_text, concept) for concept in expected_concepts
    }
    conceptual_score = round(
        sum(criteria_results.values()) / len(criteria_results), 3
    ) if criteria_results else 0.0
    misconceptions = [
        f"Needs clearer reasoning about {concept.lower()}"
        for concept, score in criteria_results.items()
        if score < 0.55
    ]
    for common_mistake in subskill.common_mistakes:
        if _phrase_coverage(answer_text, common_mistake) >= 0.6:
            misconceptions.append(common_mistake.lower())
    misconceptions = _unique_strings(misconceptions)
    threshold = _threshold_from_stage(stage, "conceptual", 0.72)
    passed = conceptual_score >= threshold and not misconceptions
    feedback = (
        f"Conceptual reasoning is strong across {len(expected_concepts)} criteria."
        if passed
        else "Strengthen the explanation around the missing concepts before claiming mastery."
    )
    parsed_output = {
        "conceptual_score": conceptual_score,
        "misconceptions": misconceptions,
        "feedback": feedback,
        "passed": passed,
        "criteria_results": criteria_results,
    }
    _record_deterministic_trace(
        services,
        "deterministic_conceptual_evaluation",
        {
            "stage": stage.to_dict(),
            "submission": answer_text,
            "expected_concepts": expected_concepts,
        },
        parsed_output,
    )
    return parsed_output


def _deterministic_practical_assessment(
    stage: StagePayload,
    subskill: CurriculumSubskill,
    submission: Any,
    *,
    services: WorkflowServices,
) -> dict[str, Any]:
    answer_text = str(submission.get("answer", submission or "")).strip(
    ) if isinstance(submission, dict) else str(submission or "").strip()
    required_elements = list(stage.expected_output.get(
        "required_elements", [])) or list(subskill.practical_criteria)
    expected_outcomes = list(stage.expected_output.get(
        "expected_outcomes", [])) or list(subskill.expected_outcomes)
    workflow_markers = list(stage.expected_output.get(
        "workflow_markers", [])) or list(subskill.example_workflows)
    required_scores = {item: _phrase_coverage(
        answer_text, item) for item in required_elements}
    outcome_scores = {item: _phrase_coverage(
        answer_text, item) for item in expected_outcomes}
    marker_scores = {item: _phrase_coverage(
        answer_text, item) for item in workflow_markers}
    structure_markers = {
        "trigger",
        "owner",
        "validation",
        "exception",
        "handoff",
        "step",
        "route",
        "outcome",
        "metric",
        "risk",
        "update",
        "decision",
        "alert",
        "milestone",
        "acceptance",
        "escalation",
        "outline",
    }
    answer_tokens = _keyword_tokens(answer_text)
    structure_hits = len(answer_tokens & structure_markers)
    structure_score = min(1.0, round(structure_hits / 4, 3))
    required_score = round(sum(required_scores.values()) /
                           len(required_scores), 3) if required_scores else 0.0
    outcome_score = round(sum(outcome_scores.values()) /
                          len(outcome_scores), 3) if outcome_scores else 0.0
    marker_score = round(sum(marker_scores.values()) /
                         len(marker_scores), 3) if marker_scores else 0.0
    practical_score = round((required_score * 0.5) + (outcome_score *
                            0.2) + (max(marker_score, structure_score) * 0.3), 3)
    errors = _unique_strings(
        [
            f"Missing required element: {item.lower()}"
            for item, score in required_scores.items()
            if max(score, structure_score) < 0.55
        ]
        + [
            f"Expected outcome not demonstrated: {item.lower()}"
            for item, score in outcome_scores.items()
            if max(score, structure_score) < 0.50
        ]
    )
    threshold = _threshold_from_stage(stage, "practical", 0.70)
    passed = practical_score >= threshold and not errors
    feedback = (
        "Practical response covers the expected workflow and output structure."
        if passed
        else "Practical response is incomplete or misses one or more required execution elements."
    )
    parsed_output = {
        "practical_score": practical_score,
        "errors": errors,
        "feedback": feedback,
        "passed": passed,
        "criteria_results": {
            **{f"required::{key}": value for key, value in required_scores.items()},
            **{f"outcome::{key}": value for key, value in outcome_scores.items()},
            **{f"workflow::{key}": value for key, value in marker_scores.items()},
        },
    }
    _record_deterministic_trace(
        services,
        "deterministic_practical_evaluation",
        {
            "stage": stage.to_dict(),
            "submission": answer_text,
            "required_elements": required_elements,
            "expected_outcomes": expected_outcomes,
            "workflow_markers": workflow_markers,
            "structure_score": structure_score,
        },
        parsed_output,
    )
    return parsed_output


def _integration_score(
    stage: StagePayload,
    subskill: CurriculumSubskill,
    submission: Any,
) -> float:
    answer_text = str(submission.get("answer", submission or "")).strip(
    ) if isinstance(submission, dict) else str(submission or "").strip()
    targets = list(subskill.conceptual_criteria) + \
        list(subskill.practical_criteria)
    if not targets:
        return 0.0
    return round(sum(_phrase_coverage(answer_text, target) for target in targets) / len(targets), 3)


def _profile_context_for_llm(curriculum: GeneratedCurriculum, skill: CurriculumSkill, subskill: CurriculumSubskill, evaluations: list[EvaluationResult], errors: list[ErrorRecord]) -> dict[str, Any]:
    return _build_profile_context(
        curriculum,
        skill=skill,
        subskill=subskill,
        evaluations=evaluations,
        errors=errors,
    )


def _conceptual_assessment(
    stage: StagePayload,
    curriculum: GeneratedCurriculum,
    skill: CurriculumSkill,
    subskill: CurriculumSubskill,
    submission: Any,
    *,
    services: WorkflowServices,
    evaluations: list[EvaluationResult],
    errors: list[ErrorRecord],
) -> dict[str, Any]:
    deterministic = _deterministic_conceptual_assessment(
        stage, subskill, submission, services=services)
    llm_result = evaluate_conceptual_with_llm(
        stage,
        submission,
        profile_context=_profile_context_for_llm(
            curriculum, skill, subskill, evaluations, errors),
        llm=services.llm,
        logger=services.logger,
    )
    if llm_result is None:
        return deterministic
    conceptual_score = round(
        (deterministic["conceptual_score"] + llm_result["conceptual_score"]) / 2, 3)
    misconceptions = _unique_strings(
        list(deterministic["misconceptions"]) +
        list(llm_result["misconceptions"])
    )
    threshold = _threshold_from_stage(stage, "conceptual", 0.72)
    passed = conceptual_score >= threshold and not misconceptions
    return {
        "conceptual_score": conceptual_score,
        "misconceptions": misconceptions,
        "feedback": llm_result["feedback"] or deterministic["feedback"],
        "passed": passed,
        "criteria_results": deterministic["criteria_results"],
        "parsed_output": dict(llm_result.get("parsed_output", {}) or {}),
    }


def _practical_assessment(
    stage: StagePayload,
    subskill: CurriculumSubskill,
    submission: Any,
    *,
    services: WorkflowServices,
) -> dict[str, Any]:
    deterministic = _deterministic_practical_assessment(
        stage, subskill, submission, services=services)
    llm_result = evaluate_practical_with_llm(
        stage,
        submission,
        llm=services.llm,
        logger=services.logger,
    )
    if llm_result is None:
        return deterministic
    practical_score = round(
        (deterministic["practical_score"] + llm_result["practical_score"]) / 2, 3)
    errors = _unique_strings(
        list(deterministic["errors"]) + list(llm_result["errors"]))
    threshold = _threshold_from_stage(stage, "practical", 0.70)
    passed = practical_score >= threshold and not errors
    return {
        "practical_score": practical_score,
        "errors": errors,
        "feedback": llm_result["feedback"] or deterministic["feedback"],
        "passed": passed,
        "criteria_results": deterministic["criteria_results"],
        "parsed_output": dict(llm_result.get("parsed_output", {}) or {}),
    }


def _fallback_final_aggregation(
    stage: StagePayload,
    subskill: CurriculumSubskill,
    conceptual_result: EvaluationResult,
    practical_result: EvaluationResult,
    final_submission: Any,
    *,
    services: WorkflowServices,
) -> dict[str, Any]:
    weights = _weights_from_stage(stage)
    integration_score = _integration_score(stage, subskill, final_submission)
    final_score = round(
        (conceptual_result.score * weights["conceptual"]) +
        (practical_result.score * weights["practical"]) +
        (integration_score * weights["integration"]),
        3,
    )
    conceptual_threshold = _threshold_from_stage(stage, "conceptual", 0.72)
    practical_threshold = _threshold_from_stage(stage, "practical", 0.70)
    final_threshold = _threshold_from_stage(stage, "final", 0.75)
    critical_misconceptions = _unique_strings(
        [
            *conceptual_result.misconceptions,
            *conceptual_result.errors,
            *practical_result.errors,
        ]
    )
    passed = (
        conceptual_result.score >= conceptual_threshold
        and practical_result.score >= practical_threshold
        and final_score >= final_threshold
        and not critical_misconceptions
    )
    feedback = (
        "Final evaluation shows coherent conceptual understanding and practical execution."
        if passed
        else "Final evaluation shows unresolved conceptual or practical weaknesses that require remediation."
    )
    parsed_output = {
        "final_score": final_score,
        "passed": passed,
        "critical_misconceptions": critical_misconceptions,
        "retry_required": not passed,
        "feedback": feedback,
        "integration_score": integration_score,
    }
    _record_deterministic_trace(
        services,
        "deterministic_final_aggregation",
        {
            "stage": stage.to_dict(),
            "conceptual_result": conceptual_result.to_dict(),
            "practical_result": practical_result.to_dict(),
            "final_submission": final_submission,
        },
        parsed_output,
    )
    return parsed_output


def _final_aggregation(
    stage: StagePayload,
    curriculum: GeneratedCurriculum,
    skill: CurriculumSkill,
    subskill: CurriculumSubskill,
    conceptual_result: EvaluationResult,
    practical_result: EvaluationResult,
    final_submission: Any,
    *,
    services: WorkflowServices,
    evaluations: list[EvaluationResult],
    errors: list[ErrorRecord],
) -> dict[str, Any]:
    deterministic = _fallback_final_aggregation(
        stage,
        subskill,
        conceptual_result,
        practical_result,
        final_submission,
        services=services,
    )
    llm_result = aggregate_final_with_llm(
        stage,
        conceptual_result=conceptual_result.to_dict(),
        practical_result=practical_result.to_dict(),
        final_submission=final_submission,
        llm=services.llm,
        logger=services.logger,
    )
    if llm_result is None:
        return deterministic
    final_score = round(
        (deterministic["final_score"] + llm_result["final_score"]) / 2, 3)
    critical_misconceptions = _unique_strings(
        list(deterministic["critical_misconceptions"]) +
        list(llm_result["critical_misconceptions"])
    )
    conceptual_threshold = _threshold_from_stage(stage, "conceptual", 0.72)
    practical_threshold = _threshold_from_stage(stage, "practical", 0.70)
    final_threshold = _threshold_from_stage(stage, "final", 0.75)
    passed = (
        conceptual_result.score >= conceptual_threshold
        and practical_result.score >= practical_threshold
        and final_score >= final_threshold
        and not critical_misconceptions
    )
    return {
        "final_score": final_score,
        "passed": passed,
        "critical_misconceptions": critical_misconceptions,
        "retry_required": not passed or bool(llm_result.get("retry_required", False)),
        "feedback": llm_result["feedback"] or deterministic["feedback"],
        "integration_score": deterministic["integration_score"],
        "parsed_output": dict(llm_result.get("parsed_output", {}) or {}),
    }


def _fallback_remediation(
    stage: StagePayload,
    subskill: CurriculumSubskill,
    final_result: EvaluationResult,
) -> dict[str, Any]:
    main_errors = _unique_strings(
        list(final_result.critical_misconceptions) or list(final_result.errors)
    )
    retry_focus = _unique_strings(
        main_errors
        + [
            item
            for item in list(subskill.conceptual_criteria) + list(subskill.practical_criteria)
            if item.lower() in final_result.feedback.lower()
        ]
    ) or list(subskill.conceptual_criteria[:1] + subskill.practical_criteria[:1])
    reinforcement_task = (
        f"Generate a smaller exercise around {retry_focus[0]} using {subskill.example_workflows[0] if subskill.example_workflows else subskill.subskill_name}."
    )
    correct_reasoning = (
        f"To master {subskill.subskill_name}, the learner must connect {', '.join(retry_focus[:2])} to a usable workforce-transition workflow."
    )
    return {
        "main_errors": main_errors,
        "correct_reasoning": correct_reasoning,
        "reinforcement_task": reinforcement_task,
        "retry_focus": retry_focus,
        "parsed_output": {
            "main_errors": main_errors,
            "correct_reasoning": correct_reasoning,
            "reinforcement_task": reinforcement_task,
            "retry_focus": retry_focus,
        },
    }


def _generate_remediation(
    stage: StagePayload,
    curriculum: GeneratedCurriculum,
    skill: CurriculumSkill,
    subskill: CurriculumSubskill,
    final_result: EvaluationResult,
    *,
    services: WorkflowServices,
    evaluations: list[EvaluationResult],
    errors: list[ErrorRecord],
) -> dict[str, Any]:
    deterministic = _fallback_remediation(stage, subskill, final_result)
    llm_result = generate_remediation_with_llm(
        stage,
        profile_context=_profile_context_for_llm(
            curriculum, skill, subskill, evaluations, errors),
        evaluation=final_result.to_dict(),
        llm=services.llm,
        logger=services.logger,
    )
    if llm_result is None:
        return deterministic
    return {
        "main_errors": _unique_strings(list(deterministic["main_errors"]) + list(llm_result["main_errors"])),
        "correct_reasoning": llm_result["correct_reasoning"] or deterministic["correct_reasoning"],
        "reinforcement_task": llm_result["reinforcement_task"] or deterministic["reinforcement_task"],
        "retry_focus": _unique_strings(list(deterministic["retry_focus"]) + list(llm_result["retry_focus"])),
        "parsed_output": dict(llm_result.get("parsed_output", {}) or {}),
    }


def _ordered_subskills(curriculum: GeneratedCurriculum) -> list[tuple[CurriculumSkill, CurriculumSubskill]]:
    ordered: list[tuple[CurriculumSkill, CurriculumSubskill]] = []
    for skill in curriculum.skills:
        for subskill in skill.subskills:
            ordered.append((skill, subskill))
    return ordered


def _progress_lookup(progress_states: list[ProgressState]) -> dict[tuple[str, str], ProgressState]:
    return {(item.skill_id, item.subskill_id): item for item in progress_states}


def _stage_attempt_count(evaluations: list[EvaluationResult], stage_name: str) -> int:
    return len([item for item in evaluations if item.stage == stage_name])


def _default_progress(user_id: str, skill: CurriculumSkill, subskill: CurriculumSubskill) -> ProgressState:
    return ProgressState(
        user_id=user_id,
        skill_id=skill.skill_id,
        subskill_id=subskill.subskill_id,
        completed_steps=[],
        current_step="introduction",
        progress_percent=0.0,
        mastery_status="not_started",
        current_skill_id=skill.skill_id,
        current_subskill_id=subskill.subskill_id,
        current_stage="introduction",
        completed_subskills=[],
        retry_count=0,
        remediation_state={"status": "not_started"},
        latest_scores={},
        latest_errors=[],
        unlock_state=_build_unlock_state([], "introduction", "not_started"),
    )


def _stage_by_type(subskill: CurriculumSubskill, stage_type: str) -> StagePayload:
    for stage in subskill.stages:
        if stage.stage_type == stage_type:
            return stage
    raise ValueError(
        f"Subskill '{subskill.subskill_id}' does not define stage '{stage_type}'.")


def _next_standard_stage(completed_steps: list[str]) -> str | None:
    for stage_type in STAGE_SEQUENCE:
        if stage_type == "reflection":
            continue
        if stage_type not in completed_steps:
            return stage_type
    return None


def _resolve_stage_type(progress: ProgressState) -> str | None:
    if progress.current_step:
        return progress.current_step
    if progress.mastery_status == "completed":
        return None
    return _next_standard_stage(progress.completed_steps)


def _progress_percent(completed_steps: list[str], mastery_status: str) -> float:
    if mastery_status == "completed":
        return 100.0
    standard_steps = [
        stage for stage in STAGE_SEQUENCE if stage != "reflection"]
    completed = len(
        [stage for stage in standard_steps if stage in completed_steps])
    return round((completed / len(standard_steps)) * 100, 1)


def _build_skill_overview(
    curriculum: GeneratedCurriculum,
    user_id: str,
    progress_states: list[ProgressState],
) -> list[RuntimeSkillProgress]:
    ordered = _ordered_subskills(curriculum)
    lookup = _progress_lookup(progress_states)
    overview: list[RuntimeSkillProgress] = []
    prior_completed = True
    for skill, subskill in ordered:
        progress = lookup.get((skill.skill_id, subskill.subskill_id)) or _default_progress(
            user_id, skill, subskill)
        unlocked = prior_completed
        overview.append(
            RuntimeSkillProgress(
                skill_id=skill.skill_id,
                skill_name=skill.skill_name,
                subskill_id=subskill.subskill_id,
                subskill_name=subskill.subskill_name,
                mastery_status=progress.mastery_status,
                progress_percent=progress.progress_percent,
                unlocked=unlocked,
            )
        )
        prior_completed = prior_completed and progress.mastery_status == "completed"
    return overview


def _resolve_selection(
    curriculum: GeneratedCurriculum,
    user_id: str,
    progress_states: list[ProgressState],
    selected_skill_id: str | None,
    selected_subskill_id: str | None,
) -> tuple[CurriculumSkill | None, CurriculumSubskill | None, ProgressState | None, list[RuntimeSkillProgress]]:
    ordered = _ordered_subskills(curriculum)
    lookup = _progress_lookup(progress_states)
    overview = _build_skill_overview(curriculum, user_id, progress_states)
    unlocked_pairs = {
        (entry.skill_id, entry.subskill_id)
        for entry in overview
        if entry.unlocked
    }
    requested_pair = None
    if selected_skill_id and selected_subskill_id:
        requested_pair = (selected_skill_id, selected_subskill_id)
    if requested_pair in unlocked_pairs:
        for skill, subskill in ordered:
            if (skill.skill_id, subskill.subskill_id) == requested_pair:
                progress = lookup.get(requested_pair) or _default_progress(
                    user_id, skill, subskill)
                return skill, subskill, progress, overview
    for skill, subskill in ordered:
        pair = (skill.skill_id, subskill.subskill_id)
        if pair not in unlocked_pairs:
            continue
        progress = lookup.get(pair) or _default_progress(
            user_id, skill, subskill)
        if progress.mastery_status != "completed":
            return skill, subskill, progress, overview
    return None, None, None, overview


def _next_step_payload(curriculum: GeneratedCurriculum, selected_pair: tuple[str, str] | None) -> dict[str, str] | None:
    ordered = _ordered_subskills(curriculum)
    if selected_pair is None:
        if not ordered:
            return None
        first_skill, first_subskill = ordered[0]
        return {
            "skill_id": first_skill.skill_id,
            "subskill_id": first_subskill.subskill_id,
            "stage_type": "introduction",
        }
    for index, (skill, subskill) in enumerate(ordered):
        if (skill.skill_id, subskill.subskill_id) != selected_pair:
            continue
        if index + 1 >= len(ordered):
            return None
        next_skill, next_subskill = ordered[index + 1]
        return {
            "skill_id": next_skill.skill_id,
            "subskill_id": next_subskill.subskill_id,
            "stage_type": "introduction",
        }
    return None


def _normalize_evaluation(submission: Any, *, user_id: str, skill_id: str, subskill_id: str, attempt: int) -> EvaluationResult:
    payload = dict(submission or {}) if isinstance(submission, dict) else {}
    answer_text = str(payload.get("answer", submission or "")).strip()
    passed = bool(payload.get("passed", bool(answer_text)))
    score = float(payload.get("score", 0.85 if passed else 0.35))
    errors = [str(item).strip() for item in list(
        payload.get("errors", [])) if str(item).strip()]
    if not passed and not errors:
        errors = ["incomplete reasoning"]
    feedback = str(payload.get(
        "feedback", "Passed final evaluation." if passed else "Targeted remediation is required before retry."))
    return EvaluationResult(
        evaluation_id=f"{user_id}-{skill_id}-{subskill_id}-evaluation-{attempt}",
        user_id=user_id,
        skill_id=skill_id,
        subskill_id=subskill_id,
        stage="evaluation",
        score=score,
        passed=passed,
        errors=errors,
        feedback=feedback,
        created_at=utc_now(),
    )


def _build_error_record(evaluation: EvaluationResult, attempt: int) -> ErrorRecord:
    error_type = evaluation.errors[0] if evaluation.errors else "incomplete reasoning"
    return ErrorRecord(
        error_id=f"{evaluation.user_id}-{evaluation.skill_id}-{evaluation.subskill_id}-error-{attempt}",
        user_id=evaluation.user_id,
        skill_id=evaluation.skill_id,
        subskill_id=evaluation.subskill_id,
        error_type=error_type,
        description=evaluation.feedback,
        correct_reasoning="Revisit the remediation guidance, then retry the final evaluation with clearer reasoning and a grounded workflow.",
        timestamp=utc_now(),
    )


def _persist_progress(
    repository,
    progress: ProgressState,
    *,
    services: WorkflowServices,
    previous_progress: ProgressState | None = None,
) -> None:
    if previous_progress is not None:
        _record_runtime_event(
            services,
            "learning.progression",
            {
                "skill_id": progress.skill_id,
                "subskill_id": progress.subskill_id,
                "from_stage": previous_progress.current_step,
                "to_stage": progress.current_step,
                "mastery_status": progress.mastery_status,
                "progress_percent": progress.progress_percent,
                "retry_count": progress.retry_count,
            },
        )
    destination = repository.save_progress(progress)
    _record_runtime_event(
        services,
        "learning.persistence",
        {
            "entity": "progress",
            "path": str(destination),
            "skill_id": progress.skill_id,
            "subskill_id": progress.subskill_id,
            "current_step": progress.current_step,
            "mastery_status": progress.mastery_status,
        },
    )


def _build_stage_evaluation_result(
    *,
    stage_name: str,
    user_id: str,
    skill_id: str,
    subskill_id: str,
    attempt: int,
    score: float,
    passed: bool,
    errors: list[str],
    misconceptions: list[str],
    critical_misconceptions: list[str],
    feedback: str,
    retry_required: bool,
    criteria_results: dict[str, float],
    supporting_evaluation_ids: list[str],
    parsed_output: dict[str, Any],
) -> EvaluationResult:
    return EvaluationResult(
        evaluation_id=f"{user_id}-{skill_id}-{subskill_id}-{stage_name}-{attempt}",
        user_id=user_id,
        skill_id=skill_id,
        subskill_id=subskill_id,
        stage=stage_name,
        score=score,
        passed=passed,
        errors=errors,
        misconceptions=misconceptions,
        critical_misconceptions=critical_misconceptions,
        feedback=feedback,
        retry_required=retry_required,
        criteria_results=criteria_results,
        supporting_evaluation_ids=supporting_evaluation_ids,
        parsed_output=parsed_output,
        created_at=utc_now(),
    )


def _load_runtime_context(state, _services):
    repository = state.shared["repository"]
    curriculum = repository.load_curriculum(state.shared["curriculum_id"])
    if curriculum is None:
        raise ValueError(
            f"Curriculum '{state.shared['curriculum_id']}' was not found.")
    bundle = repository.load_learning_state(
        curriculum_id=curriculum.curriculum_id,
        user_id=state.shared["user_id"],
    )
    return NodeResult(
        updates={
            "curriculum": curriculum,
            "progress_states": bundle.progress_states,
            "evaluation_results": bundle.evaluation_results,
            "error_records": bundle.error_records,
        }
    )


def _resolve_runtime_target(state, _services):
    curriculum = state.shared["curriculum"]
    evaluation_results = state.shared.get("evaluation_results", [])
    error_records = state.shared.get("error_records", [])
    skill, subskill, progress, overview = _resolve_selection(
        curriculum,
        state.shared["user_id"],
        state.shared.get("progress_states", []),
        state.shared.get("skill_id"),
        state.shared.get("subskill_id"),
    )
    if skill is None or subskill is None or progress is None:
        return NodeResult(
            updates={
                "skill_overview": overview,
                "current_progress": None,
                "current_stage": None,
                "selected_skill": None,
                "selected_subskill": None,
                "current_evaluations": [],
                "current_errors": [],
                "next_step": None,
            }
        )
    current_evaluations, current_errors = _subskill_records(
        evaluation_results,
        error_records,
        skill_id=skill.skill_id,
        subskill_id=subskill.subskill_id,
    )
    stage_type = _resolve_stage_type(progress)
    current_stage = (
        _hydrate_runtime_stage(
            _stage_by_type(subskill, stage_type),
            curriculum=curriculum,
            skill=skill,
            subskill=subskill,
            evaluations=current_evaluations,
            errors=current_errors,
        )
        if stage_type
        else None
    )
    next_step = None
    if progress.mastery_status == "completed":
        next_step = _next_step_payload(
            curriculum, (skill.skill_id, subskill.subskill_id))
    elif stage_type is not None:
        next_step = {
            "skill_id": skill.skill_id,
            "subskill_id": subskill.subskill_id,
            "stage_type": stage_type,
        }
    return NodeResult(
        updates={
            "skill_overview": overview,
            "selected_skill": skill,
            "selected_subskill": subskill,
            "current_progress": progress,
            "current_stage": current_stage,
            "current_evaluations": current_evaluations,
            "current_errors": current_errors,
            "next_step": next_step,
        }
    )


def _apply_runtime_action(state, services):
    repository = state.shared["repository"]
    curriculum = state.shared["curriculum"]
    skill = state.shared.get("selected_skill")
    subskill = state.shared.get("selected_subskill")
    progress = state.shared.get("current_progress")
    stage = state.shared.get("current_stage")
    action = str(state.shared.get("action", "view"))
    submission = state.shared.get("submission")
    progress_states = list(state.shared.get("progress_states", []))
    current_evaluations = list(state.shared.get("current_evaluations", []))
    current_errors = list(state.shared.get("current_errors", []))
    evaluation_result = None
    error_record = None

    if skill is None or subskill is None or progress is None or stage is None:
        snapshot = RuntimeSnapshot(
            curriculum_id=curriculum.curriculum_id,
            user_id=state.shared["user_id"],
            current_skill_id=None,
            current_subskill_id=None,
            current_stage_type=None,
            current_stage=None,
            progress=None,
            skill_overview=state.shared.get("skill_overview", []),
            next_step=None,
            completed=True,
        )
        return NodeResult(outputs={"runtime_snapshot": snapshot}, stop=True, status="completed")

    current_stage_type = stage.stage_type
    new_progress = progress
    if action == "view":
        pass
    elif current_stage_type == "introduction":
        if action != "advance":
            raise ValueError(
                "Introduction stages require the 'advance' action.")
        completed_steps = list(dict.fromkeys(
            [*progress.completed_steps, "introduction"]))
        new_progress = _build_progress_state(
            progress,
            current_stage="conceptual",
            completed_steps=completed_steps,
            mastery_status="in_progress",
            progress_percent=_progress_percent(completed_steps, "in_progress"),
            retry_count=progress.retry_count,
            remediation_state=dict(progress.remediation_state or {
                                   "status": "in_progress"}),
            latest_scores=dict(progress.latest_scores),
            latest_errors=list(progress.latest_errors),
            completed_subskills=list(progress.completed_subskills),
        )
        _persist_progress(
            repository,
            new_progress,
            services=services,
            previous_progress=progress,
        )
    elif current_stage_type in {"conceptual", "practical"}:
        if action != "submit" or submission in (None, ""):
            raise ValueError(
                f"Stage '{current_stage_type}' requires a non-empty submission.")
        if current_stage_type == "conceptual":
            conceptual_payload = _conceptual_assessment(
                stage,
                curriculum,
                skill,
                subskill,
                submission,
                services=services,
                evaluations=current_evaluations,
                errors=current_errors,
            )
            evaluation_result = _build_stage_evaluation_result(
                stage_name="conceptual",
                user_id=progress.user_id,
                skill_id=progress.skill_id,
                subskill_id=progress.subskill_id,
                attempt=_stage_attempt_count(
                    current_evaluations, "conceptual") + 1,
                score=conceptual_payload["conceptual_score"],
                passed=conceptual_payload["passed"],
                errors=list(conceptual_payload["misconceptions"]),
                misconceptions=list(conceptual_payload["misconceptions"]),
                critical_misconceptions=[],
                feedback=conceptual_payload["feedback"],
                retry_required=False,
                criteria_results=conceptual_payload["criteria_results"],
                supporting_evaluation_ids=[],
                parsed_output=dict(conceptual_payload.get(
                    "parsed_output", {}) or {}),
            )
            next_stage = "practical"
            latest_scores = {**dict(progress.latest_scores),
                             "conceptual": evaluation_result.score}
            latest_errors = list(evaluation_result.misconceptions)
        else:
            practical_payload = _practical_assessment(
                stage,
                subskill,
                submission,
                services=services,
            )
            evaluation_result = _build_stage_evaluation_result(
                stage_name="practical",
                user_id=progress.user_id,
                skill_id=progress.skill_id,
                subskill_id=progress.subskill_id,
                attempt=_stage_attempt_count(
                    current_evaluations, "practical") + 1,
                score=practical_payload["practical_score"],
                passed=practical_payload["passed"],
                errors=list(practical_payload["errors"]),
                misconceptions=[],
                critical_misconceptions=[],
                feedback=practical_payload["feedback"],
                retry_required=False,
                criteria_results=practical_payload["criteria_results"],
                supporting_evaluation_ids=[],
                parsed_output=dict(practical_payload.get(
                    "parsed_output", {}) or {}),
            )
            next_stage = "evaluation"
            latest_scores = {**dict(progress.latest_scores),
                             "practical": evaluation_result.score}
            latest_errors = list(evaluation_result.errors)
        evaluation_destination = repository.save_evaluation(evaluation_result)
        _record_runtime_event(
            services,
            "learning.evaluation",
            {
                "stage": current_stage_type,
                "result": evaluation_result.to_dict(),
            },
        )
        _record_runtime_event(
            services,
            "learning.persistence",
            {
                "entity": "evaluation",
                "path": str(evaluation_destination),
                "stage": current_stage_type,
                "evaluation_id": evaluation_result.evaluation_id,
            },
        )
        completed_steps = list(dict.fromkeys(
            [*progress.completed_steps, current_stage_type]))
        new_progress = _build_progress_state(
            progress,
            current_stage=next_stage,
            completed_steps=completed_steps,
            mastery_status="in_progress",
            progress_percent=_progress_percent(completed_steps, "in_progress"),
            retry_count=progress.retry_count,
            remediation_state={"status": "stage_completed",
                               "last_stage": current_stage_type},
            latest_scores=latest_scores,
            latest_errors=latest_errors,
            completed_subskills=list(progress.completed_subskills),
        )
        _persist_progress(
            repository,
            new_progress,
            services=services,
            previous_progress=progress,
        )
    elif current_stage_type == "evaluation":
        if action != "submit" or submission in (None, ""):
            raise ValueError("Evaluation requires a submission payload.")
        conceptual_result = _latest_stage_evaluation(
            current_evaluations, "conceptual")
        practical_result = _latest_stage_evaluation(
            current_evaluations, "practical")
        if conceptual_result is None or practical_result is None:
            raise ValueError(
                "Final evaluation requires completed conceptual and practical stage results.")
        prior_attempts = _stage_attempt_count(
            current_evaluations, "evaluation")
        evaluator = dict(getattr(services, "extras", {})
                         or {}).get("evaluator")
        if callable(evaluator):
            evaluation_result = evaluator(
                submission,
                user_id=progress.user_id,
                skill_id=progress.skill_id,
                subskill_id=progress.subskill_id,
                attempt=prior_attempts + 1,
                conceptual_result=conceptual_result,
                practical_result=practical_result,
                stage=stage,
            )
            if not isinstance(evaluation_result, EvaluationResult):
                payload = dict(evaluation_result or {})
                evaluation_result = _build_stage_evaluation_result(
                    stage_name="evaluation",
                    user_id=progress.user_id,
                    skill_id=progress.skill_id,
                    subskill_id=progress.subskill_id,
                    attempt=prior_attempts + 1,
                    score=_safe_float(payload.get(
                        "final_score", payload.get("score", 0.0)), 0.0),
                    passed=bool(payload.get("passed", False)),
                    errors=_unique_strings(payload.get(
                        "critical_misconceptions", payload.get("errors", []))),
                    misconceptions=_unique_strings(payload.get(
                        "misconceptions", payload.get("errors", []))),
                    critical_misconceptions=_unique_strings(payload.get(
                        "critical_misconceptions", payload.get("errors", []))),
                    feedback=str(payload.get("feedback", "")).strip(),
                    retry_required=bool(payload.get(
                        "retry_required", not payload.get("passed", False))),
                    criteria_results={
                        "conceptual": conceptual_result.score,
                        "practical": practical_result.score,
                        "integration": _safe_float(payload.get("integration_score", 0.0), 0.0),
                    },
                    supporting_evaluation_ids=[
                        conceptual_result.evaluation_id, practical_result.evaluation_id],
                    parsed_output=payload,
                )
        else:
            final_payload = _final_aggregation(
                stage,
                curriculum,
                skill,
                subskill,
                conceptual_result,
                practical_result,
                submission,
                services=services,
                evaluations=current_evaluations,
                errors=current_errors,
            )
            evaluation_result = _build_stage_evaluation_result(
                stage_name="evaluation",
                user_id=progress.user_id,
                skill_id=progress.skill_id,
                subskill_id=progress.subskill_id,
                attempt=prior_attempts + 1,
                score=final_payload["final_score"],
                passed=final_payload["passed"],
                errors=list(final_payload["critical_misconceptions"]),
                misconceptions=_unique_strings(
                    list(conceptual_result.misconceptions) + list(practical_result.errors)),
                critical_misconceptions=list(
                    final_payload["critical_misconceptions"]),
                feedback=final_payload["feedback"],
                retry_required=bool(final_payload["retry_required"]),
                criteria_results={
                    "conceptual": conceptual_result.score,
                    "practical": practical_result.score,
                    "integration": final_payload["integration_score"],
                },
                supporting_evaluation_ids=[
                    conceptual_result.evaluation_id, practical_result.evaluation_id],
                parsed_output=dict(final_payload.get(
                    "parsed_output", {}) or {}),
            )
        evaluation_destination = repository.save_evaluation(evaluation_result)
        _record_runtime_event(
            services,
            "learning.evaluation",
            {
                "stage": "evaluation",
                "result": evaluation_result.to_dict(),
                "supporting_results": [conceptual_result.to_dict(), practical_result.to_dict()],
            },
        )
        _record_runtime_event(
            services,
            "learning.persistence",
            {
                "entity": "evaluation",
                "path": str(evaluation_destination),
                "stage": "evaluation",
                "evaluation_id": evaluation_result.evaluation_id,
            },
        )
        completed_steps = list(progress.completed_steps)
        if evaluation_result.passed:
            completed_steps = list(dict.fromkeys(
                [*completed_steps, "evaluation"]))
            completed_subskills = _completed_subskills(
                progress_states, skill.skill_id)
            if progress.subskill_id not in completed_subskills:
                completed_subskills.append(progress.subskill_id)
            completed_subskills = sorted(completed_subskills)
            new_progress = _build_progress_state(
                progress,
                current_stage="",
                completed_steps=completed_steps,
                mastery_status="completed",
                progress_percent=100.0,
                retry_count=progress.retry_count,
                remediation_state={"status": "completed"},
                latest_scores={
                    **dict(progress.latest_scores),
                    "conceptual": conceptual_result.score,
                    "practical": practical_result.score,
                    "final": evaluation_result.score,
                },
                latest_errors=[],
                completed_subskills=completed_subskills,
            )
        else:
            reflection_stage = _hydrate_runtime_stage(
                _stage_by_type(subskill, "reflection"),
                curriculum=curriculum,
                skill=skill,
                subskill=subskill,
                evaluations=current_evaluations + [evaluation_result],
                errors=current_errors,
            )
            remediation_payload = _generate_remediation(
                reflection_stage,
                curriculum,
                skill,
                subskill,
                evaluation_result,
                services=services,
                evaluations=current_evaluations + [evaluation_result],
                errors=current_errors,
            )
            error_record = ErrorRecord(
                error_id=f"{evaluation_result.user_id}-{evaluation_result.skill_id}-{evaluation_result.subskill_id}-error-{prior_attempts + 1}",
                user_id=evaluation_result.user_id,
                skill_id=evaluation_result.skill_id,
                subskill_id=evaluation_result.subskill_id,
                error_type=(remediation_payload["main_errors"][0]
                            if remediation_payload["main_errors"] else "incomplete reasoning"),
                description=evaluation_result.feedback,
                correct_reasoning=remediation_payload["correct_reasoning"],
                main_errors=remediation_payload["main_errors"],
                reinforcement_task=remediation_payload["reinforcement_task"],
                retry_focus=remediation_payload["retry_focus"],
                needs_retry=True,
                related_evaluation_id=evaluation_result.evaluation_id,
                score_snapshot={
                    "conceptual": conceptual_result.score,
                    "practical": practical_result.score,
                    "final": evaluation_result.score,
                },
                timestamp=utc_now(),
            )
            error_destination = repository.save_error(error_record)
            _record_runtime_event(
                services,
                "learning.persistence",
                {
                    "entity": "error",
                    "path": str(error_destination),
                    "error_id": error_record.error_id,
                    "related_evaluation_id": error_record.related_evaluation_id,
                },
            )
            new_progress = _build_progress_state(
                progress,
                current_stage="reflection",
                completed_steps=completed_steps,
                mastery_status="needs_remediation",
                progress_percent=_progress_percent(
                    completed_steps, "needs_remediation"),
                retry_count=progress.retry_count + 1,
                remediation_state={
                    "status": "needs_remediation",
                    "main_errors": remediation_payload["main_errors"],
                    "reinforcement_task": remediation_payload["reinforcement_task"],
                    "retry_focus": remediation_payload["retry_focus"],
                    "related_evaluation_id": evaluation_result.evaluation_id,
                },
                latest_scores={
                    **dict(progress.latest_scores),
                    "conceptual": conceptual_result.score,
                    "practical": practical_result.score,
                    "final": evaluation_result.score,
                },
                latest_errors=list(error_record.main_errors),
                completed_subskills=list(progress.completed_subskills),
            )
        _persist_progress(
            repository,
            new_progress,
            services=services,
            previous_progress=progress,
        )
    elif current_stage_type == "reflection":
        if action != "advance":
            raise ValueError(
                "Reflection remediation requires the 'advance' action to unlock a retry.")
        completed_steps = list(dict.fromkeys(
            [*progress.completed_steps, "reflection"]))
        new_progress = _build_progress_state(
            progress,
            current_stage="evaluation",
            completed_steps=completed_steps,
            mastery_status="retry_ready",
            progress_percent=_progress_percent(
                progress.completed_steps, "retry_ready"),
            retry_count=progress.retry_count,
            remediation_state={
                **dict(progress.remediation_state), "status": "retry_ready"},
            latest_scores=dict(progress.latest_scores),
            latest_errors=list(progress.latest_errors),
            completed_subskills=list(progress.completed_subskills),
        )
        _persist_progress(
            repository,
            new_progress,
            services=services,
            previous_progress=progress,
        )
    else:
        raise ValueError(f"Unsupported runtime stage '{current_stage_type}'.")

    _record_runtime_event(
        services,
        "learning.state_update",
        {"progress": new_progress.to_dict()},
    )

    refreshed_bundle = repository.load_learning_state(
        curriculum_id=curriculum.curriculum_id,
        user_id=state.shared["user_id"],
    )
    selected_pair = (new_progress.skill_id, new_progress.subskill_id)
    next_stage_type = _resolve_stage_type(new_progress)
    refreshed_evaluations, refreshed_errors = _subskill_records(
        refreshed_bundle.evaluation_results,
        refreshed_bundle.error_records,
        skill_id=skill.skill_id,
        subskill_id=subskill.subskill_id,
    )
    next_stage = (
        _hydrate_runtime_stage(
            _stage_by_type(subskill, next_stage_type),
            curriculum=curriculum,
            skill=skill,
            subskill=subskill,
            evaluations=refreshed_evaluations,
            errors=refreshed_errors,
        )
        if next_stage_type
        else None
    )
    next_step = None
    if new_progress.mastery_status == "completed":
        next_step = _next_step_payload(curriculum, selected_pair)
    elif next_stage_type is not None:
        next_step = {
            "skill_id": new_progress.skill_id,
            "subskill_id": new_progress.subskill_id,
            "stage_type": next_stage_type,
        }
    snapshot = RuntimeSnapshot(
        curriculum_id=curriculum.curriculum_id,
        user_id=state.shared["user_id"],
        current_skill_id=skill.skill_id,
        current_subskill_id=subskill.subskill_id,
        current_stage_type=next_stage.stage_type if next_stage else None,
        current_stage=next_stage,
        progress=new_progress,
        skill_overview=_build_skill_overview(
            curriculum, state.shared["user_id"], refreshed_bundle.progress_states),
        next_step=next_step,
        requires_submission=bool(
            next_stage and next_stage.stage_type in SUBMISSION_REQUIRED_STAGES),
        remediation_required=bool(
            next_stage and next_stage.stage_type == "reflection"),
        evaluation_result=evaluation_result,
        error_record=error_record,
        completed=next_step is None and new_progress.mastery_status == "completed",
    )
    return NodeResult(outputs={"runtime_snapshot": snapshot}, stop=True, status="completed")


def build_learning_runtime_runner() -> WorkflowRunner:
    return WorkflowRunner(
        [
            WorkflowNode(name="load_runtime_context", handler=_load_runtime_context,
                         default_next="resolve_runtime_target"),
            WorkflowNode(name="resolve_runtime_target",
                         handler=_resolve_runtime_target, default_next="apply_runtime_action"),
            WorkflowNode(name="apply_runtime_action",
                         handler=_apply_runtime_action),
        ],
        name="learning_runtime_workflow",
    )


def run_learning_runtime(
    *,
    repository,
    curriculum_id: str,
    user_id: str,
    action: str = "view",
    skill_id: str | None = None,
    subskill_id: str | None = None,
    submission: Any = None,
    services: WorkflowServices | None = None,
):
    runtime = services or WorkflowServices()
    state = init_state(
        run_id=f"runtime-{curriculum_id}-{user_id}",
        objective="Navigate and complete a persisted learning curriculum with deterministic progression.",
        shared={
            "repository": repository,
            "curriculum_id": curriculum_id,
            "user_id": user_id,
            "action": action,
            "skill_id": skill_id,
            "subskill_id": subskill_id,
            "submission": submission,
        },
        metadata={"workflow_name": "learning_runtime_workflow"},
    )
    return build_learning_runtime_runner().run(state, start_at="load_runtime_context", services=runtime)
