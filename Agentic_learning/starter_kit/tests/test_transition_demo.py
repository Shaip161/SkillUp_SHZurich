from starter_kit.examples.transition_demo import (
    build_learning_roadmap,
    infer_profile_skills,
    run_demo,
    score_transition,
)


def test_infer_profile_skills_adds_transferable_capabilities():
    analyzed = infer_profile_skills(
        {
            "explicit_skills": ["Stakeholder Management"],
            "experience_signals": ["operations", "analysis"],
        }
    )

    assert analyzed["explicit_skills"] == ["stakeholder management"]
    assert "workflow automation" in analyzed["transferable_skills"]
    assert "data analysis" in analyzed["transferable_skills"]


def test_score_transition_prefers_roles_with_overlap_and_market_strength():
    recommendation = score_transition(
        ["stakeholder management", "process improvement", "data analysis"],
        {
            "role_id": "demo-role",
            "title": "AI Operations Analyst",
            "industry": "Enterprise Services",
            "growth_score": 0.9,
            "resilience_score": 0.8,
            "normalized_skills": [
                "stakeholder management",
                "process improvement",
                "data analysis",
                "workflow automation",
            ],
            "courses": ["Course A"],
        },
    )

    assert recommendation["matched_skills"] == [
        "data analysis",
        "process improvement",
        "stakeholder management",
    ]
    assert recommendation["missing_skills"] == ["workflow automation"]
    assert recommendation["compatibility"] > 0.75


def test_build_learning_roadmap_uses_missing_skills_in_priority_order():
    roadmap = build_learning_roadmap(
        {
            "missing_skills": ["workflow automation", "dashboard reporting"],
            "courses": ["Automation Basics", "Reporting Studio"],
        }
    )

    assert roadmap[0]["skill"] == "workflow automation"
    assert roadmap[0]["recommended_course"] == "Automation Basics"
    assert roadmap[1]["recommended_course"] == "Reporting Studio"


def test_run_demo_returns_transition_report():
    final_state = run_demo(log_mode="minimal")

    assert final_state.status == "completed"
    assert final_state.outputs["final_report"]["top_match"]["title"] == "AI Operations Analyst"
    assert final_state.outputs["final_report"]["roadmap"]
