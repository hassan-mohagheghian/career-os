import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { JobDetailDrawer } from './JobDetailDrawer'
import { jobApi } from '@/entities/job/api'

vi.mock('@/entities/job/api', () => ({
  jobApi: {
    getDetail: vi.fn(),
  },
}))

const sampleDetail = {
  id: 'job-1',
  title: 'Staff Engineer',
  company_name: 'Acme GmbH',
  role: 'Staff',
  location: 'Berlin',
  work_types: ['Hybrid'],
  employment_types: ['Full-time'],
  salary: '100k',
  visa: 'Strong',
  url: 'https://example.com/job',
  status: 'imported',
  scores: { overall: 90, fit: 85, success: 88, overall_grade: 'A+' },
  latest_processing_execution: null,
  description: 'A great role.',
  notes: [],
  links: [],
  analysis: null,
  workflow: [],
  updated_at: null,
  created_at: null,
}

beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(jobApi.getDetail).mockResolvedValue(sampleDetail as any)
})

function renderDrawer(jobId: string | null, onEdit: (id: string) => void = vi.fn()) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={qc}>
      <JobDetailDrawer jobId={jobId} onOpenChange={vi.fn()} onEdit={onEdit} />
    </QueryClientProvider>
  )
}

describe('JobDetailDrawer edit', () => {
  it('opens the edit drawer when Edit is clicked', async () => {
    const onEdit = vi.fn()
    renderDrawer('job-1', onEdit)

    await waitFor(() => expect(screen.getByText('Acme GmbH')).toBeInTheDocument())
    fireEvent.click(screen.getByRole('button', { name: 'Edit job' }))
    expect(onEdit).toHaveBeenCalledWith('job-1')
  })

  it('does not render the Edit button without an onEdit handler', () => {
    const qc = new QueryClient({
      defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
    })
    render(
      <QueryClientProvider client={qc}>
        <JobDetailDrawer jobId="job-1" onOpenChange={vi.fn()} />
      </QueryClientProvider>
    )
    expect(screen.queryByRole('button', { name: 'Edit job' })).not.toBeInTheDocument()
  })
})
