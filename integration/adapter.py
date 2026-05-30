"""Adapter: System A output  ->  System B input.

This is the one place that knows how to reshape a :class:`MatchmakingOutput`
into a :class:`LearningRequest`. It depends only on the boundary contracts in
:mod:`integration.contracts` -- never on either subsystem's internals -- so the
two systems stay decoupled and either side can evolve as long as its contract
holds.

What the adapter reconciles:

* **Skill gaps.** System A reports ``missing_skills`` *per matched job*. System B
  wants a single, deduplicated, prioritised list. We aggregate across the top
  matches, rank a gap by how many target jobs demand it (and, as a tiebreaker,
  by the best match score that demands it), and emit one ``SkillGapInput`` per
  distinct skill.

* **Learner profile.** System B wants a learner profile. System A's match
  response does not always carry one, so we use the optional
  ``candidate_profile`` when present and otherwise derive a minimal profile
  (the learner's ``explicit_skills`` are inferred from the union of
  ``matched_skills`` across jobs).

* **Target role / learning objective.** A pure skill gap has no destination.
  The caller supplies a :class:`LearningObjective` (target role + optional
  learner overrides). When no explicit target role is given, we fall back to
  the top-scoring matched job as a reasonable default.

No value-level assumptions are hardcoded: skill names are passed through as-is
(only trimmed/deduplicated); System B decides which it can actually teach.
"""

from __future__ import annotations

from typing import Iterable

from pydantic import BaseModel, ConfigDict, Field

from .contracts import (
    GapResponse,
    LearnerProfileInput,
    LearningRequest,
    MatchmakingOutput,
    SkillGapInput,
    TargetRoleInput,
)


class LearningObjective(BaseModel):
    """Caller-supplied objective that complements System A's skill gaps.

    System B's documented inputs are "structured skill gaps" *and* "learning
    objectives". System A produces the former; this object carries the latter.
    """

    model_config = ConfigDict(extra="ignore")

    target_role: TargetRoleInput | None = None
    learner: LearnerProfileInput | None = None
    # Cap the number of skill gaps forwarded to System B (highest priority
    # first). ``None`` forwards them all.
    max_skills: int | None = None
    curriculum_id: str | None = None
    # Free-form preferences merged into the learner profile's ``preferences``.
    preferences: dict = Field(default_factory=dict)


def _slugify(text: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in text.strip())
    parts = [segment for segment in cleaned.split("-") if segment]
    return "-".join(parts) or "role"


def _dedupe_preserve_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        cleaned = str(value).strip()
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(cleaned)
    return result


def aggregate_skill_gaps(
    output: MatchmakingOutput,
    *,
    max_skills: int | None = None,
) -> list[SkillGapInput]:
    """Collapse per-job ``missing_skills`` into one prioritised gap list.

    Priority is assigned by demand: a skill missing for more (higher-scoring)
    target jobs is more important. The returned list is ordered by priority and
    each item's ``priority`` field is its 1-based rank.
    """
    # skill_key -> (display_name, demand_count, best_score)
    stats: dict[str, tuple[str, int, float]] = {}
    for match in output.matches:
        for raw_skill in match.missing_skills:
            display = str(raw_skill).strip()
            if not display:
                continue
            key = display.lower()
            if key in stats:
                name, count, best = stats[key]
                stats[key] = (name, count + 1, max(best, match.score))
            else:
                stats[key] = (display, 1, match.score)

    # Sort by demand count desc, then best score desc, then name for stability.
    ranked = sorted(
        stats.values(),
        key=lambda item: (-item[1], -item[2], item[0].lower()),
    )
    if max_skills is not None:
        ranked = ranked[: max(0, max_skills)]

    return [
        SkillGapInput(
            skill_name=name,
            gap_type="missing",
            priority=rank,
            source="matching",
        )
        for rank, (name, _count, _best) in enumerate(ranked, start=1)
    ]


def _top_match(output: MatchmakingOutput):
    if not output.matches:
        return None
    return max(output.matches, key=lambda match: match.score)


def resolve_target_role(
    output: MatchmakingOutput,
    objective: LearningObjective,
) -> TargetRoleInput:
    """Pick the target role: explicit objective first, top match as fallback."""
    if objective.target_role is not None:
        return objective.target_role
    top = _top_match(output)
    if top is None:
        # Nothing to anchor on; produce a clearly-labelled placeholder so the
        # downstream contract still validates and the issue is visible.
        return TargetRoleInput(role_id="unknown-role", title="Unknown target role")
    job = top.job
    return TargetRoleInput(
        role_id=_slugify(job.title) or str(job.id),
        title=job.title,
        industry=job.category or "Unknown industry",
    )


def build_learner_profile(
    output: MatchmakingOutput,
    objective: LearningObjective,
) -> LearnerProfileInput:
    """Build System B's learner profile from whatever System A surfaced.

    Precedence: an explicit ``objective.learner`` wins; otherwise the optional
    ``candidate_profile`` is used; otherwise a minimal profile is derived from
    the matches. ``objective.preferences`` are always merged in.
    """
    if objective.learner is not None:
        profile = objective.learner.model_copy(deep=True)
    elif output.candidate_profile is not None:
        cp = output.candidate_profile
        profile = LearnerProfileInput(
            name=cp.name or "",
            current_role=cp.current_role or "",
            years_experience=cp.years_experience or 0,
            location=cp.location or "",
            industry_background=cp.industry_background or "",
            explicit_skills=_dedupe_preserve_order(cp.skills),
            user_id=output.user_id,
        )
    else:
        # No profile surfaced: infer the skills the learner already has from the
        # union of matched skills across all jobs.
        inferred_skills = _dedupe_preserve_order(
            skill for match in output.matches for skill in match.matched_skills
        )
        profile = LearnerProfileInput(
            explicit_skills=inferred_skills,
            user_id=output.user_id,
        )

    # Always anchor the user_id to System A's identity and merge preferences.
    updates: dict = {}
    if not profile.user_id:
        updates["user_id"] = output.user_id
    if objective.preferences:
        merged = {**profile.preferences, **objective.preferences}
        updates["preferences"] = merged
    if updates:
        profile = profile.model_copy(update=updates)
    return profile


def build_learning_request(
    output: MatchmakingOutput,
    objective: LearningObjective | None = None,
) -> LearningRequest:
    """Transform a validated System A output into a System B :class:`LearningRequest`.

    This is the adapter's public entry point and the only function the
    orchestrator calls.
    """
    objective = objective or LearningObjective()
    target_role = resolve_target_role(output, objective)
    learner = build_learner_profile(output, objective)
    gaps = aggregate_skill_gaps(output, max_skills=objective.max_skills)
    return LearningRequest(
        user_profile=learner,
        target_role=target_role,
        missing_skills=gaps,
        curriculum_id=objective.curriculum_id,
    )


def build_learning_request_from_gap(
    gaps: GapResponse | list[GapResponse],
    objective: LearningObjective | None = None,
) -> LearningRequest:
    """Map System A's documented ``/gap`` contract into a System B request.

    ``GapResponse`` is the pure data contract the backend explicitly exposes for
    the learning system. It is per-job and carries no job title, so the target
    role must come from the caller's :class:`LearningObjective`. Accepts a single
    gap or several (e.g. the user's top jobs), aggregating missing skills across
    them while ranking by how many jobs demand each skill.
    """
    objective = objective or LearningObjective()
    gap_list = [gaps] if isinstance(gaps, GapResponse) else list(gaps)

    # Rank gaps by demand across the supplied jobs; ties keep first-seen order
    # (no per-job scores exist on this contract to break ties by).
    demand: dict[str, tuple[str, int, int]] = {}
    order = 0
    for gap in gap_list:
        for raw_skill in gap.missing_skills:
            display = str(raw_skill).strip()
            if not display:
                continue
            key = display.lower()
            if key in demand:
                name, count, first_index = demand[key]
                demand[key] = (name, count + 1, first_index)
            else:
                demand[key] = (display, 1, order)
                order += 1
    ranked = [
        (name, count)
        for name, count, _first in sorted(
            demand.values(), key=lambda item: (-item[1], item[2])
        )
    ]
    if objective.max_skills is not None:
        ranked = ranked[: max(0, objective.max_skills)]
    skill_gaps = [
        SkillGapInput(skill_name=name, gap_type="missing", priority=rank, source="gap_endpoint")
        for rank, (name, _count) in enumerate(ranked, start=1)
    ]

    # Learner profile: explicit objective wins; otherwise derive the skills the
    # learner already has from the union of ``user_skills`` across gaps.
    user_id = gap_list[0].user_id if gap_list else None
    if objective.learner is not None:
        learner = objective.learner.model_copy(deep=True)
        if not learner.user_id and user_id:
            learner = learner.model_copy(update={"user_id": user_id})
    else:
        known = _dedupe_preserve_order(
            skill for gap in gap_list for skill in (gap.user_skills or gap.matched_skills)
        )
        learner = LearnerProfileInput(explicit_skills=known, user_id=user_id)
    if objective.preferences:
        learner = learner.model_copy(
            update={"preferences": {**learner.preferences, **objective.preferences}}
        )

    target_role = objective.target_role or TargetRoleInput(
        role_id="unknown-role", title="Unknown target role"
    )
    return LearningRequest(
        user_profile=learner,
        target_role=target_role,
        missing_skills=skill_gaps,
        curriculum_id=objective.curriculum_id,
    )
