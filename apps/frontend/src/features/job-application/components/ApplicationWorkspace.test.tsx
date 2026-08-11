import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent, within } from '@testing-library/react'
import '@testing-library/jest-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ApplicationWorkspace } from './ApplicationWorkspace'
import { jobApi } from '@/entities/job/api'
import { applicationApi } from '@/entities/application/api'
import type { JobDetail } from '@/entities/job/types'
import type { ApplicationDetail } from '@/entities/application/types'

vi.mock('@/entities/job/api', () => ({
  jobApi: { getDetail: vi.fn() },
}))

vi.mock('@/entities/application/api', () => ({
  applicationApi: {
    getByJob: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    addFollowUp: vi.fn(),
    updateFollowUp: vi.fn(),
    deleteFollowUp: vi.fn(),
    generatePreparation: vi.fn(),
    generateDocument: vi.fn(),
    updateDocument: vi.fn(),
    deleteDocument: vi.fn(),
  },
}))

vi.mock('@/shared/api/processingEvents', () => ({
  subscribeProcessingEvents: () => () => {},
}))

const sampleJob: JobDetail = {
  id: 'job-1',
  title: 'Staff Engineer',
  company_name: 'Acme GmbH',
  company_id: 'company-1',
  role: 'Staff',
  location: 'Berlin',
  work_types: ['Hybrid'],
  employment_types: ['Full-time'],
  salary: '100k',
  visa: 'Strong',
  url: 'https://example.com/job',
  status: 'imported',
  scores: { overall: 90, fit: 85, success: 88 },
  latest_processing_execution: null,
  description: 'A great role.',
  notes: [],
  links: [],
  analysis: null,
  related_companies: [],
  updated_at: null,
  created_at: null,
}

const sampleApplication: ApplicationDetail = {
  id: 'app-1',
  job_id: 'job-1',
  status: 'recommended',
  applied_at: null,
  created_at: null,
  updated_at: null,
  follow_ups: [],
  documents: [],
  preparation: null,
}

beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(jobApi.getDetail).mockResolvedValue(sampleJob)
})

function renderWorkspace(application: ApplicationDetail | null = sampleApplication) {
  vi.mocked(applicationApi.getByJob).mockImplementation(() =>
    application
      ? Promise.resolve(application)
      : Promise.reject({ status: 404, message: 'not found' })
  )
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={qc}>
      <ApplicationWorkspace jobId="job-1" />
    </QueryClientProvider>
  )
}

describe('ApplicationWorkspace', () => {
  it('renders the workspace header and sections for an existing application', async () => {
    renderWorkspace()

    await waitFor(() => expect(screen.getByText('Staff Engineer')).toBeInTheDocument())
    expect(screen.getByText('Back to Job')).toBeInTheDocument()
    expect(screen.getByText('Application')).toBeInTheDocument()
    expect(screen.getByText('Preparation')).toBeInTheDocument()
    expect(screen.getByText('Documents')).toBeInTheDocument()
  })

  it('shows the empty state and creates an application', async () => {
    renderWorkspace(null)

    await waitFor(() => expect(screen.getByText('No application yet')).toBeInTheDocument())
    vi.mocked(applicationApi.create).mockResolvedValue(sampleApplication)

    fireEvent.click(screen.getByRole('button', { name: /Create Application/ }))
    await waitFor(() => {
      expect(applicationApi.create).toHaveBeenCalledWith('job-1')
    })
  })

  it('renders the preparation generate button without a plan', async () => {
    renderWorkspace()

    await waitFor(() => expect(screen.getByText('Preparation')).toBeInTheDocument())
    const section = screen.getByText('Preparation').closest('div')!
    expect(within(section).getByText(/No preparation plan yet/)).toBeInTheDocument()
    fireEvent.click(within(section).getByRole('button', { name: /Generate/ }))
    await waitFor(() => {
      expect(applicationApi.generatePreparation).toHaveBeenCalledWith('app-1')
    })
  })

  it('renders document generate buttons without documents', async () => {
    renderWorkspace()

    await waitFor(() => expect(screen.getByText('Documents')).toBeInTheDocument())
    const section = screen.getByText('Documents').closest('div')!
    expect(within(section).getByText('Tailored Resume')).toBeInTheDocument()
    expect(within(section).getByText('Cover Letter')).toBeInTheDocument()
  })
})
