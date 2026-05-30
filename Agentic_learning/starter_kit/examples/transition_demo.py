"""TransitionAI Zurich workflow demo built on the reusable starter kit."""

from __future__ import annotations

import os
from typing import Any

from starter_kit import (
    DebugLogger,
    NodeResult,
    ObservabilityConfig,
    WorkflowNode,
    WorkflowRunner,
    WorkflowServices,
    attach_cli_observer,
    init_state,
)

MARKET_ROLES = [
    {
        "role_id": "zurich-ai-ops-analyst",
        "title": "AI Operations Analyst",
        "industry": "Enterprise Services",
        "growth_score": 0.91,
        "resilience_score": 0.86,
        "skills": [
            "process improvement",
            "stakeholder management",
            "data analysis",
            "workflow automation",
            "dashboard reporting",
        ],
        "courses": [
            "Workflow Automation Foundations",
            "SQL for Operations Analytics",
            "Applied Process Mining",
        ],
    },
    {
        "role_id": "zurich-customer-success-lead",
        "title": "Customer Success Lead",
        "industry": "SaaS",
        "growth_score": 0.83,
        "resilience_score": 0.72,
        "skills": [
            "stakeholder management",
            "client communication",
            "account strategy",
            "data analysis",
            "crm systems",
        ],
        "courses": [
            "Advanced Customer Discovery",
            "CRM Analytics for Growth Teams",
            "Strategic Account Planning",
        ],
    },
    {
        "role_id": "zurich-green-project-coordinator",
        "title": "Green Transition Project Coordinator",
        "industry": "Sustainability",
        "growth_score": 0.88,
        "resilience_score": 0.81,
        "skills": [
            "project coordination",
            "cross-functional collaboration",
            "stakeholder management",
            "reporting",
            "vendor coordination",
        ],
        "courses": [
            "Sustainability Reporting Basics",
            "Project Coordination Bootcamp",
            "Supplier Management for Transformation Programs",
        ],
    },
]

TRANSFER_RULES = {
    "operations": ["process improvement", "workflow automation", "reporting"],
    "people leadership": ["stakeholder management", "cross-functional collaboration"],
    "client service": ["client communication", "stakeholder management"],
    "analysis": ["data analysis", "dashboard reporting"],
}

DEMO_USER_PROFILE = {
    "name": "Alex Meyer",
    "current_role": "Senior Operations Manager",
    "years_experience": 14,
    "location": "Zurich",
    "target_preferences": ["sustainability", "enterprise services", "healthtech"],
    "explicit_skills": [
        "stakeholder management",
        "process improvement",
        "project coordination",
        "reporting",
        "client communication",
    ],
    "experience_signals": ["operations", "people leadership", "analysis"],
}


def _unique_skills(skills: list[str]) -> list[str]:
    return sorted({skill.strip().lower() for skill in skills if skill and skill.strip()})


def infer_profile_skills(profile: dict[str, Any]) -> dict[str, Any]:
    explicit_skills = _unique_skills(list(profile.get("explicit_skills", [])))
    inferred_skills: list[str] = []
    for signal in profile.get("experience_signals", []):
        inferred_skills.extend(TRANSFER_RULES.get(
            str(signal).strip().lower(), []))
    transferable_skills = _unique_skills(explicit_skills + inferred_skills)
    return {
        "explicit_skills": explicit_skills,
        "transferable_skills": transferable_skills,
        "experience_signals": list(profile.get("experience_signals", [])),
    }


def score_transition(profile_skills: list[str], role: dict[str, Any]) -> dict[str, Any]:
    role_skills = _unique_skills(
        list(role.get("normalized_skills", role.get("skills", []))))
    matched_skills = sorted(set(profile_skills) & set(role_skills))
    missing_skills = sorted(set(role_skills) - set(profile_skills))
    coverage = len(matched_skills) / len(role_skills) if role_skills else 0.0
    market_score = (float(role.get("growth_score", 0.0)) +
                    float(role.get("resilience_score", 0.0))) / 2
    compatibility = round((coverage * 0.7) + (market_score * 0.3), 3)
    return {
        "role_id": role["role_id"],
        "title": role["title"],
        "industry": role["industry"],
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "coverage": round(coverage, 3),
        "market_score": round(market_score, 3),
        "compatibility": compatibility,
        "courses": list(role.get("courses", [])),
    }


def build_learning_roadmap(recommendation: dict[str, Any]) -> list[dict[str, Any]]:
    roadmap: list[dict[str, Any]] = []
    missing_skills = list(recommendation.get("missing_skills", []))
    courses = list(recommendation.get("courses", []))
    for index, skill in enumerate(missing_skills, start=1):
        suggested_course = courses[min(
            index - 1, len(courses) - 1)] if courses else "Targeted skills practice"
        roadmap.append(
            {
                "priority": index,
                "skill": skill,
                "recommended_course": suggested_course,
                "goal": f"Reach interview-ready confidence in {skill}.",
            }
        )
    if not roadmap:
        roadmap.append(
            {
                "priority": 1,
                "skill": "portfolio validation",
                "recommended_course": courses[0] if courses else "Applied portfolio sprint",
                "goal": "Convert existing experience into role-specific evidence.",
            }
        )
    return roadmap


def _ingest_market_data(_state, _services):
    return NodeResult(
        updates={
            "market_source": "Zurich jobs API demo fixture",
            "raw_market_roles": MARKET_ROLES,
        },
        outputs={"market_role_count": len(MARKET_ROLES)},
    )


def _normalize_market_data(state, _services):
    normalized_roles = []
    for role in state.shared.get("raw_market_roles", []):
        normalized_roles.append(
            {
                **role,
                "normalized_skills": _unique_skills(list(role.get("skills", []))),
            }
        )
    skill_index = {
        role["role_id"]: list(role["normalized_skills"])
        for role in normalized_roles
    }
    return NodeResult(
        updates={
            "normalized_market_roles": normalized_roles,
            "role_skill_index": skill_index,
        }
    )


def _prepare_user_profile(state, _services):
    profile = dict(state.shared.get("user_profile", DEMO_USER_PROFILE))
    analyzed_profile = infer_profile_skills(profile)
    return NodeResult(
        updates={
            "user_profile": profile,
            "analyzed_profile": analyzed_profile,
        },
        outputs={
            "user_transferable_skills": analyzed_profile["transferable_skills"]},
    )


def _recommend_transitions(state, _services):
    profile_skills = list(
        state.shared["analyzed_profile"]["transferable_skills"])
    scored_roles = [
        score_transition(profile_skills, role)
        for role in state.shared.get("normalized_market_roles", [])
    ]
    recommendations = sorted(
        scored_roles,
        key=lambda item: (item["compatibility"],
                          item["coverage"], -len(item["missing_skills"])),
        reverse=True,
    )
    top_matches = recommendations[:3]
    return NodeResult(
        updates={
            "transition_recommendations": top_matches,
            "selected_role": top_matches[0] if top_matches else None,
        },
        outputs={"top_transition_matches": top_matches},
    )


def _build_learning_plan(state, _services):
    selected_role = state.shared.get("selected_role")
    if not selected_role:
        return NodeResult(outputs={"learning_roadmap": []})
    roadmap = build_learning_roadmap(selected_role)
    return NodeResult(
        updates={"learning_roadmap": roadmap},
        outputs={"learning_roadmap": roadmap},
    )


def _finalize_report(state, _services):
    profile = dict(state.shared.get("user_profile", {}))
    selected_role = dict(state.shared.get("selected_role") or {})
    roadmap = list(state.shared.get("learning_roadmap", []))
    report = {
        "candidate": profile.get("name", "Unknown candidate"),
        "current_role": profile.get("current_role", "Unknown role"),
        "top_match": selected_role,
        "roadmap": roadmap,
        "recommendations": list(state.shared.get("transition_recommendations", [])),
    }
    return NodeResult(outputs={"final_report": report}, stop=True, status="completed")


def run_demo(user_profile: dict[str, Any] | None = None, *, log_mode: str | None = None):
    logger = DebugLogger()
    attach_cli_observer(
        logger,
        ObservabilityConfig(
            mode=log_mode or os.environ.get(
                "STARTER_KIT_LOG_MODE", "standard"),
            max_chars=900,
            show_prompt_sections=False,
            show_state_diffs=True,
        ),
    )

    state = init_state(
        run_id="transitionai-zurich-demo",
        objective="Model an end-to-end workforce transition flow from market intelligence to a personalized learning roadmap.",
        shared={"user_profile": dict(user_profile or DEMO_USER_PROFILE)},
        metadata={"workflow_name": "transitionai_workflow"},
    )
    runner = WorkflowRunner(
        [
            WorkflowNode(name="ingest_market_data", handler=_ingest_market_data,
                         default_next="normalize_market_data"),
            WorkflowNode(name="normalize_market_data",
                         handler=_normalize_market_data, default_next="prepare_user_profile"),
            WorkflowNode(name="prepare_user_profile", handler=_prepare_user_profile,
                         default_next="recommend_transitions"),
            WorkflowNode(name="recommend_transitions",
                         handler=_recommend_transitions, default_next="build_learning_plan"),
            WorkflowNode(name="build_learning_plan",
                         handler=_build_learning_plan, default_next="finalize_report"),
            WorkflowNode(name="finalize_report", handler=_finalize_report),
        ],
        name="transitionai_workflow",
    )
    return runner.run(state, start_at="ingest_market_data", services=WorkflowServices(logger=logger))


def _print_report(final_state) -> None:
    report = final_state.outputs.get("final_report", {})
    top_match = dict(report.get("top_match") or {})
    roadmap = list(report.get("roadmap", []))
    print("TransitionAI Zurich Demo")
    print(f"Candidate: {report.get('candidate', 'Unknown')}")
    print(f"Current role: {report.get('current_role', 'Unknown')}")
    print(
        f"Recommended transition: {top_match.get('title', 'No match')} ({top_match.get('industry', 'n/a')})")
    print(f"Compatibility score: {top_match.get('compatibility', 0.0)}")
    print("Matched skills: " + ", ".join(top_match.get("matched_skills", [])))
    print("Missing skills: " + ", ".join(top_match.get("missing_skills", [])))
    print("Learning roadmap:")
    for step in roadmap:
        print(
            f"  {step['priority']}. {step['skill']} -> {step['recommended_course']}")


def main() -> None:
    final_state = run_demo()
    _print_report(final_state)


if __name__ == "__main__":
    main()
