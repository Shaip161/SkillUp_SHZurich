"""Offline curriculum generation workflow for the TransitionAI learning product."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from SkillUp_SHZurich.Agentic_learning.starter_kit.state import init_state
from SkillUp_SHZurich.Agentic_learning.starter_kit.workflow import NodeResult, WorkflowNode, WorkflowRunner, WorkflowServices
from SkillUp_SHZurich.Agentic_learning.transition_learning.contracts import (
    CurriculumSkill,
    CurriculumSubskill,
    GeneratedCurriculum,
    SkillGapItem,
    StagePayload,
    TargetRole,
    UserProfileInput,
)
from SkillUp_SHZurich.Agentic_learning.transition_learning.integrations import generate_stage_payload_with_llm
from SkillUp_SHZurich.Agentic_learning.transition_learning.knowledge_base import STAGE_SEQUENCE, select_catalog_skills


def _record_generation_event(logger: Any, event_type: str, payload: dict[str, Any]) -> None:
    if logger is None or not hasattr(logger, "record"):
        return
    logger.record(event_type, payload, level="debug")


def _render_stage_content(
    stage: StagePayload,
    *,
    profile: UserProfileInput,
    target_role: TargetRole,
    subskill: CurriculumSubskill,
    subskill_name: str,
    contextual_analogy: str,
) -> str:
    examples = ", ".join(subskill.example_workflows[:2])
    examples_clause = f" Examples: {examples}." if examples else ""
    analogy_clause = f" {contextual_analogy}" if contextual_analogy else ""
    role_clause = (
        f" This is tailored for your move from {profile.current_role} to {target_role.title}."
        if profile.current_role.strip() and target_role.title.strip()
        else ""
    )

    if stage.stage_type == "introduction":
        return (
            f"{subskill_name} helps you {subskill.objective.lower()}.{role_clause}"
            f" Focus on the key ideas, why they matter operationally, and where they show up in real workflows."
            f"{analogy_clause}{examples_clause}"
        ).strip()
    if stage.stage_type == "conceptual":
        return (
            f"Explain how {subskill_name} works and why it matters in an operational workflow.{role_clause}"
            f" In your answer, cover the core concept, the reasoning behind it, and the main mistakes to avoid."
            f"{analogy_clause}{examples_clause}"
        ).strip()
    if stage.stage_type == "practical":
        return (
            f"Apply {subskill_name} to a realistic workflow task.{role_clause}"
            f" Produce a concrete, usable response that shows the trigger, key steps, decision points, and safeguards."
            f"{analogy_clause}{examples_clause}"
        ).strip()
    if stage.stage_type == "evaluation":
        return (
            f"Give a final answer that combines the concept and the practical execution for {subskill_name}.{role_clause}"
            f" Show that you can explain the approach clearly and apply it in a workflow that would hold up in practice."
            f"{analogy_clause}{examples_clause}"
        ).strip()
    if stage.stage_type == "reflection":
        return (
            f"Review the weak points in your work on {subskill_name} and prepare for a stronger retry.{role_clause}"
            f" Focus on the specific reasoning gaps, execution mistakes, and what you would change next time."
            f"{analogy_clause}{examples_clause}"
        ).strip()
    return stage.instructions


def _target_role_from_input(target_role: Any) -> TargetRole:
    if isinstance(target_role, TargetRole):
        return target_role
    payload = dict(target_role or {})
    return TargetRole(
        role_id=str(payload.get("role_id", "unknown-role")),
        title=str(payload.get("title", "Unknown target role")),
        industry=str(payload.get("industry", "Unknown industry")),
    )


def _skill_gap_items_from_input(missing_skills: list[Any]) -> list[SkillGapItem]:
    gap_items: list[SkillGapItem] = []
    for index, item in enumerate(list(missing_skills or []), start=1):
        if isinstance(item, SkillGapItem):
            gap_items.append(item)
            continue
        if isinstance(item, str):
            skill_name = item.strip().lower()
            if not skill_name:
                continue
            gap_items.append(SkillGapItem(
                skill_name=skill_name, priority=index))
            continue
        payload = dict(item or {})
        skill_name = str(
            payload.get("skill_name")
            or payload.get("name")
            or payload.get("skill")
            or ""
        ).strip().lower()
        if not skill_name:
            continue
        gap_items.append(
            SkillGapItem(
                skill_name=skill_name,
                gap_type=str(payload.get("gap_type", "missing")),
                priority=int(payload.get("priority", index) or index),
                source=str(payload.get("source", "matching")),
            )
        )
    return gap_items


def _contextualize_stage(
    stage: StagePayload,
    *,
    profile: UserProfileInput,
    target_role: TargetRole,
    skill_name: str,
    subskill_name: str,
    subskill: CurriculumSubskill,
) -> StagePayload:
    context_anchor = (
        (profile.analogous_experiences or profile.previous_workflows or profile.previous_tasks or profile.previous_roles)
        or list(profile.explicit_skills)
    )
    contextual_analogy = ""
    if context_anchor:
        contextual_analogy = (
            f"Tie {subskill_name} to the learner's experience with {context_anchor[0]}."
        )
    context = {
        **dict(stage.context),
        "current_role": profile.current_role,
        "target_role": target_role.title,
        "target_industry": target_role.industry,
        "industry_background": profile.industry_background,
        "known_skills": list(profile.explicit_skills),
        "previous_roles": list(profile.previous_roles),
        "previous_tasks": list(profile.previous_tasks),
        "previous_workflows": list(profile.previous_workflows),
        "analogous_experiences": list(profile.analogous_experiences),
        "certifications": list(profile.certifications),
        "known_tools": list(profile.known_tools),
        "skill_name": skill_name,
        "subskill_name": subskill_name,
        "contextual_analogy": contextual_analogy,
    }
    authoring_prompt = (
        f"{stage.instructions} "
        f"Relate it to the learner's background as {profile.current_role} and to the target role {target_role.title}."
    )
    if contextual_analogy:
        authoring_prompt = f"{authoring_prompt} {contextual_analogy}"
    if subskill.example_workflows:
        authoring_prompt = (
            f"{authoring_prompt} Use examples such as {', '.join(subskill.example_workflows[:2])}."
        )
    if profile.industry_background:
        authoring_prompt = (
            f"{authoring_prompt} Keep the framing grounded in {profile.industry_background}."
        )
    learner_instructions = _render_stage_content(
        stage,
        profile=profile,
        target_role=target_role,
        subskill=subskill,
        subskill_name=subskill_name,
        contextual_analogy=contextual_analogy,
    )
    expected_output = {
        **dict(stage.expected_output),
        "contextual_analogy": contextual_analogy,
        "context_sources": [
            source_name
            for source_name, values in (
                ("previous_roles", profile.previous_roles),
                ("previous_tasks", profile.previous_tasks),
                ("previous_workflows", profile.previous_workflows),
                ("analogous_experiences", profile.analogous_experiences),
                ("known_tools", profile.known_tools),
            )
            if values
        ],
    }
    metadata = {
        **dict(stage.metadata),
        "generated_by": "offline_curriculum_generation",
        "target_role": target_role.title,
        "context_sources_used": expected_output["context_sources"],
        "authoring_prompt": authoring_prompt,
    }
    return replace(
        stage,
        instructions=learner_instructions,
        context=context,
        expected_output=expected_output,
        metadata=metadata,
    )


def validate_generated_curriculum(curriculum: GeneratedCurriculum) -> GeneratedCurriculum:
    if not curriculum.target_role.title.strip():
        raise ValueError(
            "Generated curriculum is missing a target role title.")
    if not curriculum.skills:
        raise ValueError(
            "Generated curriculum must contain at least one supported skill.")
    if len(curriculum.skills) > 6:
        raise ValueError(
            "Generated curriculum cannot contain more than 6 skills.")
    for skill in curriculum.skills:
        if len(skill.subskills) != 5:
            raise ValueError(
                f"Curriculum skill '{skill.skill_name}' must contain exactly 5 sequential subskills."
            )
        if not skill.subskills:
            raise ValueError(
                f"Curriculum skill '{skill.skill_name}' must contain subskills.")
        for subskill in skill.subskills:
            if tuple(stage.stage_type for stage in subskill.stages) != STAGE_SEQUENCE:
                raise ValueError(
                    f"Subskill '{subskill.subskill_name}' does not follow the fixed stage order."
                )
    return curriculum


def _normalize_inputs(state, _services):
    profile = UserProfileInput.from_mapping(
        state.shared.get("user_profile", {}))
    target_role = _target_role_from_input(state.shared.get("target_role", {}))
    missing_skills = _skill_gap_items_from_input(
        state.shared.get("missing_skills", []))
    return NodeResult(
        updates={
            "normalized_user_profile": profile,
            "normalized_target_role": target_role,
            "normalized_missing_skills": missing_skills,
        },
        outputs={"normalized_missing_skill_names": [
            item.skill_name for item in missing_skills]},
    )


def _select_skill_skeletons(state, _services):
    missing_skills = [item.skill_name for item in state.shared.get(
        "normalized_missing_skills", [])]
    selected_skills = select_catalog_skills(missing_skills)
    return NodeResult(
        updates={"selected_skill_skeletons": selected_skills},
        outputs={"selected_skill_names": [
            skill.skill_name for skill in selected_skills]},
    )


def _generate_stage_content(state, _services):
    profile = state.shared["normalized_user_profile"]
    target_role = state.shared["normalized_target_role"]
    llm = getattr(_services, "llm", None)
    logger = getattr(_services, "logger", None)
    contextualized_skills: list[CurriculumSkill] = []
    for skill in state.shared.get("selected_skill_skeletons", []):
        contextualized_subskills: list[CurriculumSubskill] = []
        for subskill in skill.subskills:
            generated_stages: list[StagePayload] = []
            for stage in subskill.stages:
                contextualized_stage = _contextualize_stage(
                    stage,
                    profile=profile,
                    target_role=target_role,
                    skill_name=skill.skill_name,
                    subskill_name=subskill.subskill_name,
                    subskill=subskill,
                )
                llm_stage = generate_stage_payload_with_llm(
                    contextualized_stage,
                    profile=profile,
                    target_role=target_role,
                    skill_name=skill.skill_name,
                    subskill_name=subskill.subskill_name,
                    llm=llm,
                    logger=getattr(_services, "logger", None),
                )
                if llm_stage is not None:
                    _record_generation_event(
                        logger,
                        "learning.stage_content_stored",
                        {
                            "stage_id": llm_stage.stage_id,
                            "stage_type": llm_stage.stage_type,
                            "generation_mode": llm_stage.metadata.get("generation_mode", ""),
                            "stored_stage_content": llm_stage.instructions,
                            "authoring_prompt": llm_stage.metadata.get("authoring_prompt", ""),
                        },
                    )
                    generated_stages.append(llm_stage)
                    continue
                fallback_metadata = dict(contextualized_stage.metadata)
                fallback_metadata["generation_mode"] = "deterministic_fallback" if llm is not None else "deterministic"
                fallback_stage = replace(
                    contextualized_stage, metadata=fallback_metadata)
                _record_generation_event(
                    logger,
                    "learning.stage_content_stored",
                    {
                        "stage_id": fallback_stage.stage_id,
                        "stage_type": fallback_stage.stage_type,
                        "generation_mode": fallback_stage.metadata.get("generation_mode", ""),
                        "stored_stage_content": fallback_stage.instructions,
                        "authoring_prompt": fallback_stage.metadata.get("authoring_prompt", ""),
                        "llm_available": bool(llm is not None and hasattr(llm, "generate")),
                    },
                )
                generated_stages.append(fallback_stage)
            contextualized_subskills.append(
                replace(subskill, stages=generated_stages))
        contextualized_skills.append(
            replace(skill, subskills=contextualized_subskills))
    return NodeResult(
        updates={"contextualized_curriculum_skills": contextualized_skills},
        outputs={"generated_skill_count": len(contextualized_skills)},
    )


def _assemble_curriculum(state, _services):
    profile = state.shared["normalized_user_profile"]
    target_role = state.shared["normalized_target_role"]
    missing_skills = state.shared.get("normalized_missing_skills", [])
    skills = state.shared.get("contextualized_curriculum_skills", [])
    curriculum_id = str(
        state.shared.get("curriculum_id")
        or f"curriculum-{target_role.role_id}-{profile.current_role.strip().lower().replace(' ', '-')}"
    )
    curriculum = GeneratedCurriculum(
        curriculum_id=curriculum_id,
        user_profile=profile,
        target_role=target_role,
        missing_skills=list(missing_skills),
        skills=list(skills),
        status="generated",
    )
    return NodeResult(
        updates={"generated_curriculum": curriculum},
        outputs={"generated_curriculum": curriculum},
    )


def _validate_curriculum(state, _services):
    curriculum = validate_generated_curriculum(
        state.shared["generated_curriculum"])
    return NodeResult(
        updates={"validated_curriculum": curriculum},
        outputs={
            "generated_curriculum": curriculum,
            "curriculum_skill_names": [skill.skill_name for skill in curriculum.skills],
        },
    )


def _persist_curriculum(state, services):
    curriculum = state.shared["validated_curriculum"]
    repository = dict(getattr(services, "extras", {}) or {}).get("repository")
    outputs = {"generated_curriculum": curriculum,
               "persisted_curriculum_path": None}
    updates: dict[str, Any] = {}
    if repository is not None:
        destination = repository.save_curriculum(curriculum)
        updates["persisted_curriculum_path"] = str(destination)
        outputs["persisted_curriculum_path"] = str(destination)
        if getattr(services, "logger", None) is not None:
            services.logger.record(
                "learning.persistence",
                {
                    "entity": "curriculum",
                    "path": str(destination),
                    "curriculum_id": curriculum.curriculum_id,
                    "skill_count": len(curriculum.skills),
                },
                level="debug",
            )
    return NodeResult(
        updates=updates,
        outputs=outputs,
        stop=True,
        status="completed",
    )


def build_curriculum_generation_runner() -> WorkflowRunner:
    return WorkflowRunner(
        [
            WorkflowNode(name="normalize_inputs", handler=_normalize_inputs,
                         default_next="select_skill_skeletons"),
            WorkflowNode(name="select_skill_skeletons", handler=_select_skill_skeletons,
                         default_next="generate_stage_content"),
            WorkflowNode(name="generate_stage_content",
                         handler=_generate_stage_content, default_next="assemble_curriculum"),
            WorkflowNode(name="assemble_curriculum", handler=_assemble_curriculum,
                         default_next="validate_curriculum"),
            WorkflowNode(name="validate_curriculum",
                         handler=_validate_curriculum, default_next="persist_curriculum"),
            WorkflowNode(name="persist_curriculum",
                         handler=_persist_curriculum),
        ],
        name="curriculum_generation_workflow",
    )


def run_curriculum_generation_workflow(
    *,
    user_profile: dict[str, Any] | UserProfileInput,
    target_role: dict[str, Any] | TargetRole,
    missing_skills: list[Any],
    curriculum_id: str | None = None,
    services: WorkflowServices | None = None,
) -> Any:
    state = init_state(
        run_id="transitionai-curriculum-generation",
        objective="Generate a complete curriculum once from a user profile, a target role, and a precomputed skill gap.",
        shared={
            "user_profile": UserProfileInput.from_mapping(user_profile),
            "target_role": _target_role_from_input(target_role),
            "missing_skills": _skill_gap_items_from_input(missing_skills),
            "curriculum_id": curriculum_id,
        },
        metadata={"workflow_name": "curriculum_generation_workflow"},
    )
    runtime = services or WorkflowServices()
    return build_curriculum_generation_runner().run(
        state,
        start_at="normalize_inputs",
        services=runtime,
    )


def generate_curriculum(
    *,
    user_profile: dict[str, Any] | UserProfileInput,
    target_role: dict[str, Any] | TargetRole,
    missing_skills: list[Any],
    curriculum_id: str | None = None,
    services: WorkflowServices | None = None,
) -> GeneratedCurriculum:
    final_state = run_curriculum_generation_workflow(
        user_profile=user_profile,
        target_role=target_role,
        missing_skills=missing_skills,
        curriculum_id=curriculum_id,
        services=services,
    )
    if final_state.status != "completed":
        raise RuntimeError(
            "Curriculum generation workflow did not complete successfully.")
    return final_state.outputs["generated_curriculum"]
