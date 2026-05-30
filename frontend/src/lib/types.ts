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
