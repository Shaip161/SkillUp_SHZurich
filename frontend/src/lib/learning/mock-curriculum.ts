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
  { suffix: 'Foundations', verb: 'recognise the core building blocks of' },
  { suffix: 'Core Techniques', verb: 'apply the essential techniques of' },
  { suffix: 'Applied Practice', verb: 'execute a realistic task using' },
  { suffix: 'Integration', verb: 'combine into an end-to-end workflow' },
  { suffix: 'Mastery & Judgment', verb: 'make sound real-world decisions about' },
]

function stageFor(
  type: StageType,
  skill: string,
  subskill: string,
  index: number,
): StagePayload {
  const id = `${slugify(subskill)}-${type}`
  const common = { context: {}, expected_output: {}, metadata: {} }
  switch (type) {
    case 'introduction':
      return {
        stage_id: id,
        stage_type: type,
        title: 'Concept Introduction',
        instructions: `${subskill} helps you ${SUBSKILL_THEMES[index].verb} ${skill.toLowerCase()}. We'll build intuition first — why it matters operationally and where it shows up in real workflows.`,
        rubric: ['Understand the core idea', 'See where it applies', 'Connect it to prior experience'],
        ...common,
      }
    case 'conceptual':
      return {
        stage_id: id,
        stage_type: type,
        title: 'Understanding Validation',
        instructions: `Explain in your own words how ${subskill.toLowerCase()} works and why it matters. Cover the core concept, the reasoning behind it, and the main mistake to avoid.`,
        rubric: ['Explains the concept clearly', 'Reasons correctly', 'Avoids the common misconception'],
        ...common,
      }
    case 'practical':
      return {
        stage_id: id,
        stage_type: type,
        title: 'Practical Exercise',
        instructions: `Apply ${subskill.toLowerCase()} to a realistic task. Produce a concrete, usable result that shows the trigger, the key steps, decision points, and safeguards.`,
        rubric: ['Completes the expected workflow', 'Produces a usable result', 'Handles edge cases'],
        ...common,
      }
    case 'evaluation':
      return {
        stage_id: id,
        stage_type: type,
        title: 'Mastery Evaluation',
        instructions: `Give a final answer that combines the concept and the practical execution for ${subskill.toLowerCase()}. Show you can both explain and apply it.`,
        rubric: ['Combines theory and practice', 'Meets the mastery threshold', 'No critical gaps'],
        ...common,
      }
    case 'reflection':
      return {
        stage_id: id,
        stage_type: type,
        title: 'Reflection & Remediation',
        instructions: `Review the weak points from your last attempt and prepare a stronger retry. Focus on the specific reasoning gaps and what you'll change.`,
        rubric: ['Identifies the failure clearly', 'Targets a concrete weakness'],
        ...common,
      }
  }
}

function buildSubskill(skill: string, index: number): CurriculumSubskill {
  const theme = SUBSKILL_THEMES[index]
  const name = `${skill} — ${theme.suffix}`
  return {
    subskill_id: slugify(name),
    subskill_name: name,
    objective: `Be able to ${theme.verb} ${skill.toLowerCase()} in a real operational context.`,
    conceptual_criteria: [`Core concept of ${theme.suffix.toLowerCase()}`, 'Correct reasoning'],
    practical_criteria: ['Executes the workflow', 'Produces a usable artifact'],
    expected_outcomes: [`Can ${theme.verb} ${skill.toLowerCase()}`],
    example_workflows: [`${skill} in a weekly operations cadence`],
    common_mistakes: ['Pattern-matching without understanding', 'Skipping validation'],
    stages: STAGE_SEQUENCE.map((t) => stageFor(t, skill, name, index)),
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
    description: `Build real, employable capability in ${name.toLowerCase()} — from first principles to confident operational use.`,
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
