/**
 * Mock curriculum generator — produces data shaped exactly like System B's
 * `GeneratedCurriculum` contract (contracts.py). Swap the /api/learning/generate
 * route's call to this for the real System B API later with no UI changes.
 *
 * Structure mirrors the product spec: <=6 skills, exactly 5 sequential
 * subskills per skill, fixed 5-stage pipeline per subskill.
 */
import type {
  Curriculum,
  CurriculumSkill,
  CurriculumSubskill,
  LearningConcept,
  StagePayload,
  StageType,
  TargetRole,
} from '@/lib/types'
import { slugify } from '@/lib/utils'

const STAGE_SEQUENCE: StageType[] = [
  'introduction',
  'conceptual',
  'practical',
  'evaluation',
  'reflection',
]

const DIFFICULTY = ['foundational', 'intermediate', 'intermediate', 'advanced', 'advanced']

/** Five sequential subskill themes applied to any skill. */
const SUBSKILL_THEMES = [
  { idSuffix: 'Foundations', label: 'Fundamentals', verb: 'recognise the core building blocks of' },
  { idSuffix: 'Core Techniques', label: 'Core Practice', verb: 'apply the essential techniques of' },
  { idSuffix: 'Applied Practice', label: 'Applied Scenarios', verb: 'execute a realistic task using' },
  { idSuffix: 'Integration', label: 'Workflow Integration', verb: 'combine into an end-to-end workflow' },
  { idSuffix: 'Mastery & Judgment', label: 'Strategic Judgment', verb: 'make sound real-world decisions about' },
]

function buildConceptSequence(skill: string, subskill: string): LearningConcept[] {
  return [
    {
      concept_id: `${slugify(subskill)}-concept-1`,
      title: 'Start with the outcome',
      explanation: `${subskill} makes the most sense when you begin with the outcome it is supposed to create. Before techniques, frameworks, or best practices matter, the learner needs a clear picture of what better looks like in the real world: what becomes easier, what friction is removed, and what decision or workflow improves because this skill is used well.\n\nIn practice, people are rarely rewarded for naming a concept correctly. They are rewarded for helping a team move from confusion to clarity, from hesitation to action, or from noisy information to a useful decision. This first concept teaches the learner to ask what job the skill is really doing before they think about how to perform it.\n\nThat shift matters because it prevents shallow learning. If the learner can describe the improved state the skill creates, they have a stable anchor for everything that follows: the parts they need to notice, the decisions they need to make, and the standards they will later use to judge quality.`,
      example: `Imagine a team preparing for a launch and struggling to keep priorities aligned. ${subskill} becomes useful not because it sounds sophisticated, but because it helps the team decide faster, surface the right trade-offs earlier, and move with fewer surprises.`,
      intuition: `A useful first question is: what becomes clearer, faster, safer, or more coordinated when this skill is used well?`,
      checkpoints: [
        'Name the real-world friction this skill reduces.',
        'Describe who benefits when the skill is done well.',
        'State the improved outcome before thinking about method.',
      ],
      takeaway: `If you cannot describe the better outcome, you are not ready to choose the right method yet.`,
    },
    {
      concept_id: `${slugify(subskill)}-concept-2`,
      title: 'See the moving parts',
      explanation: `Once the learner understands the outcome, the next step is learning to see the structure underneath it. Every strong workflow has moving parts: inputs, signals, decision points, outputs, and moments where the work can go wrong. ${subskill} becomes much easier when the learner can identify those pieces instead of treating the skill as a single black box.\n\nThis is where teaching becomes concrete. Rather than saying "be good at ${skill.toLowerCase()}", the learner is shown what to look for: what information matters at the start, what changes in the middle, and what needs to be checked before the work is finished. That is what makes the concept usable rather than abstract.\n\nThe deeper lesson is that confident execution usually comes from good decomposition. When a learner can break the workflow into parts, they can explain it clearly, diagnose weak points, and adapt it when the situation changes.`,
      example: `A strong learner might map the workflow as input -> interpretation -> decision -> handoff -> review. Even if the exact details differ by context, seeing the pattern gives them a repeatable way to think.`,
      intuition: `When the work feels vague, break it into stages until you can point to what enters the process, what changes, and what leaves it.`,
      checkpoints: [
        'Identify the key inputs or signals.',
        'Describe what changes between the start and the end.',
        'Point out where mistakes or blind spots usually enter the workflow.',
      ],
      takeaway: `Clarity grows when the learner can see the parts of the workflow, not just the name of the skill.`,
    },
    {
      concept_id: `${slugify(subskill)}-concept-3`,
      title: 'Choose with intent',
      explanation: `Knowing the pieces is not enough. The learner also needs the reasoning layer: how to choose an approach, what trade-offs matter, and how context changes the right answer. This is the moment where the skill starts to feel professional instead of mechanical.\n\nIn real work, the best answer is rarely "always do the same thing." Sometimes speed matters more than completeness. Sometimes a rough answer is acceptable, and sometimes the situation demands extra validation because the cost of being wrong is higher. ${subskill} becomes valuable when the learner can explain those choices rather than merely list steps.\n\nTeaching this concept helps the learner move from procedure to judgment. It asks them to connect actions to reasons: why this path, why now, why this level of rigor, and why this trade-off is worth it in the current situation.`,
      example: `For example, a learner might explain that in a fast-moving decision they would prioritize speed first, but still protect one critical quality check. In a high-risk scenario, they would slow down, gather more signal, and justify that extra rigor explicitly.`,
      intuition: `A strong answer sounds like a reasoned choice, not a memorized checklist.`,
      checkpoints: [
        'Name the trade-off you are managing.',
        'Explain why one approach fits the situation better than another.',
        'Show how context changes the level of rigor or speed.',
      ],
      takeaway: `Good learners do not just describe what to do; they explain why that choice makes sense here.`,
    },
    {
      concept_id: `${slugify(subskill)}-concept-4`,
      title: 'Judge the work before you ship it',
      explanation: `The final concept is judgment. Learners need to know what success looks like, how weak work tends to fail, and what signals tell them whether their answer is actually good enough to trust. Without this, even a thoughtful approach can remain fragile because it lacks self-correction.\n\nThis is where the lesson becomes realistic. Strong practitioners do not stop at "I finished." They ask whether the result solves the intended problem, whether the reasoning holds up under scrutiny, and whether an avoidable mistake is still hiding inside the work. ${subskill} becomes durable when the learner knows how to review their own output before someone else has to.\n\nPedagogically, this concept closes the loop. The learner now has an outcome to aim for, a structure to work with, a method for choosing wisely, and a way to judge the result. That combination is what makes later evaluation feel coherent rather than sudden.`,
      example: `A practical check might sound like this: "Does this answer fit the real goal, use the right inputs, make a clear choice, and include a way to notice if I got it wrong?" That kind of review catches weak work before it spreads.`,
      intuition: `If you can explain how you would notice a weak answer, you are much closer to producing a strong one.`,
      checkpoints: [
        'Define what a strong result should look like.',
        'Name a likely failure mode or blind spot.',
        'Explain how you would catch the problem before it causes downstream damage.',
      ],
      takeaway: `Mastery includes execution, self-review, and the ability to course-correct before the stakes get higher.`,
    },
  ]
}

function conceptTitles(concepts: LearningConcept[]): string {
  if (concepts.length === 0) return 'the taught concepts'
  if (concepts.length === 1) return concepts[0].title
  return `${concepts.slice(0, -1).map((concept) => concept.title).join(', ')}, and ${concepts.at(-1)?.title}`
}

function stageFor(
  type: StageType,
  skill: string,
  subskill: string,
  index: number,
  concepts: LearningConcept[],
): StagePayload {
  const id = `${slugify(subskill)}-${type}`
  const plan = concepts.map((concept, order) => `Concept ${order + 1}: ${concept.title}`)
  const focus = conceptTitles(concepts)
  const common = {
    context: {
      learning_plan: plan,
      explained_concepts: concepts,
    },
    expected_output: {},
    metadata: { concept_count: concepts.length },
  }
  switch (type) {
    case 'introduction':
      return {
        stage_id: id,
        stage_type: type,
        title: 'Guided lesson',
        instructions: `${subskill} is taught as a short guided lesson. Move through one idea at a time, let each example settle, and build a real mental model before you are asked to explain or apply anything.`,
        rubric: ['Follow the concepts in sequence', 'Use the example to ground the idea', 'Carry the takeaway forward to the next concept'],
        context: {
          ...common.context,
          concept_sequence: concepts,
        },
        expected_output: { mode: 'concept_sequence' },
        metadata: common.metadata,
      }
    case 'conceptual':
      return {
        stage_id: id,
        stage_type: type,
        title: 'Explain the idea',
        instructions: `Before moving into practice, explain the lesson back in your own words. Stay close to what was taught and show how the ideas connect from outcome to judgment.`,
        rubric: ['Uses only the concepts that were taught', 'Connects the concepts in the right sequence', 'Explains why the reasoning works'],
        context: {
          ...common.context,
          prompt: `Using only the concepts you just learned, explain how ${subskill.toLowerCase()} works from goal to quality check. Define the core idea, connect the building blocks, explain the decision logic, and name the main failure mode to avoid.`,
        },
        expected_output: { mode: 'written_reasoning' },
        metadata: common.metadata,
      }
    case 'practical':
      return {
        stage_id: id,
        stage_type: type,
        title: 'Apply it',
        instructions: `Now turn the lesson into action. Describe how you would handle a realistic situation using the same ideas, choices, and quality checks you just learned.`,
        rubric: ['Applies the taught concepts to a believable workflow', 'Makes clear decisions and trade-offs', 'Shows how the result would be validated'],
        context: {
          ...common.context,
          prompt: `A teammate asks you to use ${subskill.toLowerCase()} in a real project. Describe the approach you would take using the concepts already taught: start with the goal, identify the key building blocks, explain the decisions you would make, and finish with the quality checks you would apply.`,
        },
        expected_output: { mode: 'applied_reasoning' },
        metadata: common.metadata,
      }
    case 'evaluation':
      return {
        stage_id: id,
        stage_type: type,
        title: 'Final synthesis',
        instructions: `This is the final synthesis. Bring together the concept, the reasoning, and the practical judgment you have built so far into one confident response.`,
        rubric: ['Reuses the taught concepts coherently', 'Combines explanation with application', 'Demonstrates judgment and validation'],
        context: {
          ...common.context,
          prompt: `Deliver a final response for ${subskill.toLowerCase()} that reuses the full teaching sequence: explain the concept clearly, show how you would apply it in practice, justify your choices, and state how you would judge whether the result is strong enough to trust.`,
        },
        expected_output: { mode: 'synthesised_evaluation' },
        metadata: common.metadata,
      }
    case 'reflection':
      return {
        stage_id: id,
        stage_type: type,
        title: 'Retry with clarity',
        instructions: `Pause, review what felt weak, and prepare a stronger retry grounded in the same concepts you already learned. Focus on what you will make clearer or more concrete this time.`,
        rubric: ['Identifies which taught concept was weak', 'Targets a concrete improvement for the retry'],
        ...common,
      }
  }
}

function buildSubskill(skill: string, index: number): CurriculumSubskill {
  const theme = SUBSKILL_THEMES[index]
  const legacyName = `${skill} — ${theme.idSuffix}`
  const name = `${skill}, ${theme.label}`
  const concepts = buildConceptSequence(skill, name)
  return {
    subskill_id: slugify(legacyName),
    subskill_name: name,
    objective: `Be able to ${theme.verb} ${skill.toLowerCase()} in a real operational context.`,
    conceptual_criteria: [`Core concept of ${theme.label.toLowerCase()}`, 'Correct reasoning'],
    practical_criteria: ['Executes the workflow', 'Produces a usable artifact'],
    expected_outcomes: [`Can ${theme.verb} ${skill.toLowerCase()}`],
    example_workflows: [`${skill} in a weekly operations cadence`],
    common_mistakes: ['Pattern-matching without understanding', 'Skipping validation'],
    stages: STAGE_SEQUENCE.map((t) => stageFor(t, skill, name, index, concepts)),
  }
}

function buildSkill(skillName: string, order: number): CurriculumSkill {
  const name = skillName
    .split(' ')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ')
  return {
    skill_id: slugify(name),
    skill_name: name,
    description: `Build real, employable capability in ${name.toLowerCase()}, moving from first principles to confident operational use.`,
    subskills: SUBSKILL_THEMES.map((_, i) => buildSubskill(name, i)),
    target_jobs: [],
    difficulty_level: DIFFICULTY[order % DIFFICULTY.length],
    prerequisites: order > 0 ? [] : [],
    related_certifications: [],
  }
}

export interface GenerateInput {
  targetRole: TargetRole
  missingSkills: string[]
  userProfile?: Record<string, unknown>
  curriculumId?: string
}

export function buildMockCurriculum({
  targetRole,
  missingSkills,
  userProfile = {},
  curriculumId,
}: GenerateInput): Curriculum {
  // De-duplicate, cap at 6 skills (product constraint).
  const seen = new Set<string>()
  const unique = missingSkills
    .map((s) => s.trim())
    .filter((s) => {
      const k = s.toLowerCase()
      if (!s || seen.has(k)) return false
      seen.add(k)
      return true
    })
    .slice(0, 6)

  const skills = (unique.length ? unique : ['workflow automation']).map((s, i) =>
    buildSkill(s, i),
  )

  return {
    curriculum_id: curriculumId ?? `curriculum-${slugify(targetRole.title)}`,
    user_profile: userProfile,
    target_role: targetRole,
    missing_skills: unique.map((s, i) => ({
      skill_name: s,
      gap_type: 'missing',
      priority: i + 1,
      source: 'matching',
    })),
    skills,
    status: 'generated',
  }
}
