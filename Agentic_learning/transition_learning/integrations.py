"""Integration helpers that connect TransitionAI to real upstream inputs and optional LLM seams."""

from __future__ import annotations

import json
from dataclasses import replace
from typing import Any

from SkillUp_SHZurich.Agentic_learning.starter_kit.prompts import PromptTemplate
from SkillUp_SHZurich.Agentic_learning.transition_learning.contracts import (
    StagePayload,
    TargetRole,
    UserProfileInput,
)


_STAGE_ENRICHMENT_TEMPLATE = PromptTemplate.from_text(
    "stage_enrichment",
    """
TASK:
You are an expert career-transition curriculum designer. Rewrite the learner-facing content for one fixed learning stage so it teaches SUBSKILL_NAME (part of SKILL_NAME) to this specific learner. Ground every explanation in the learner's prior experience: draw an explicit analogy from their previous roles, tasks, tools, or workflows in the USER_PROFILE to the demands of the TARGET_ROLE. Keep the content concrete, operational, and employability-oriented.

RULES:
- Keep the curriculum structure fixed: do not invent new stage types, rename the stage, or change stage order.
- Only enrich the content of the given STAGE; preserve its stage_type and pedagogical intent.
- Use the learner's background for analogies; if no relevant background exists, stay concrete and practical without inventing experience.
- Write "instructions" as clear, motivating, learner-facing text for this stage.
- Return ONLY a single JSON object, with no markdown fences and no text before or after it, with exactly these keys: instructions (string), context (object), expected_output (object), metadata (object).

USER_PROFILE:
{{USER_PROFILE}}

TARGET_ROLE:
{{TARGET_ROLE}}

SKILL_NAME:
{{SKILL_NAME}}

SUBSKILL_NAME:
{{SUBSKILL_NAME}}

STAGE:
{{STAGE}}
""",
)

_EVALUATION_TEMPLATE = PromptTemplate.from_text(
    "evaluation",
    """
TASK:
FINAL_EVALUATION_TASK

RULES:
- Keep the evaluation structured and deterministic.
- Return only JSON with keys: score, passed, errors, feedback.
- Score must be a number between 0 and 1.

STAGE:
{{STAGE}}

SUBMISSION:
{{SUBMISSION}}
""",
)

_CONCEPTUAL_EVALUATION_TEMPLATE = PromptTemplate.from_text(
    "conceptual_evaluation",
    """
TASK:
You are a rigorous but supportive conceptual examiner for a career-transition learning program. Judge whether the learner's SUBMISSION demonstrates genuine conceptual understanding of the subskill described in the STAGE. Score against the stage's rubric and expected concepts, not against surface wording. Detect misconceptions and give feedback the learner can act on, connecting it to their background in PROFILE_CONTEXT where helpful.

RULES:
- Evaluate conceptual reasoning against the rubric and expected concepts found in the STAGE.
- Reward correct reasoning and concept transfer; penalize memorized or superficial answers.
- conceptual_score must be a number between 0 and 1.
- "passed" must reflect whether the learner meets the conceptual mastery bar with no critical misconception.
- Return ONLY a single JSON object, with no markdown fences or surrounding text, with exactly these keys: conceptual_score (number 0-1), misconceptions (array of strings), feedback (string), passed (boolean).

STAGE:
{{STAGE}}

PROFILE_CONTEXT:
{{PROFILE_CONTEXT}}

SUBMISSION:
{{SUBMISSION}}
""",
)

_PRACTICAL_EVALUATION_TEMPLATE = PromptTemplate.from_text(
    "practical_evaluation",
    """
TASK:
You are evaluating a practical, operational exercise in a career-transition learning program. Judge whether the learner's SUBMISSION correctly applies the subskill to a realistic workflow task as specified in the STAGE (its required elements, expected outcomes, and workflow steps). Prefer deterministic judgment where the expected result is explicit, and identify concrete execution errors.

RULES:
- Evaluate practical execution against the required elements and expected outcomes found in the STAGE.
- Prefer deterministic judgment where the answer is explicit.
- Credit correct, usable execution (trigger, steps, decision points, safeguards); flag missing or incorrect required elements as errors.
- practical_score must be a number between 0 and 1.
- "passed" must reflect operational competence, not just effort.
- Return ONLY a single JSON object, with no markdown fences or surrounding text, with exactly these keys: practical_score (number 0-1), errors (array of strings), feedback (string), passed (boolean).

STAGE:
{{STAGE}}

SUBMISSION:
{{SUBMISSION}}
""",
)

_FINAL_AGGREGATION_TEMPLATE = PromptTemplate.from_text(
    "final_aggregation",
    """
TASK:
You are the final mastery judge for a subskill in a career-transition learning program. Combine the CONCEPTUAL_RESULT and the PRACTICAL_RESULT with the learner's FINAL_SUBMISSION into a single mastery decision for the subskill described in the STAGE. A learner masters the subskill only when both conceptual understanding and practical execution are sound and no critical misconception remains.

RULES:
- Aggregate the conceptual and practical results into a final mastery judgment; do not excuse a weak component because the other is strong.
- final_score must be a number between 0 and 1.
- List any misconception serious enough to block mastery in critical_misconceptions.
- Set retry_required to true whenever the learner has not yet mastered the subskill.
- Return ONLY a single JSON object, with no markdown fences or surrounding text, with exactly these keys: final_score (number 0-1), passed (boolean), critical_misconceptions (array of strings), retry_required (boolean), feedback (string).

STAGE:
{{STAGE}}

CONCEPTUAL_RESULT:
{{CONCEPTUAL_RESULT}}

PRACTICAL_RESULT:
{{PRACTICAL_RESULT}}

FINAL_SUBMISSION:
{{FINAL_SUBMISSION}}
""",
)

_REMEDIATION_TEMPLATE = PromptTemplate.from_text(
    "remediation",
    """
TASK:
You are a remediation coach in a career-transition learning program. The learner failed the final evaluation captured in EVALUATION. Produce targeted remediation that fixes the specific mistakes: name the main errors, explain the correct reasoning clearly, and design one focused reinforcement task that rebuilds the weak area. Use the learner's background in PROFILE_CONTEXT to make the reinforcement task concrete and relevant.

RULES:
- Generate targeted remediation from the actual mistakes and score profile in EVALUATION, not generic advice.
- correct_reasoning must directly address why the learner's approach was wrong and what correct reasoning looks like.
- reinforcement_task must be a single, concrete, doable exercise focused on the failed concepts.
- retry_focus must list the specific concepts or skills the retry should target.
- Return ONLY a single JSON object, with no markdown fences or surrounding text, with exactly these keys: main_errors (array of strings), correct_reasoning (string), reinforcement_task (string), retry_focus (array of strings).

STAGE:
{{STAGE}}

PROFILE_CONTEXT:
{{PROFILE_CONTEXT}}

EVALUATION:
{{EVALUATION}}
""",
)


def _normalize_skill_names(values: list[Any]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for item in list(values or []):
        skill_name = str(item).strip().lower()
        if not skill_name or skill_name in seen:
            continue
        seen.add(skill_name)
        normalized.append(skill_name)
    return normalized


def _extract_json_object(raw_text: str) -> dict[str, Any] | None:
    text = str(raw_text or "").strip()
    if not text:
        return None
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        parsed = json.loads(text[start: end + 1])
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _record_learning_event(
    logger: Any,
    event_type: str,
    payload: dict[str, Any],
    *,
    level: str = "debug",
) -> None:
    if logger is None or not hasattr(logger, "record"):
        return
    logger.record(event_type, payload, level=level)


def _structured_llm_call(
    template: PromptTemplate,
    dynamic_sections: dict[str, Any],
    *,
    llm: Any,
    logger: Any = None,
    prompt_name: str,
    metadata: dict[str, Any],
) -> dict[str, Any] | None:
    if llm is None or not hasattr(llm, "generate"):
        _record_learning_event(
            logger,
            "learning.generation_skipped",
            {"prompt_name": prompt_name, "metadata": metadata,
                "reason": "llm_unavailable"},
        )
        return None
    prompt_text = template.render(dynamic_sections)
    _record_learning_event(
        logger,
        "learning.input",
        {"prompt_name": prompt_name, "metadata": metadata, "input": dynamic_sections},
    )
    _record_learning_event(
        logger,
        "learning.prompt",
        {"prompt_name": prompt_name, "metadata": metadata, "prompt": prompt_text},
    )
    raw_output = llm.generate(prompt_text, metadata=metadata)
    _record_learning_event(
        logger,
        "learning.raw_output",
        {"prompt_name": prompt_name, "metadata": metadata, "raw_output": raw_output},
    )
    parsed_output = _extract_json_object(raw_output)
    _record_learning_event(
        logger,
        "learning.parsed_output",
        {"prompt_name": prompt_name, "metadata": metadata,
            "parsed_output": parsed_output},
    )
    if parsed_output is None:
        _record_learning_event(
            logger,
            "learning.generation_parse_failed",
            {"prompt_name": prompt_name, "metadata": metadata,
                "raw_output": raw_output},
        )
    return parsed_output


def generate_stage_payload_with_llm(
    stage: StagePayload,
    *,
    profile: UserProfileInput,
    target_role: TargetRole,
    skill_name: str,
    subskill_name: str,
    llm: Any,
    logger: Any = None,
) -> StagePayload | None:
    prompt_stage = stage.to_dict()
    authoring_prompt = str(stage.metadata.get(
        "authoring_prompt", "") or "").strip()
    if authoring_prompt:
        prompt_stage["instructions"] = authoring_prompt
        prompt_stage["learner_visible_instructions"] = stage.instructions
    payload = _structured_llm_call(
        _STAGE_ENRICHMENT_TEMPLATE,
        {
            "USER_PROFILE": profile.to_dict(),
            "TARGET_ROLE": target_role.to_dict(),
            "SKILL_NAME": skill_name,
            "SUBSKILL_NAME": subskill_name,
            "STAGE": prompt_stage,
        },
        llm=llm,
        logger=logger,
        prompt_name="stage_enrichment",
        metadata={
            "task": "stage_enrichment",
            "stage_id": stage.stage_id,
            "stage_type": stage.stage_type,
        },
    )
    if payload is None:
        return None
    instructions = str(payload.get("instructions", "")
                       ).strip() or stage.instructions
    context = dict(stage.context)
    if isinstance(payload.get("context"), dict):
        context.update(dict(payload.get("context") or {}))
    expected_output = dict(stage.expected_output)
    if isinstance(payload.get("expected_output"), dict):
        expected_output.update(dict(payload.get("expected_output") or {}))
    metadata = dict(stage.metadata)
    if isinstance(payload.get("metadata"), dict):
        metadata.update(dict(payload.get("metadata") or {}))
    metadata["generation_mode"] = "llm_enriched"
    _record_learning_event(
        logger,
        "learning.stage_content_parsed",
        {
            "stage_id": stage.stage_id,
            "stage_type": stage.stage_type,
            "parsed_stage_content": instructions,
            "authoring_prompt": authoring_prompt,
        },
    )
    return replace(
        stage,
        instructions=instructions,
        context=context,
        expected_output=expected_output,
        metadata=metadata,
    )


def evaluate_conceptual_with_llm(
    stage: StagePayload,
    submission: Any,
    *,
    profile_context: dict[str, Any],
    llm: Any,
    logger: Any = None,
) -> dict[str, Any] | None:
    payload = _structured_llm_call(
        _CONCEPTUAL_EVALUATION_TEMPLATE,
        {
            "STAGE": stage.to_dict(),
            "PROFILE_CONTEXT": profile_context,
            "SUBMISSION": submission,
        },
        llm=llm,
        logger=logger,
        prompt_name="conceptual_evaluation",
        metadata={"task": "conceptual_evaluation", "stage_id": stage.stage_id},
    )
    if payload is None:
        return None
    try:
        conceptual_score = float(payload.get("conceptual_score", 0.0) or 0.0)
    except (TypeError, ValueError):
        return None
    conceptual_score = max(0.0, min(1.0, conceptual_score))
    return {
        "conceptual_score": conceptual_score,
        "misconceptions": _normalize_skill_names(payload.get("misconceptions", [])),
        "feedback": str(payload.get("feedback", "")).strip(),
        "passed": bool(payload.get("passed", False)),
        "parsed_output": payload,
    }


def evaluate_practical_with_llm(
    stage: StagePayload,
    submission: Any,
    *,
    llm: Any,
    logger: Any = None,
) -> dict[str, Any] | None:
    payload = _structured_llm_call(
        _PRACTICAL_EVALUATION_TEMPLATE,
        {
            "STAGE": stage.to_dict(),
            "SUBMISSION": submission,
        },
        llm=llm,
        logger=logger,
        prompt_name="practical_evaluation",
        metadata={"task": "practical_evaluation", "stage_id": stage.stage_id},
    )
    if payload is None:
        return None
    try:
        practical_score = float(payload.get("practical_score", 0.0) or 0.0)
    except (TypeError, ValueError):
        return None
    practical_score = max(0.0, min(1.0, practical_score))
    return {
        "practical_score": practical_score,
        "errors": _normalize_skill_names(payload.get("errors", [])),
        "feedback": str(payload.get("feedback", "")).strip(),
        "passed": bool(payload.get("passed", False)),
        "parsed_output": payload,
    }


def aggregate_final_with_llm(
    stage: StagePayload,
    *,
    conceptual_result: dict[str, Any],
    practical_result: dict[str, Any],
    final_submission: Any,
    llm: Any,
    logger: Any = None,
) -> dict[str, Any] | None:
    payload = _structured_llm_call(
        _FINAL_AGGREGATION_TEMPLATE,
        {
            "STAGE": stage.to_dict(),
            "CONCEPTUAL_RESULT": conceptual_result,
            "PRACTICAL_RESULT": practical_result,
            "FINAL_SUBMISSION": final_submission,
        },
        llm=llm,
        logger=logger,
        prompt_name="final_aggregation",
        metadata={"task": "final_aggregation", "stage_id": stage.stage_id},
    )
    if payload is None:
        return None
    try:
        final_score = float(payload.get("final_score", 0.0) or 0.0)
    except (TypeError, ValueError):
        return None
    final_score = max(0.0, min(1.0, final_score))
    return {
        "final_score": final_score,
        "passed": bool(payload.get("passed", False)),
        "critical_misconceptions": _normalize_skill_names(
            payload.get("critical_misconceptions", [])
        ),
        "retry_required": bool(payload.get("retry_required", not payload.get("passed", False))),
        "feedback": str(payload.get("feedback", "")).strip(),
        "parsed_output": payload,
    }


def generate_remediation_with_llm(
    stage: StagePayload,
    *,
    profile_context: dict[str, Any],
    evaluation: dict[str, Any],
    llm: Any,
    logger: Any = None,
) -> dict[str, Any] | None:
    payload = _structured_llm_call(
        _REMEDIATION_TEMPLATE,
        {
            "STAGE": stage.to_dict(),
            "PROFILE_CONTEXT": profile_context,
            "EVALUATION": evaluation,
        },
        llm=llm,
        logger=logger,
        prompt_name="remediation",
        metadata={"task": "remediation", "stage_id": stage.stage_id},
    )
    if payload is None:
        return None
    return {
        "main_errors": _normalize_skill_names(payload.get("main_errors", [])),
        "correct_reasoning": str(payload.get("correct_reasoning", "")).strip(),
        "reinforcement_task": str(payload.get("reinforcement_task", "")).strip(),
        "retry_focus": _normalize_skill_names(payload.get("retry_focus", [])),
        "parsed_output": payload,
    }
