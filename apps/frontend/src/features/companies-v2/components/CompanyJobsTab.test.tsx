import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import CompanyJobsTab from './CompanyJobsTab'

const mockJobs = [
  { id: 'job-1', role: 'Senior Engineer', score: 'A', location: 'Berlin' },
  { id: 'job-2', role: 'Junior Developer', score: 'B', location: 'Munich' },
]

describe('CompanyJobsTab', () => {
  it('renders jobs from the passed payload', () => {
    render(<CompanyJobsTab companyId="comp-1" companyName="TechCorp" jobs={mockJobs} />)
    expect(screen.getByText('Senior Engineer')).toBeInTheDocument()
    expect(screen.getByText('Junior Developer')).toBeInTheDocument()
  })

  it('renders job count', () => {
    render(<CompanyJobsTab companyId="comp-1" companyName="TechCorp" jobs={mockJobs} />)
    expect(screen.getByText('2 linked jobs')).toBeInTheDocument()
  })

  it('renders empty state when no jobs', () => {
    render(<CompanyJobsTab companyId="comp-1" companyName="TechCorp" jobs={[]} />)
    expect(screen.getByText('No jobs linked to this company yet.')).toBeInTheDocument()
  })

  it('calls onOpenJob when job clicked', () => {
    const onOpenJob = vi.fn()
    render(<CompanyJobsTab companyId="comp-1" companyName="TechCorp" jobs={mockJobs} onOpenJob={onOpenJob} />)
    fireEvent.click(screen.getByText('Senior Engineer'))
    expect(onOpenJob).toHaveBeenCalledWith('job-1')
  })

  it('renders score badges in Overall, Success, Fit order', () => {
    const { container } = render(<CompanyJobsTab companyId="comp-1" companyName="TechCorp" jobs={[
      { id: 'job-1', role: 'Senior Engineer', score: 'A', location: 'Berlin', fit_score: 90, success_score: 70, overall_score: 80 },
    ]} />)
    const text = container.textContent ?? ''
    const overall = text.indexOf('Overall 80')
    const success = text.indexOf('Success 70')
    const fit = text.indexOf('Fit 90')
    expect(overall).toBeGreaterThan(-1)
    expect(success).toBeGreaterThan(overall)
    expect(fit).toBeGreaterThan(success)
  })
})
