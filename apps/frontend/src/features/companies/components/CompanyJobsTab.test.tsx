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
})
