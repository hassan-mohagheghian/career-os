export interface CandidateSkill {
  id: string
  profile_id: string
  skill_id: number | null
  name: string
  level: number | null
  category: string | null
  confidence: number | null
  origin: string | null
  years_of_experience: number | null
  last_used: string | null
  evidence: Record<string, unknown> | null
  created_at: string | null
  updated_at: string | null
}

export interface CandidateExperience {
  id: string
  profile_id: string
  company: string
  role: string
  start_date: string | null
  end_date: string | null
  duration_months: number | null
  summary: string | null
  highlights: string[] | null
  skills: string[] | null
  evidence: Record<string, unknown> | null
}

export interface CandidateProject {
  id: string
  profile_id: string
  name: string
  description: string | null
  url: string | null
  role: string | null
  skills: string[] | null
  evidence: Record<string, unknown> | null
  start_date: string | null
  end_date: string | null
}

export interface CandidateEducation {
  id: string
  profile_id: string
  institution: string
  degree: string | null
  field: string | null
  start_date: string | null
  end_date: string | null
}

export interface CandidateCertificate {
  id: string
  profile_id: string
  name: string
  issuer: string | null
  issue_date: string | null
  credential_url: string | null
}

export interface CandidateInterest {
  id: string
  profile_id: string
  name: string
}

export interface CandidateLanguage {
  id: string
  profile_id: string
  name: string
  proficiency: string | null
}

export interface CandidateProfile {
  id: string
  candidate_id: string | null
  version: number | null
  name: string
  title: string
  headline: string
  summary: string
  location: string
  skills: CandidateSkill[]
  experiences: CandidateExperience[]
  projects: CandidateProject[]
  educations: CandidateEducation[]
  certificates: CandidateCertificate[]
  interests: CandidateInterest[]
  languages: CandidateLanguage[]
  created_at: string | null
  updated_at: string | null
}

export interface CandidateSource {
  id: string
  profile_id: string | null
  source_type: string
  version: number
  status: string
  error: string | null
  raw_text: string | null
  processed_at: string | null
  created_at: string | null
  updated_at: string | null
}

export interface CandidateVersion {
  id: string
  profile_id: string
  version: number
  snapshot: Record<string, unknown> | null
  source_versions: Record<string, number> | null
  change_summary: string | null
  created_at: string | null
  updated_at: string | null
}

export interface CandidateSourcesResult {
  items: CandidateSource[]
}

export interface CandidateVersionsResult {
  items: CandidateVersion[]
}

export interface CandidateAnalyzeResult {
  execution_id: string
  status: string
}
