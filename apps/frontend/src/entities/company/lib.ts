export const RECRUITER_TYPES = ['RECRUITING_AGENCY', 'STAFFING_COMPANY'] as const

export interface RecruiterCandidate {
  company_type?: string | null
  recruiter_job_count?: number | null
}

export function isRecruiterCompany(company: RecruiterCandidate | null | undefined): boolean {
  if (!company) return false
  const typeRecruiter = RECRUITER_TYPES.includes(company.company_type as (typeof RECRUITER_TYPES)[number])
  const hasListedJobs = (company.recruiter_job_count ?? 0) > 0
  return typeRecruiter || hasListedJobs
}
