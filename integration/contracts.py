"""Explicit, typed contracts for the A -> B integration boundary.

These Pydantic models are the *only* shared vocabulary between System A
(Job Matchmaking Engine) and System B (Learning Agent System). Neither
subsystem imports this module; the integration layer owns it. That keeps the
two systems decoupled and lets us validate the data crossing the boundary
without reaching into either implementation.

Two contracts are defined:

* ``MatchmakingOutput`` -- the schema System A is expected to emit. It mirrors
  the backend's ``/match`` response (``user_id`` + ``matches``) and adds an
  *optional* ``candidate_profile`` enrichment channel that System A may expose
  but is not required to. Validation enforces required fields and types while
  tolerating unknown extra keys for forward-compatibility.

* ``LearningRequest`` -- the schema System B is expected to consume. It mirrors
  the arguments of ``generate_curriculum`` (user profile, target role, skill
  gaps). The adapter produces instances of this contract; the learning engine
  provider unpacks them into System B's native kwargs.

Nothing here hardcodes assumptions about field *values*; it only pins the
*shape* of the data. Use :func:`validate_matchmaking_output` and
:func:`validate_learning_request` to turn arbitrary mappings into validated
contracts, raising :class:`ContractError` on malformed input.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator


class ContractError(ValueError):
    """Raised when a payload fails to satisfy a boundary contract.

    Wraps Pydantic's ``ValidationError`` with a stable, integration-layer
    exception type so callers (the orchestrator, tests) can catch schema
    mismatches without depending on Pydantic internals.
    """

    def __init__(self, contract: str, error: ValidationError) -> None:
        self.contract = contract
        self.validation_error = error
        super().__init__(f"{contract} contract validation failed:\n{error}")


# ---------------------------------------------------------------------------
# System A output contract
# ---------------------------------------------------------------------------


class MatchedJob(BaseModel):
    """A single job as emitted inside a System A match result.

    Mirrors the backend ``JobListItem`` shape. Only ``id``, ``title`` and
    ``redirect_url`` are required; everything else is optional metadata.
    """

    model_config = ConfigDict(extra="ignore")

    id: str
    title: str
    company: str | None = None
    location: str | None = None
    category: str | None = None
    seniority: str | None = None
    required_skills: list[str] = Field(default_factory=list)
    redirect_url: str

    @field_validator("id", mode="before")
    @classmethod
    def _coerce_id(cls, value: Any) -> str:
        # Backend ids are UUIDs; accept UUID objects/ints transparently.
        return str(value)


class JobMatch(BaseModel):
    """One matched job plus the per-job skill breakdown from System A."""

    model_config = ConfigDict(extra="ignore")

    job: MatchedJob
    score: float
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)

    @field_validator("score")
    @classmethod
    def _score_is_finite(cls, value: float) -> float:
        # A cosine similarity should be a real, non-negative number. We do not
        # clamp to [0, 1] (the matcher can emit small overshoots); we only
        # reject clearly malformed values.
        if value != value or value in (float("inf"), float("-inf")):  # NaN/inf
            raise ValueError("score must be a finite number")
        if value < 0:
            raise ValueError("score must be non-negative")
        return value


class CandidateProfile(BaseModel):
    """Optional enrichment: the parsed candidate behind the matches.

    System A's current ``/match`` endpoint persists this to its database
    rather than returning it, so this block is entirely optional. When a
    matchmaking provider *does* surface it, the adapter uses it to build a
    far richer learner profile for System B. When absent, the adapter
    degrades gracefully (deriving skills from ``matched_skills``).
    """

    model_config = ConfigDict(extra="ignore")

    name: str | None = None
    current_role: str | None = None
    seniority: str | None = None
    years_experience: int | None = None
    location: str | None = None
    industry_background: str | None = None
    skills: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)


class MatchmakingOutput(BaseModel):
    """The contract for everything System A hands to the integration layer."""

    model_config = ConfigDict(extra="ignore")

    user_id: str
    matches: list[JobMatch]
    candidate_profile: CandidateProfile | None = None

    @field_validator("user_id", mode="before")
    @classmethod
    def _coerce_user_id(cls, value: Any) -> str:
        return str(value)


class GapResponse(BaseModel):
    """System A's ``POST /gap/{job_id}`` response -- the *designated* A->B contract.

    Per the backend docs, this is the pure, no-LLM data contract that the
    learning system is meant to consume directly: a single job's required
    skills minus the user's skills. It is a leaner alternative to the full
    ``MatchmakingOutput`` (which carries many jobs); the adapter can map either.
    """

    model_config = ConfigDict(extra="ignore")

    job_id: str
    user_id: str
    required_skills: list[str] = Field(default_factory=list)
    user_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    matched_skills: list[str] = Field(default_factory=list)

    @field_validator("job_id", "user_id", mode="before")
    @classmethod
    def _coerce_str(cls, value: Any) -> str:
        return str(value)


# ---------------------------------------------------------------------------
# System B input contract
# ---------------------------------------------------------------------------


class TargetRoleInput(BaseModel):
    """The role the learner is transitioning toward (a learning objective)."""

    model_config = ConfigDict(extra="ignore")

    role_id: str
    title: str
    industry: str = "Unknown industry"


class SkillGapInput(BaseModel):
    """A single structured skill gap headed into System B."""

    model_config = ConfigDict(extra="ignore")

    skill_name: str
    gap_type: str = "missing"
    priority: int = 1
    source: str = "matching"

    @field_validator("skill_name")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("skill_name must be a non-empty string")
        return cleaned


class LearnerProfileInput(BaseModel):
    """Learner profile for System B.

    A faithful, validated subset of System B's ``UserProfileInput`` dataclass.
    System B accepts a plain mapping, so the engine provider simply dumps this
    model to a dict -- no tight coupling to System B's dataclass.
    """

    model_config = ConfigDict(extra="ignore")

    name: str = ""
    current_role: str = ""
    years_experience: int = 0
    location: str = ""
    industry_background: str = ""
    target_preferences: list[str] = Field(default_factory=list)
    explicit_skills: list[str] = Field(default_factory=list)
    experience_signals: list[str] = Field(default_factory=list)
    previous_roles: list[str] = Field(default_factory=list)
    previous_tasks: list[str] = Field(default_factory=list)
    previous_workflows: list[str] = Field(default_factory=list)
    analogous_experiences: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    known_tools: list[str] = Field(default_factory=list)
    user_id: str | None = None
    preferences: dict[str, Any] = Field(default_factory=dict)


class LearningRequest(BaseModel):
    """The contract for everything the integration layer hands to System B.

    Construction validates the full payload. ``missing_skills`` may be empty at
    the schema level (the orchestrator logs a warning and System B will reject
    an empty curriculum downstream), but each entry that *is* present must be a
    well-formed :class:`SkillGapInput`.
    """

    model_config = ConfigDict(extra="ignore")

    user_profile: LearnerProfileInput
    target_role: TargetRoleInput
    missing_skills: list[SkillGapInput] = Field(default_factory=list)
    curriculum_id: str | None = None


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def validate_matchmaking_output(payload: Any) -> MatchmakingOutput:
    """Validate a raw System A payload into a :class:`MatchmakingOutput`.

    Accepts an already-built model (returned as-is) or any mapping. Raises
    :class:`ContractError` on malformed input.
    """
    if isinstance(payload, MatchmakingOutput):
        return payload
    try:
        return MatchmakingOutput.model_validate(payload)
    except ValidationError as error:
        raise ContractError("MatchmakingOutput", error) from error


def validate_learning_request(payload: Any) -> LearningRequest:
    """Validate a raw payload into a :class:`LearningRequest`.

    Raises :class:`ContractError` on malformed input.
    """
    if isinstance(payload, LearningRequest):
        return payload
    try:
        return LearningRequest.model_validate(payload)
    except ValidationError as error:
        raise ContractError("LearningRequest", error) from error


def validate_gap_response(payload: Any) -> GapResponse:
    """Validate a raw System A ``/gap`` payload into a :class:`GapResponse`.

    Raises :class:`ContractError` on malformed input.
    """
    if isinstance(payload, GapResponse):
        return payload
    try:
        return GapResponse.model_validate(payload)
    except ValidationError as error:
        raise ContractError("GapResponse", error) from error
