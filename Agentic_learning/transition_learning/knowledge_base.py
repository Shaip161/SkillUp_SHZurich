"""Hardcoded MVP knowledge layer for TransitionAI learning workflows."""

from __future__ import annotations

from dataclasses import dataclass, field

from SkillUp_SHZurich.Agentic_learning.transition_learning.contracts import (
    CurriculumSkill,
    CurriculumSubskill,
    SkillTemplate,
    StagePayload,
    StageType,
    SubskillTemplate,
)

STAGE_SEQUENCE: tuple[StageType, ...] = (
    "introduction",
    "conceptual",
    "practical",
    "evaluation",
    "reflection",
)

CONCEPTUAL_RUBRIC: tuple[str, ...] = (
    "Understands the core concept.",
    "Explains the concept with correct reasoning.",
    "Avoids the most common misconception.",
)

PRACTICAL_RUBRIC: tuple[str, ...] = (
    "Completes the task with the expected workflow.",
    "Produces an operationally usable result.",
    "Shows correct execution rather than superficial pattern matching.",
)

EVALUATION_RUBRIC: tuple[str, ...] = (
    "Combines conceptual understanding and practical execution.",
    "Meets the minimum mastery threshold for progression.",
)

REFLECTION_RUBRIC: tuple[str, ...] = (
    "Explains the failed reasoning clearly.",
    "Targets a concrete weakness for retry.",
)

ERROR_CATEGORIES: tuple[str, ...] = (
    "conceptual misunderstanding",
    "practical execution mistake",
    "incomplete reasoning",
    "repeated misconception",
    "careless error",
)

CONCEPTUAL_PASS_THRESHOLD = 0.72
PRACTICAL_PASS_THRESHOLD = 0.70
FINAL_PASS_THRESHOLD = 0.75


@dataclass(frozen=True)
class SkillDefinition:
    skill_template: SkillTemplate
    subskill_templates: list[SubskillTemplate] = field(default_factory=list)
    remediation_slots: list[str] = field(default_factory=list)


def _skill_id_from_name(skill_name: str) -> str:
    return str(skill_name).strip().lower().replace(" ", "_")


def _build_stage_payloads(skill_name: str, subskill: SubskillTemplate) -> list[StagePayload]:
    skill_label = skill_name.strip()
    subskill_label = subskill.subskill_name.strip()
    shared_context = {
        "objective": subskill.objective,
        "expected_outcomes": list(subskill.expected_outcomes),
        "example_workflows": list(subskill.example_workflows),
        "common_mistakes": list(subskill.common_mistakes),
    }
    return [
        StagePayload(
            stage_id=f"{subskill.subskill_id}-introduction",
            stage_type="introduction",
            title=f"Introduction to {subskill_label}",
            instructions=f"Introduce {subskill_label} as part of {skill_label} using the learner's prior operational context.",
            rubric=["Connect the topic to prior experience.",
                    "Build intuition before technical detail."],
            context=shared_context,
            expected_output={"content_type": "explanation",
                             "interaction": "guided",
                             "key_takeaways": list(subskill.expected_outcomes),
                             "analogy_required": True},
            metadata={"fixed_stage_order": 1,
                      "stage_executor": "introduction"},
        ),
        StagePayload(
            stage_id=f"{subskill.subskill_id}-conceptual",
            stage_type="conceptual",
            title=f"Conceptual understanding of {subskill_label}",
            instructions=f"Check whether the learner can explain and reason about {subskill_label}.",
            rubric=list(CONCEPTUAL_RUBRIC),
            context=shared_context,
            expected_output={"content_type": "open_answer",
                             "evaluation_mode": "rubric",
                             "expected_concepts": list(subskill.conceptual_criteria),
                             "misconception_hints": list(subskill.common_mistakes),
                             "passing_threshold": CONCEPTUAL_PASS_THRESHOLD},
            metadata={"fixed_stage_order": 2, "stage_executor": "conceptual"},
        ),
        StagePayload(
            stage_id=f"{subskill.subskill_id}-practical",
            stage_type="practical",
            title=f"Practical exercise for {subskill_label}",
            instructions=f"Ask the learner to apply {subskill_label} in a realistic workforce-transition task.",
            rubric=list(PRACTICAL_RUBRIC),
            context=shared_context,
            expected_output={"content_type": "exercise",
                             "evaluation_mode": "deterministic_when_possible",
                             "required_elements": list(subskill.practical_criteria),
                             "expected_outcomes": list(subskill.expected_outcomes),
                             "workflow_markers": list(subskill.example_workflows),
                             "passing_threshold": PRACTICAL_PASS_THRESHOLD},
            metadata={"fixed_stage_order": 3, "stage_executor": "practical"},
        ),
        StagePayload(
            stage_id=f"{subskill.subskill_id}-evaluation",
            stage_type="evaluation",
            title=f"Final evaluation for {subskill_label}",
            instructions=f"Aggregate conceptual and practical performance for {subskill_label} before progression.",
            rubric=list(EVALUATION_RUBRIC),
            context=shared_context,
            expected_output={"content_type": "score_and_feedback",
                             "evaluation_mode": "aggregated",
                             "thresholds": {
                                 "conceptual": CONCEPTUAL_PASS_THRESHOLD,
                                 "practical": PRACTICAL_PASS_THRESHOLD,
                                 "final": FINAL_PASS_THRESHOLD,
                             },
                             "weights": {
                                 "conceptual": 0.45,
                                 "practical": 0.45,
                                 "integration": 0.10,
                             }},
            metadata={"fixed_stage_order": 4, "stage_executor": "evaluation"},
        ),
        StagePayload(
            stage_id=f"{subskill.subskill_id}-reflection",
            stage_type="reflection",
            title=f"Reflection and remediation for {subskill_label}",
            instructions=f"Prepare targeted remediation for failed concepts in {subskill_label} if the learner does not pass.",
            rubric=list(REFLECTION_RUBRIC),
            context=shared_context,
            expected_output={"content_type": "remediation",
                             "evaluation_mode": "post_failure",
                             "retry_focus": list(subskill.conceptual_criteria + subskill.practical_criteria),
                             "needs_retry": True},
            metadata={"fixed_stage_order": 5,
                      "error_categories": list(ERROR_CATEGORIES),
                      "stage_executor": "reflection"},
        ),
    ]


_SKILL_DEFINITIONS: dict[str, SkillDefinition] = {
    "workflow automation": SkillDefinition(
        skill_template=SkillTemplate(
            skill_id="workflow_automation",
            skill_name="workflow automation",
            description="Design and improve repeatable workflows with lightweight automation.",
            subskills=["process mapping",
                       "automation design", "exception handling"],
            target_jobs=["AI Operations Analyst", "Operations Manager"],
            difficulty_level="intermediate",
            prerequisites=["process improvement"],
            related_certifications=["Workflow Automation Foundations"],
        ),
        subskill_templates=[
            SubskillTemplate(
                subskill_id="workflow_automation_process_mapping",
                subskill_name="Process mapping",
                objective="Translate an operational workflow into a clear automation-ready flow.",
                expected_outcomes=["Maps a workflow from trigger to outcome."],
                conceptual_criteria=[
                    "Recognizes handoff points and repetitive steps."],
                practical_criteria=[
                    "Produces an automation-ready workflow outline."],
                example_workflows=["Incident routing", "Request intake"],
                common_mistakes=["Automating unclear steps",
                                 "Ignoring exceptions"],
            ),
            SubskillTemplate(
                subskill_id="workflow_automation_design",
                subskill_name="Automation design",
                objective="Choose a safe automation pattern for a repeated operational task.",
                expected_outcomes=[
                    "Explains when and how to automate a workflow."],
                conceptual_criteria=[
                    "Distinguishes automation from ad hoc scripting."],
                practical_criteria=[
                    "Designs a basic rule-based automation flow."],
                example_workflows=["Approval routing", "Ticket enrichment"],
                common_mistakes=["Automating without guardrails",
                                 "Skipping validation checks"],
            ),
            SubskillTemplate(
                subskill_id="workflow_automation_exception_handling",
                subskill_name="Exception handling",
                objective="Design fallback paths when automation cannot proceed safely.",
                expected_outcomes=[
                    "Adds escalation and fallback logic to a workflow."],
                conceptual_criteria=[
                    "Identifies where automation should stop and escalate."],
                practical_criteria=[
                    "Adds error-handling paths to an automated flow."],
                example_workflows=[
                    "Data validation failures", "Missing approval owner"],
                common_mistakes=["Silent failures", "No manual fallback"],
            ),
            SubskillTemplate(
                subskill_id="workflow_automation_tool_selection",
                subskill_name="Tool selection",
                objective="Choose a workflow automation approach that fits the risk, ownership, and complexity of the task.",
                expected_outcomes=[
                    "Chooses an automation pattern that fits the workflow and governance needs."],
                conceptual_criteria=[
                    "Explains how workflow stability and governance affect tool choice."],
                practical_criteria=[
                    "Selects a trigger, owner, and validation path for an automation scenario."],
                example_workflows=[
                    "Scheduled report distribution", "Low-risk request routing"],
                common_mistakes=[
                    "Choosing tools before defining the workflow", "Ignoring governance constraints"],
            ),
            SubskillTemplate(
                subskill_id="workflow_automation_monitoring_optimization",
                subskill_name="Monitoring and optimization",
                objective="Monitor automated workflows and improve them based on exceptions, throughput, and business impact.",
                expected_outcomes=[
                    "Defines monitoring signals and an improvement loop for an automated workflow."],
                conceptual_criteria=[
                    "Explains why automation needs monitoring, alerts, and periodic review."],
                practical_criteria=[
                    "Defines workflow metrics, alerts, and a simple optimization plan."],
                example_workflows=[
                    "Automation failure monitoring", "Cycle-time improvement review"],
                common_mistakes=["No monitoring metrics",
                                 "Optimizing without baseline data"],
            ),
        ],
        remediation_slots=["concept_rebuild",
                           "guided_retry", "worked_example"],
    ),
    "dashboard reporting": SkillDefinition(
        skill_template=SkillTemplate(
            skill_id="dashboard_reporting",
            skill_name="dashboard reporting",
            description="Design dashboard outputs that support decisions and operational monitoring.",
            subskills=["metric design", "dashboard structuring",
                       "insight communication"],
            target_jobs=["AI Operations Analyst", "Customer Success Lead"],
            difficulty_level="intermediate",
            prerequisites=["data analysis"],
            related_certifications=["Reporting Studio"],
        ),
        subskill_templates=[
            SubskillTemplate(
                subskill_id="dashboard_reporting_metric_design",
                subskill_name="Metric design",
                objective="Choose useful metrics that reflect operational performance.",
                expected_outcomes=[
                    "Defines a metric aligned with a business objective."],
                conceptual_criteria=[
                    "Distinguishes vanity metrics from decision metrics."],
                practical_criteria=["Selects the right KPI for a scenario."],
                example_workflows=["Service level monitoring",
                                   "Customer retention review"],
                common_mistakes=["Too many KPIs", "No business objective"],
            ),
            SubskillTemplate(
                subskill_id="dashboard_reporting_dashboard_structuring",
                subskill_name="Dashboard structuring",
                objective="Organize a dashboard so the most important signals are obvious.",
                expected_outcomes=[
                    "Creates a simple and readable dashboard layout."],
                conceptual_criteria=["Explains hierarchy of information."],
                practical_criteria=[
                    "Places key metrics and context in a usable layout."],
                example_workflows=[
                    "Operations performance dashboard", "Client health dashboard"],
                common_mistakes=["Visual clutter", "No prioritization"],
            ),
            SubskillTemplate(
                subskill_id="dashboard_reporting_insight_communication",
                subskill_name="Insight communication",
                objective="Explain what changed, why it matters, and what action should follow.",
                expected_outcomes=[
                    "Writes a concise interpretation of dashboard signals."],
                conceptual_criteria=["Links evidence to action."],
                practical_criteria=[
                    "Summarizes performance for stakeholders."],
                example_workflows=[
                    "Weekly operations summary", "Quarterly health review"],
                common_mistakes=[
                    "Reading numbers without insight", "No recommended action"],
            ),
            SubskillTemplate(
                subskill_id="dashboard_reporting_stakeholder_tailoring",
                subskill_name="Stakeholder tailoring",
                objective="Tailor dashboard views and explanations to the decisions different stakeholders need to make.",
                expected_outcomes=[
                    "Adapts dashboard framing for operators, managers, and executives."],
                conceptual_criteria=[
                    "Explains how audience changes the level of detail and framing."],
                practical_criteria=[
                    "Adjusts a dashboard narrative for a specific stakeholder."],
                example_workflows=[
                    "Executive performance review", "Team operations stand-up"],
                common_mistakes=[
                    "Same dashboard for every audience", "No decision linkage"],
            ),
            SubskillTemplate(
                subskill_id="dashboard_reporting_data_quality_guardrails",
                subskill_name="Data quality guardrails",
                objective="Protect dashboard outputs from stale, incomplete, or misleading data.",
                expected_outcomes=[
                    "Defines checks that keep dashboard metrics trustworthy."],
                conceptual_criteria=[
                    "Explains why freshness, completeness, and metric definitions matter."],
                practical_criteria=[
                    "Lists validation checks or alerts for dashboard data."],
                example_workflows=["Data freshness alert",
                                   "Broken KPI definition review"],
                common_mistakes=["Unvalidated metrics",
                                 "No alert for stale data"],
            ),
        ],
        remediation_slots=["metric_checklist",
                           "annotated_example", "guided_retry"],
    ),
    "vendor coordination": SkillDefinition(
        skill_template=SkillTemplate(
            skill_id="vendor_coordination",
            skill_name="vendor coordination",
            description="Coordinate external partners with clear deliverables, timelines, and escalation paths.",
            subskills=["handoff clarity",
                       "milestone tracking", "escalation management"],
            target_jobs=["Green Transition Project Coordinator"],
            difficulty_level="intermediate",
            prerequisites=["stakeholder management", "project coordination"],
            related_certifications=[
                "Supplier Management for Transformation Programs"],
        ),
        subskill_templates=[
            SubskillTemplate(
                subskill_id="vendor_coordination_handoff_clarity",
                subskill_name="Handoff clarity",
                objective="Define clear deliverables, owners, and acceptance criteria with vendors.",
                expected_outcomes=["Creates a clear handoff definition."],
                conceptual_criteria=[
                    "Explains what makes an external dependency clear."],
                practical_criteria=[
                    "Documents a vendor handoff without ambiguity."],
                example_workflows=["Implementation handoff",
                                   "Reporting deliverable handoff"],
                common_mistakes=["Ambiguous ownership",
                                 "No acceptance criteria"],
            ),
            SubskillTemplate(
                subskill_id="vendor_coordination_milestone_tracking",
                subskill_name="Milestone tracking",
                objective="Track vendor progress with explicit milestones and risks.",
                expected_outcomes=[
                    "Builds a milestone view for partner work."],
                conceptual_criteria=[
                    "Explains milestone versus task-level tracking."],
                practical_criteria=["Produces a milestone and risk summary."],
                example_workflows=[
                    "Sustainability data submission", "Platform rollout"],
                common_mistakes=[
                    "Tracking tasks without milestones", "No risk flagging"],
            ),
            SubskillTemplate(
                subskill_id="vendor_coordination_escalation_management",
                subskill_name="Escalation management",
                objective="Escalate vendor delays or quality issues with the right level of urgency.",
                expected_outcomes=["Chooses an appropriate escalation path."],
                conceptual_criteria=[
                    "Recognizes when escalation is necessary."],
                practical_criteria=["Writes a structured escalation update."],
                example_workflows=["Missed reporting deadline",
                                   "Incorrect deliverable quality"],
                common_mistakes=["Escalating too late",
                                 "Escalating without evidence"],
            ),
            SubskillTemplate(
                subskill_id="vendor_coordination_risk_alignment",
                subskill_name="Risk alignment",
                objective="Align vendor risks with project impact, mitigation actions, and stakeholder visibility.",
                expected_outcomes=[
                    "Creates a vendor risk view with impact, owner, and mitigation."],
                conceptual_criteria=[
                    "Explains how vendor risk differs from routine status tracking."],
                practical_criteria=[
                    "Creates a risk log with owner, impact, and mitigation."],
                example_workflows=["Supplier delay risk log",
                                   "External dependency review"],
                common_mistakes=["No impact assessment",
                                 "Risks without owners"],
            ),
            SubskillTemplate(
                subskill_id="vendor_coordination_stakeholder_communication",
                subskill_name="Stakeholder communication",
                objective="Communicate vendor status clearly to internal stakeholders with the right level of detail and actionability.",
                expected_outcomes=[
                    "Writes a concise stakeholder update with status, risk, and decision points."],
                conceptual_criteria=[
                    "Explains what internal stakeholders need to know about vendor progress."],
                practical_criteria=[
                    "Writes a structured stakeholder update with decision points."],
                example_workflows=["Weekly steering update",
                                   "Project status escalation summary"],
                common_mistakes=["Status without decision point",
                                 "Too much detail for the audience"],
            ),
        ],
        remediation_slots=["decision_tree",
                           "escalation_template", "guided_retry"],
    ),
}


def list_supported_skill_names() -> list[str]:
    return sorted(_SKILL_DEFINITIONS.keys())


def get_skill_definition(skill_name: str) -> SkillDefinition:
    normalized_name = str(skill_name).strip().lower()
    if normalized_name not in _SKILL_DEFINITIONS:
        raise KeyError(f"Unsupported MVP skill: {skill_name}")
    return _SKILL_DEFINITIONS[normalized_name]


def build_curriculum_skill_skeleton(skill_name: str) -> CurriculumSkill:
    definition = get_skill_definition(skill_name)
    skill_template = definition.skill_template
    subskills = []
    for subskill in definition.subskill_templates:
        subskills.append(
            CurriculumSubskill(
                subskill_id=subskill.subskill_id,
                subskill_name=subskill.subskill_name,
                objective=subskill.objective,
                conceptual_criteria=list(subskill.conceptual_criteria),
                practical_criteria=list(subskill.practical_criteria),
                expected_outcomes=list(subskill.expected_outcomes),
                example_workflows=list(subskill.example_workflows),
                common_mistakes=list(subskill.common_mistakes),
                stages=_build_stage_payloads(
                    skill_template.skill_name, subskill),
            )
        )
    return CurriculumSkill(
        skill_id=skill_template.skill_id or _skill_id_from_name(
            skill_template.skill_name),
        skill_name=skill_template.skill_name,
        description=skill_template.description,
        subskills=subskills,
        target_jobs=list(skill_template.target_jobs),
        difficulty_level=skill_template.difficulty_level,
        prerequisites=list(skill_template.prerequisites),
        related_certifications=list(skill_template.related_certifications),
    )


def select_catalog_skills(missing_skills: list[str]) -> list[CurriculumSkill]:
    selected: list[CurriculumSkill] = []
    seen: set[str] = set()
    for skill_name in missing_skills:
        normalized_name = str(skill_name).strip().lower()
        if normalized_name in seen or normalized_name not in _SKILL_DEFINITIONS:
            continue
        selected.append(build_curriculum_skill_skeleton(normalized_name))
        seen.add(normalized_name)
    return selected
