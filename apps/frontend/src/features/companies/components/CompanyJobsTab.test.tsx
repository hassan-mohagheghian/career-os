import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import CompanyJobsTab from './CompanyJobsTab'

const mockJobs = [
  { id: 'job-1', role: 'Senior Engineer', score: 'A', location: 'Berlin' },
  { id: 'job-2', role: 'Junior Developer', score: 'B', location: 'Munich' },
]

describe('CompanyJobsTab', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn(() =>
      Promise.resolve({ ok: true, json: () => Promise.resolve(mockJobs) })
    ))
  })

  it('shows loading state initially', () => {
    render(<CompanyJobsTab companyId={1} />)
    expect(screen.getByText('Loading jobs...')).toBeInTheDocument()
  })

  it('renders jobs after loading', async () => {
    render(<CompanyJobsTab companyId={1} />)
    await waitFor(() => {
      expect(screen.getByText('Senior Engineer')).toBeInTheDocument()
    })
    expect(screen.getByText('Junior Developer')).toBeInTheDocument()
  })

  it('renders job count', async () => {
    render(<CompanyJobsTab companyId={1} />)
    await waitFor(() => {
      expect(screen.getByText('2 linked jobs')).toBeInTheDocument()
    })
  })

  it('renders empty state when no jobs', async () => {
    vi.stubGlobal('fetch', vi.fn(() =>
      Promise.resolve({ ok: true, json: () => Promise.resolve([]) })
    ))
    render(<CompanyJobsTab companyId={1} />)
    await waitFor(() => {
      expect(screen.getByText('No jobs linked to this company yet.')).toBeInTheDocument()
    })
  })

  it('calls onOpenJob when job clicked', async () => {
    const onOpenJob = vi.fn()
    render(<CompanyJobsTab companyId={1} onOpenJob={onOpenJob} />)
    await waitFor(() => {
      expect(screen.getByText('Senior Engineer')).toBeInTheDocument()
    })
    fireEvent.click(screen.getByText('Senior Engineer'))
    expect(onOpenJob).toHaveBeenCalledWith('job-1')
  })
})
