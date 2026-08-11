import { describe, it, expect } from 'vitest'
import { isRecruiterCompany, RECRUITER_TYPES } from './lib'

describe('isRecruiterCompany', () => {
  it('detects RECRUITING_AGENCY companies by type', () => {
    expect(isRecruiterCompany({ company_type: 'RECRUITING_AGENCY', recruiter_job_count: 0 })).toBe(true)
  })

  it('detects STAFFING_COMPANY companies by type', () => {
    expect(isRecruiterCompany({ company_type: 'STAFFING_COMPANY', recruiter_job_count: 0 })).toBe(true)
  })

  it('detects recruiters by listed job count even without a recruiter type', () => {
    expect(isRecruiterCompany({ company_type: 'PRODUCT_COMPANY', recruiter_job_count: 3 })).toBe(true)
  })

  it('returns false for product companies with no listed jobs', () => {
    expect(isRecruiterCompany({ company_type: 'PRODUCT_COMPANY', recruiter_job_count: 0 })).toBe(false)
  })

  it('returns false for null or undefined', () => {
    expect(isRecruiterCompany(null)).toBe(false)
    expect(isRecruiterCompany(undefined)).toBe(false)
  })

  it('handles missing fields', () => {
    expect(isRecruiterCompany({})).toBe(false)
  })

  it('exposes the recruiter type list', () => {
    expect(RECRUITER_TYPES).toContain('RECRUITING_AGENCY')
    expect(RECRUITER_TYPES).toContain('STAFFING_COMPANY')
  })
})
