export interface Resume {
  id: number
  job_num: number
  content: string
  title: string
  created_at: string
  [key: string]: any
}

export interface LinkedInProfile {
  id: number
  profile_url: string
  data: any
  [key: string]: any
}

export interface ActiveGeneration {
  id: number
  type: string
  status: string
  step: number
  total_steps: number
  error?: string
}
