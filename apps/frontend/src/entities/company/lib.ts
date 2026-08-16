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

export const COMPANY_TYPE_LABELS: Record<string, string> = {
  PRODUCT_COMPANY: 'Product Company',
  RECRUITING_AGENCY: 'Recruiting Agency',
  STAFFING_COMPANY: 'Staffing Company',
  CONSULTING_COMPANY: 'Consulting Company',
  UNKNOWN: 'Unknown',
}

export function formatCompanyType(type: string | null | undefined): string {
  return (type && COMPANY_TYPE_LABELS[type]) || type || 'Unknown'
}

export function formatCompanyTypeShort(type: string | null | undefined): string {
  return formatCompanyType(type).replace(/ Company$/, '')
}

const COMPANY_TYPE_ROW_CLASSES: Record<string, string> = {
  PRODUCT_COMPANY: '',
  RECRUITING_AGENCY: 'bg-purple-500/5 hover:bg-purple-500/10 focus-within:bg-purple-500/10',
  STAFFING_COMPANY: 'bg-orange-500/5 hover:bg-orange-500/10 focus-within:bg-orange-500/10',
  CONSULTING_COMPANY: 'bg-teal-500/5 hover:bg-teal-500/10 focus-within:bg-teal-500/10',
  UNKNOWN: 'bg-muted/40 hover:bg-muted/60 focus-within:bg-muted/60',
}

export function companyTypeRowClasses(type: string | null | undefined): string {
  return (type && COMPANY_TYPE_ROW_CLASSES[type]) || ''
}
