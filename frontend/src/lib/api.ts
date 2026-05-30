import type {
  GapResponse,
  JobDetail,
  JobListItem,
  MatchResponse,
  User,
  UserProfile,
} from './types'

const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

async function request<T>(input: string, init?: RequestInit): Promise<T> {
  const res = await fetch(input, init)
  if (!res.ok) {
    const text = await res.text().catch(() => `HTTP ${res.status}`)
    throw new Error(text)
  }
  return res.json() as Promise<T>
}

export function createUser(email: string): Promise<User> {
  return request<User>(`${BASE}/users`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email }),
  })
}

export function uploadCV(file: File, userId?: string): Promise<MatchResponse> {
  const form = new FormData()
  form.append('cv', file)
  if (userId) form.append('user_id', userId)
  return request<MatchResponse>(`${BASE}/match`, { method: 'POST', body: form })
}

export function listJobs(params?: {
  category?: string
  seniority?: string
  limit?: number
}): Promise<JobListItem[]> {
  const url = new URL(`${BASE}/jobs`)
  if (params?.category) url.searchParams.set('category', params.category)
  if (params?.seniority) url.searchParams.set('seniority', params.seniority)
  if (params?.limit != null) url.searchParams.set('limit', String(params.limit))
  return request<JobListItem[]>(url.toString())
}

export function getJob(jobId: string): Promise<JobDetail> {
  return request<JobDetail>(`${BASE}/jobs/${jobId}`)
}

export function getSkillGap(jobId: string, userId: string): Promise<GapResponse> {
  return request<GapResponse>(`${BASE}/gap/${jobId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId }),
  })
}

export function getUserProfile(userId: string): Promise<UserProfile> {
  return request<UserProfile>(`${BASE}/users/${userId}/profile`)
}
