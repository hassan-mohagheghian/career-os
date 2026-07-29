export interface Job {
  num: number
  company: string
  role: string
  location: string
  score: string
  match: string
  overall_score: number | null
  fit_score: number | null
  success_score: number | null
  stack: string
  visa: string
  work_type: string
  employment_type: string
  posted_at: string | null
  created_at: string
  applicants: string | null
  locations: string | null
  linked_company: number | null
  status: string
  current_node: string | null
  progress_pct: number
  error: string | null
  [key: string]: any
}

export interface JobAgg {
  total: number
  high_match: number
  apply_now: number
  remote: number
  [key: string]: number
}

export interface JobWithLocations extends Job {
  parsedLocations: string[]
}

export interface JobsResponse {
  jobs: Job[]
  total: number
  agg: JobAgg
}

export type SortField = 'created_at' | 'overall_score' | 'fit_score' | 'success_score' | 'num' | 'company' | 'location' | 'applicants' | 'posted_at' | 'apply_time' | 'response_time'
