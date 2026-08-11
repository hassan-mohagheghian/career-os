export type ApplicationStatus =
  | 'recommended'
  | 'preparing'
  | 'ready_to_apply'
  | 'applied'
  | 'rejected'
  | 'withdrawn'

export type ApplicationDocumentType = 'tailored_resume' | 'cover_letter'

export type ApplicationArtifactType = 'preparation' | ApplicationDocumentType

export interface ApplicationFollowUp {
  id: string
  application_id: string
  scheduled_at: string | null
  note: string
  completed_at: string | null
  created_at: string | null
  updated_at: string | null
}

export interface ApplicationDocument {
  id: string
  application_id: string
  document_type: ApplicationDocumentType
  version: number
  content: string
  created_at: string | null
  updated_at: string | null
}

export interface HardSkillRecommendation {
  skill: string
  gap_level: 'missing' | 'low' | 'matching' | null
  priority: 'high' | 'medium' | 'low' | null
  why: string | null
  what_to_learn: string[]
  how_to_practice: string[]
  resources: string[]
  estimated_effort: string | null
}

export interface SoftSkillRecommendation {
  skill: string
  gap_level: 'missing' | 'low' | 'matching' | null
  priority: 'high' | 'medium' | 'low' | null
  why: string | null
  what_to_improve: string[]
  how_to_practice: string[]
}

export interface ApplicationPreparation {
  id: string
  application_id: string
  version: number
  hard_skills: HardSkillRecommendation[]
  soft_skills: SoftSkillRecommendation[]
  created_at: string | null
  updated_at: string | null
}

export interface ApplicationDetail {
  id: string
  job_id: string
  status: ApplicationStatus
  applied_at: string | null
  created_at: string | null
  updated_at: string | null
  follow_ups: ApplicationFollowUp[]
  documents: ApplicationDocument[]
  preparation: ApplicationPreparation | null
}

export interface GenerateResponse {
  execution_id: string
  status: string
  artifact: ApplicationArtifactType
}

export interface DeleteResponse {
  status: string
}

export interface UpdateApplicationInput {
  status?: ApplicationStatus
  applied_at?: string | null
}

export interface CreateFollowUpInput {
  scheduled_at?: string | null
  note?: string
}

export interface UpdateFollowUpInput {
  scheduled_at?: string | null
  note?: string
  completed?: boolean
}
