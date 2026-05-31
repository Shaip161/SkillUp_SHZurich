"""Reusable backend learning engine built on a minimal workflow core."""

from .contracts import (
    CurriculumSkill,
    CurriculumSubskill,
    ErrorRecord,
    EvaluationResult,
    GeneratedCurriculum,
    ProgressState,
    SkillGapItem,
    SkillTemplate,
    StagePayload,
    SubskillTemplate,
    TargetRole,
    UserProfileInput,
)
from .knowledge_base import (
    ERROR_CATEGORIES,
    STAGE_SEQUENCE,
    build_curriculum_skill_skeleton,
    get_skill_definition,
    list_supported_skill_names,
    select_catalog_skills,
)
from .offline_generation import (
    generate_curriculum,
    run_curriculum_generation_workflow,
    validate_generated_curriculum,
)
from .persistence import JsonLearningRepository, LearningStateBundle
from .runtime import RuntimeSkillProgress, RuntimeSnapshot, run_learning_runtime
from .integrations import (
    aggregate_final_with_llm,
    evaluate_conceptual_with_llm,
    evaluate_practical_with_llm,
    generate_remediation_with_llm,
    generate_stage_payload_with_llm,
)

__all__ = [
    "CurriculumSkill",
    "CurriculumSubskill",
    "ErrorRecord",
    "ERROR_CATEGORIES",
    "EvaluationResult",
    "GeneratedCurriculum",
    "JsonLearningRepository",
    "LearningStateBundle",
    "ProgressState",
    "RuntimeSkillProgress",
    "RuntimeSnapshot",
    "SkillGapItem",
    "SkillTemplate",
    "STAGE_SEQUENCE",
    "StagePayload",
    "SubskillTemplate",
    "TargetRole",
    "UserProfileInput",
    "build_curriculum_skill_skeleton",
    "aggregate_final_with_llm",
    "evaluate_conceptual_with_llm",
    "evaluate_practical_with_llm",
    "generate_curriculum",
    "generate_remediation_with_llm",
    "generate_stage_payload_with_llm",
    "get_skill_definition",
    "list_supported_skill_names",
    "run_learning_runtime",
    "run_curriculum_generation_workflow",
    "select_catalog_skills",
    "validate_generated_curriculum",
]
