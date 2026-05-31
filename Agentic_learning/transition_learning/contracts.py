"""Domain contracts for the backend learning engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


StageType = Literal["introduction", "conceptual",
                    "practical", "evaluation", "reflection"]


class ContractMixin:
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _list_of_strings(value: Any) -> list[str]:
    if value is None:
        return []
    return [str(item).strip() for item in list(value) if str(item).strip()]


@dataclass(frozen=True)
class UserProfileInput(ContractMixin):
    name: str = ""
    current_role: str = ""
    years_experience: int = 0
    location: str = ""
    industry_background: str = ""
    target_preferences: list[str] = field(default_factory=list)
    explicit_skills: list[str] = field(default_factory=list)
    experience_signals: list[str] = field(default_factory=list)
    previous_roles: list[str] = field(default_factory=list)
    previous_tasks: list[str] = field(default_factory=list)
    previous_workflows: list[str] = field(default_factory=list)
    analogous_experiences: list[str] = field(default_factory=list)
    certifications: list[str] = field(default_factory=list)
    known_tools: list[str] = field(default_factory=list)
    user_id: str | None = None
    preferences: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, payload: dict[str, Any] | "UserProfileInput") -> "UserProfileInput":
        if isinstance(payload, cls):
            return payload
        data = dict(payload or {})
        return cls(
            name=str(data.get("name", "")),
            current_role=str(data.get("current_role", "")),
            years_experience=int(data.get("years_experience", 0) or 0),
            location=str(data.get("location", "")),
            industry_background=str(
                data.get("industry_background")
                or (data.get("preferences", {}) or {}).get("industry_background", "")
            ),
            target_preferences=_list_of_strings(
                data.get("target_preferences", [])),
            explicit_skills=_list_of_strings(data.get("explicit_skills", [])),
            experience_signals=_list_of_strings(
                data.get("experience_signals", [])),
            previous_roles=_list_of_strings(
                data.get("previous_roles")
                or (data.get("preferences", {}) or {}).get("previous_roles", [])
            ),
            previous_tasks=_list_of_strings(
                data.get("previous_tasks")
                or (data.get("preferences", {}) or {}).get("previous_tasks", [])
            ),
            previous_workflows=_list_of_strings(
                data.get("previous_workflows")
                or (data.get("preferences", {}) or {}).get("previous_workflows", [])
            ),
            analogous_experiences=_list_of_strings(
                data.get("analogous_experiences")
                or (data.get("preferences", {}) or {}).get("analogous_experiences", [])
            ),
            certifications=_list_of_strings(
                data.get("certifications")
                or (data.get("preferences", {}) or {}).get("certifications", [])
            ),
            known_tools=_list_of_strings(
                data.get("known_tools")
                or (data.get("preferences", {}) or {}).get("known_tools", [])
            ),
            user_id=str(data["user_id"]) if data.get("user_id") else None,
            preferences=dict(data.get("preferences", {}) or {}),
        )


@dataclass(frozen=True)
class TargetRole(ContractMixin):
    role_id: str
    title: str
    industry: str

    @classmethod
    def from_mapping(cls, payload: dict[str, Any] | "TargetRole") -> "TargetRole":
        if isinstance(payload, cls):
            return payload
        data = dict(payload or {})
        return cls(
            role_id=str(data.get("role_id", "")),
            title=str(data.get("title", "")),
            industry=str(data.get("industry", "")),
        )


@dataclass(frozen=True)
class SkillGapItem(ContractMixin):
    skill_name: str
    gap_type: str = "missing"
    priority: int = 1
    source: str = "matching"

    @classmethod
    def from_mapping(cls, payload: dict[str, Any] | "SkillGapItem") -> "SkillGapItem":
        if isinstance(payload, cls):
            return payload
        data = dict(payload or {})
        return cls(
            skill_name=str(data.get("skill_name", "")).strip(),
            gap_type=str(data.get("gap_type", "missing")),
            priority=int(data.get("priority", 1) or 1),
            source=str(data.get("source", "matching")),
        )


@dataclass(frozen=True)
class SkillTemplate(ContractMixin):
    skill_id: str
    skill_name: str
    description: str
    subskills: list[str] = field(default_factory=list)
    target_jobs: list[str] = field(default_factory=list)
    difficulty_level: str = "intermediate"
    prerequisites: list[str] = field(default_factory=list)
    related_certifications: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SubskillTemplate(ContractMixin):
    subskill_id: str
    subskill_name: str
    objective: str
    prerequisites: list[str] = field(default_factory=list)
    expected_outcomes: list[str] = field(default_factory=list)
    conceptual_criteria: list[str] = field(default_factory=list)
    practical_criteria: list[str] = field(default_factory=list)
    example_workflows: list[str] = field(default_factory=list)
    common_mistakes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class StagePayload(ContractMixin):
    stage_id: str
    stage_type: StageType
    title: str
    instructions: str
    rubric: list[str] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    expected_output: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, payload: dict[str, Any] | "StagePayload") -> "StagePayload":
        if isinstance(payload, cls):
            return payload
        data = dict(payload or {})
        return cls(
            stage_id=str(data.get("stage_id", "")),
            stage_type=str(data.get("stage_type", "introduction")),
            title=str(data.get("title", "")),
            instructions=str(data.get("instructions", "")),
            rubric=_list_of_strings(data.get("rubric", [])),
            context=dict(data.get("context", {}) or {}),
            expected_output=dict(data.get("expected_output", {}) or {}),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class CurriculumSubskill(ContractMixin):
    subskill_id: str
    subskill_name: str
    objective: str
    conceptual_criteria: list[str] = field(default_factory=list)
    practical_criteria: list[str] = field(default_factory=list)
    expected_outcomes: list[str] = field(default_factory=list)
    example_workflows: list[str] = field(default_factory=list)
    common_mistakes: list[str] = field(default_factory=list)
    stages: list[StagePayload] = field(default_factory=list)

    @classmethod
    def from_mapping(
        cls, payload: dict[str, Any] | "CurriculumSubskill"
    ) -> "CurriculumSubskill":
        if isinstance(payload, cls):
            return payload
        data = dict(payload or {})
        return cls(
            subskill_id=str(data.get("subskill_id", "")),
            subskill_name=str(data.get("subskill_name", "")),
            objective=str(data.get("objective", "")),
            conceptual_criteria=_list_of_strings(
                data.get("conceptual_criteria", [])),
            practical_criteria=_list_of_strings(
                data.get("practical_criteria", [])),
            expected_outcomes=_list_of_strings(
                data.get("expected_outcomes", [])),
            example_workflows=_list_of_strings(
                data.get("example_workflows", [])),
            common_mistakes=_list_of_strings(data.get("common_mistakes", [])),
            stages=[StagePayload.from_mapping(item)
                    for item in data.get("stages", [])],
        )


@dataclass(frozen=True)
class CurriculumSkill(ContractMixin):
    skill_id: str
    skill_name: str
    description: str
    subskills: list[CurriculumSubskill] = field(default_factory=list)
    target_jobs: list[str] = field(default_factory=list)
    difficulty_level: str = "intermediate"
    prerequisites: list[str] = field(default_factory=list)
    related_certifications: list[str] = field(default_factory=list)

    @classmethod
    def from_mapping(cls, payload: dict[str, Any] | "CurriculumSkill") -> "CurriculumSkill":
        if isinstance(payload, cls):
            return payload
        data = dict(payload or {})
        return cls(
            skill_id=str(data.get("skill_id", "")),
            skill_name=str(data.get("skill_name", "")),
            description=str(data.get("description", "")),
            subskills=[CurriculumSubskill.from_mapping(
                item) for item in data.get("subskills", [])],
            target_jobs=_list_of_strings(data.get("target_jobs", [])),
            difficulty_level=str(data.get("difficulty_level", "intermediate")),
            prerequisites=_list_of_strings(data.get("prerequisites", [])),
            related_certifications=_list_of_strings(
                data.get("related_certifications", [])),
        )


@dataclass(frozen=True)
class GeneratedCurriculum(ContractMixin):
    curriculum_id: str
    user_profile: UserProfileInput
    target_role: TargetRole
    missing_skills: list[SkillGapItem] = field(default_factory=list)
    skills: list[CurriculumSkill] = field(default_factory=list)
    status: str = "generated"

    @classmethod
    def from_mapping(
        cls, payload: dict[str, Any] | "GeneratedCurriculum"
    ) -> "GeneratedCurriculum":
        if isinstance(payload, cls):
            return payload
        data = dict(payload or {})
        return cls(
            curriculum_id=str(data.get("curriculum_id", "")),
            user_profile=UserProfileInput.from_mapping(
                data.get("user_profile", {})),
            target_role=TargetRole.from_mapping(data.get("target_role", {})),
            missing_skills=[SkillGapItem.from_mapping(
                item) for item in data.get("missing_skills", [])],
            skills=[CurriculumSkill.from_mapping(
                item) for item in data.get("skills", [])],
            status=str(data.get("status", "generated")),
        )


@dataclass(frozen=True)
class EvaluationResult(ContractMixin):
    evaluation_id: str
    user_id: str
    skill_id: str
    subskill_id: str
    stage: str
    score: float
    passed: bool
    errors: list[str] = field(default_factory=list)
    misconceptions: list[str] = field(default_factory=list)
    critical_misconceptions: list[str] = field(default_factory=list)
    feedback: str = ""
    retry_required: bool = False
    criteria_results: dict[str, float] = field(default_factory=dict)
    supporting_evaluation_ids: list[str] = field(default_factory=list)
    parsed_output: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""

    @classmethod
    def from_mapping(
        cls, payload: dict[str, Any] | "EvaluationResult"
    ) -> "EvaluationResult":
        if isinstance(payload, cls):
            return payload
        data = dict(payload or {})
        return cls(
            evaluation_id=str(data.get("evaluation_id", "")),
            user_id=str(data.get("user_id", "")),
            skill_id=str(data.get("skill_id", "")),
            subskill_id=str(data.get("subskill_id", "")),
            stage=str(data.get("stage", "")),
            score=float(data.get("score", 0.0) or 0.0),
            passed=bool(data.get("passed", False)),
            errors=_list_of_strings(data.get("errors", [])),
            misconceptions=_list_of_strings(data.get("misconceptions", [])),
            critical_misconceptions=_list_of_strings(
                data.get("critical_misconceptions", [])
            ),
            feedback=str(data.get("feedback", "")),
            retry_required=bool(data.get("retry_required", False)),
            criteria_results={
                str(key): float(value)
                for key, value in dict(data.get("criteria_results", {}) or {}).items()
            },
            supporting_evaluation_ids=_list_of_strings(
                data.get("supporting_evaluation_ids", [])
            ),
            parsed_output=dict(data.get("parsed_output", {}) or {}),
            created_at=str(data.get("created_at", "")),
        )


@dataclass(frozen=True)
class ProgressState(ContractMixin):
    user_id: str
    skill_id: str
    subskill_id: str
    completed_steps: list[str] = field(default_factory=list)
    current_step: str = ""
    progress_percent: float = 0.0
    mastery_status: str = "not_started"
    current_skill_id: str = ""
    current_subskill_id: str = ""
    current_stage: str = ""
    completed_subskills: list[str] = field(default_factory=list)
    retry_count: int = 0
    remediation_state: dict[str, Any] = field(default_factory=dict)
    latest_scores: dict[str, float] = field(default_factory=dict)
    latest_errors: list[str] = field(default_factory=list)
    unlock_state: dict[str, bool] = field(default_factory=dict)

    @classmethod
    def from_mapping(
        cls, payload: dict[str, Any] | "ProgressState"
    ) -> "ProgressState":
        if isinstance(payload, cls):
            return payload
        data = dict(payload or {})
        return cls(
            user_id=str(data.get("user_id", "")),
            skill_id=str(data.get("skill_id", "")),
            subskill_id=str(data.get("subskill_id", "")),
            completed_steps=_list_of_strings(data.get("completed_steps", [])),
            current_step=str(data.get("current_step", "")),
            progress_percent=float(data.get("progress_percent", 0.0) or 0.0),
            mastery_status=str(data.get("mastery_status", "not_started")),
            current_skill_id=str(
                data.get("current_skill_id", data.get("skill_id", ""))),
            current_subskill_id=str(
                data.get("current_subskill_id", data.get("subskill_id", ""))),
            current_stage=str(
                data.get("current_stage", data.get("current_step", ""))),
            completed_subskills=_list_of_strings(
                data.get("completed_subskills", [])),
            retry_count=int(data.get("retry_count", 0) or 0),
            remediation_state=dict(data.get("remediation_state", {}) or {}),
            latest_scores={
                str(key): float(value)
                for key, value in dict(data.get("latest_scores", {}) or {}).items()
            },
            latest_errors=_list_of_strings(data.get("latest_errors", [])),
            unlock_state={
                str(key): bool(value)
                for key, value in dict(data.get("unlock_state", {}) or {}).items()
            },
        )


@dataclass(frozen=True)
class ErrorRecord(ContractMixin):
    error_id: str
    user_id: str
    skill_id: str
    subskill_id: str
    error_type: str
    description: str
    correct_reasoning: str
    main_errors: list[str] = field(default_factory=list)
    reinforcement_task: str = ""
    retry_focus: list[str] = field(default_factory=list)
    needs_retry: bool = True
    related_evaluation_id: str = ""
    score_snapshot: dict[str, float] = field(default_factory=dict)
    timestamp: str = ""

    @classmethod
    def from_mapping(cls, payload: dict[str, Any] | "ErrorRecord") -> "ErrorRecord":
        if isinstance(payload, cls):
            return payload
        data = dict(payload or {})
        return cls(
            error_id=str(data.get("error_id", "")),
            user_id=str(data.get("user_id", "")),
            skill_id=str(data.get("skill_id", "")),
            subskill_id=str(data.get("subskill_id", "")),
            error_type=str(data.get("error_type", "")),
            description=str(data.get("description", "")),
            correct_reasoning=str(data.get("correct_reasoning", "")),
            main_errors=_list_of_strings(data.get("main_errors", [])),
            reinforcement_task=str(data.get("reinforcement_task", "")),
            retry_focus=_list_of_strings(data.get("retry_focus", [])),
            needs_retry=bool(data.get("needs_retry", True)),
            related_evaluation_id=str(data.get("related_evaluation_id", "")),
            score_snapshot={
                str(key): float(value)
                for key, value in dict(data.get("score_snapshot", {}) or {}).items()
            },
            timestamp=str(data.get("timestamp", "")),
        )
