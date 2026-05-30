// ───────────────────────── System A — Job Matchmaking ─────────────────────────

export interface JobListItem {
  id: string
  title: string
  company: string | null
  location: string | null
  category: string | null
  seniority: string | null
  required_skills: string[]
  redirect_url: string
}

export interface JobDetail extends JobListItem {
  adzuna_id: string
  description: string
  nice_to_have: string[]
  soft_skills: string[]
  languages: string[]
  created_at: string
  fetched_at: string | null
  expires_at: string | null
}

export interface JobMatchResult {
  job: JobListItem
  score: number
  matched_skills: string[]
  missing_skills: string[]
}

export interface MatchResponse {
  user_id: string
  matches: JobMatchResult[]
}

export interface GapResponse {
  job_id: string
  user_id: string
  required_skills: string[]
  user_skills: string[]
  missing_skills: string[]
  matched_skills: string[]
}

export interface UserProfile {
  id: string
  user_id: string
  skills: string[]
  seniority: string | null
  languages: string[]
  updated_at: string
}

export interface User {
  id: string
  email: string
  created_at: string
}

// ───────────────────── System B — Agentic Learning System ─────────────────────
// Mirrors Agentic_learning/transition_learning/contracts.py so these types stay
// drop-in compatible when the real System B HTTP API replaces the mock routes.

export type StageType =
  | 'introduction'
  | 'conceptual'
  | 'practical'
  | 'evaluation'
  | 'reflection'

export type MasteryStatus =
  | 'not_started'
  | 'in_progress'
  | 'needs_remediation'
  | 'retry_ready'
  | 'completed'

export interface StagePayload {
  stage_id: string
  stage_type: StageType
  title: string
  instructions: string
  rubric: string[]
  context: Record<string, unknown>
  expected_output: Record<string, unknown>
  metadata: Record<string, unknown>
}

export interface CurriculumSubskill {
  subskill_id: string
  subskill_name: string
  objective: string
  conceptual_criteria: string[]
  practical_criteria: string[]
  expected_outcomes: string[]
  example_workflows: string[]
  common_mistakes: string[]
  stages: StagePayload[]
}

export interface CurriculumSkill {
  skill_id: string
  skill_name: string
  description: string
  subskills: CurriculumSubskill[]
  target_jobs: string[]
  difficulty_level: string
  prerequisites: string[]
  related_certifications: string[]
}

export interface SkillGapItem {
  skill_name: string
  gap_type: string
  priority: number
  source: string
}

export interface TargetRole {
  role_id: string
  title: string
  industry: string
}

export interface Curriculum {
  curriculum_id: string
  user_profile: Record<string, unknown>
  target_role: TargetRole
  missing_skills: SkillGapItem[]
  skills: CurriculumSkill[]
  status: string
}

/** Per-subskill progress, persisted client-side in this mock build. */
export interface SubskillProgress {
  skill_id: string
  subskill_id: string
  completed_steps: StageType[]
  current_stage: StageType | null
  mastery_status: MasteryStatus
  progress_percent: number
  retry_count: number
  latest_scores: Partial<Record<'conceptual' | 'practical' | 'final', number>>
}

/** Mock evaluation result returned by /api/learning/stage/submit. */
export interface StageEvaluation {
  stage: StageType
  score: number
  passed: boolean
  errors: string[]
  feedback: string
  retry_required: boolean
  next_stage: StageType | null
  mastery_status: MasteryStatus
}
