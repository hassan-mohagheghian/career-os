import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { CompanyDetailDrawer } from './CompanyDetailDrawer'
import { companyApi } from '@/entities/company/api'
import type { CompanyDetail } from '@/entities/company/types'

vi.mock('@/entities/company/api', () => ({
  companyApi: {
    get: vi.fn(),
  },
}))

function makeDetail(overrides: Partial<CompanyDetail> = {}): CompanyDetail {
  return {
    id: 'company-1',
    name: 'Acme GmbH',
    industry: 'Software',
    city: 'Berlin',
    country: 'Germany',
    status: 'processed',
    notes: [],
    links: [],
    jobs: [],
    scores: { overall: 80, fit: 88, success: 72, overall_grade: 'A+' },
    intelligence: null,
    parent_company_id: null,
    main_company: null,
    alias_count: 0,
    is_alias: false,
    created_at: '2026-08-01T00:00:00Z',
    updated_at: null,
    ...overrides,
  }
}

function renderDrawer(companyId: string | null, onOpenChange: (id: string | null) => void = vi.fn(), onEdit: (id: string) => void = vi.fn(), onOpenJob: (id: string) => void = vi.fn(), onReprocess: (id: string) => void = vi.fn()) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={qc}>
      <CompanyDetailDrawer
        companyId={companyId}
        onOpenChange={onOpenChange}
        onReprocess={onReprocess}
        onEdit={onEdit}
        onRelate={vi.fn()}
        relatePending={false}
        onOpenJob={onOpenJob}
      />
    </QueryClientProvider>
  )
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('CompanyDetailDrawer scores', () => {
  it('shows the processing-computed scores from the normalized company.scores', async () => {
    vi.mocked(companyApi.get).mockResolvedValue(makeDetail())
    renderDrawer('company-1')

    await waitFor(() => expect(screen.getByText('Acme GmbH')).toBeInTheDocument())
    expect(screen.getAllByText('88').length).toBeGreaterThan(0)
    expect(screen.getAllByText('72').length).toBeGreaterThan(0)
    expect(screen.getAllByText('80').length).toBeGreaterThan(0)
    expect(screen.getAllByText('A+').length).toBeGreaterThan(0)
  })

  it('falls back to the intelligence scores when the normalized scores are missing', async () => {
    vi.mocked(companyApi.get).mockResolvedValue(makeDetail({
      scores: null,
      intelligence: {
        scores: {
          fit: 77,
          success: 66,
          overall: 72,
          overall_grade: 'A',
        },
      } as CompanyDetail['intelligence'],
    }))
    renderDrawer('company-1')

    await waitFor(() => expect(screen.getByText('Acme GmbH')).toBeInTheDocument())
    expect(screen.getAllByText('77').length).toBeGreaterThan(0)
    expect(screen.getAllByText('66').length).toBeGreaterThan(0)
    expect(screen.getAllByText('72').length).toBeGreaterThan(0)
    expect(screen.getAllByText('A').length).toBeGreaterThan(0)
  })

  it('renders no score cards or explanation button for unprocessed companies', async () => {
    vi.mocked(companyApi.get).mockResolvedValue(makeDetail({
      scores: null,
      intelligence: null,
    }))
    renderDrawer('company-1')

    await waitFor(() => expect(screen.getByText('Acme GmbH')).toBeInTheDocument())
    expect(
      screen.queryByRole('button', { name: 'Show scores explanation' }),
    ).not.toBeInTheDocument()
  })
})

describe('CompanyDetailDrawer edit', () => {
  it('opens the edit drawer when Edit is clicked', async () => {
    vi.mocked(companyApi.get).mockResolvedValue(makeDetail())
    const onEdit = vi.fn()
    renderDrawer('company-1', vi.fn(), onEdit)

    await waitFor(() => expect(screen.getByText('Acme GmbH')).toBeInTheDocument())
    fireEvent.click(screen.getByRole('button', { name: 'Edit company' }))
    expect(onEdit).toHaveBeenCalledWith('company-1')
  })

  it('calls onReprocess when the header Reprocess button is clicked', async () => {
    vi.mocked(companyApi.get).mockResolvedValue(makeDetail())
    const onReprocess = vi.fn()
    renderDrawer('company-1', vi.fn(), vi.fn(), vi.fn(), onReprocess)

    await waitFor(() => expect(screen.getByText('Acme GmbH')).toBeInTheDocument())
    fireEvent.click(screen.getByRole('button', { name: 'Reprocess company' }))
    expect(onReprocess).toHaveBeenCalledWith('company-1')
  })
})

describe('CompanyDetailDrawer footer actions', () => {
  it('renders the website link at the top, next to the scores', async () => {
    vi.mocked(companyApi.get).mockResolvedValue(makeDetail({
      website: 'https://acme.dev',
      job_count: 3,
    }))
    renderDrawer('company-1')

    await waitFor(() => expect(screen.getByText('Acme GmbH')).toBeInTheDocument())
    const websiteLink = screen.getByRole('link', { name: 'Website' })
    expect(websiteLink).toHaveAttribute('href', 'https://acme.dev')
    expect(websiteLink).toHaveAttribute('target', '_blank')
  })

  it('lists the other company links below the website link at the top', async () => {
    vi.mocked(companyApi.get).mockResolvedValue(makeDetail({
      website: 'https://acme.dev',
      links: [
        { id: 1, url: 'https://acme.dev', title: 'Website', description: null, status: 'ok', created_at: null },
        { id: 2, url: 'https://acme.dev/careers', title: 'Careers',
          description: null, status: 'ok', created_at: null },
        { id: 3, url: 'https://github.com/acme', title: 'GitHub', description: null, status: 'ok', created_at: null },
      ],
      job_count: 3,
    }))
    renderDrawer('company-1')

    await waitFor(() => expect(screen.getByText('Acme GmbH')).toBeInTheDocument())
    const topCareers = screen.getAllByRole('link', { name: 'Careers' })[0]
    expect(topCareers).toHaveAttribute('href', 'https://acme.dev/careers')
    expect(topCareers).toHaveAttribute('target', '_blank')
    expect(screen.getAllByRole('link', { name: 'GitHub' })[0]).toHaveAttribute('href', 'https://github.com/acme')
    expect(
      screen.getAllByRole('link', { name: 'Website' }).some((l) => l.getAttribute('href') === 'https://acme.dev'),
    ).toBe(true)
  })

  it('does not render View All Jobs or Delete buttons', async () => {
    vi.mocked(companyApi.get).mockResolvedValue(makeDetail({ job_count: 3, website: 'https://acme.dev' }))
    renderDrawer('company-1')

    await waitFor(() => expect(screen.getByText('Acme GmbH')).toBeInTheDocument())
    expect(screen.queryByRole('button', { name: 'View All Jobs' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Delete' })).not.toBeInTheDocument()
  })
})

describe('CompanyDetailDrawer scores explanation', () => {
  it('opens the scores explanation popover on click and shows the factors', async () => {
    vi.mocked(companyApi.get).mockResolvedValue(makeDetail({
      intelligence: {
        scores: {
          fit: 88,
          success: 72,
          overall: 80,
          fit_explanation: 'Strong stack alignment',
          fit_positive_factors: ['Go + Postgres match'],
          fit_negative_factors: ['No Kafka experience'],
          success_explanation: 'Growing team',
          success_positive_factors: ['Clear engineering roadmap'],
          success_negative_factors: ['Small team'],
        },
      } as CompanyDetail['intelligence'],
    }))
    renderDrawer('company-1')

    await waitFor(() => expect(screen.getByText('Acme GmbH')).toBeInTheDocument())
    fireEvent.click(screen.getByRole('button', { name: 'Show scores explanation' }))
    expect(screen.getAllByText('Scores Explanation').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Strong stack alignment').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Go + Postgres match').length).toBeGreaterThan(0)
    expect(screen.getAllByText('No Kafka experience').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Growing team').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Clear engineering roadmap').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Small team').length).toBeGreaterThan(0)
  })

  it('does not render the scores explanation button without explanation data', async () => {
    vi.mocked(companyApi.get).mockResolvedValue(makeDetail())
    renderDrawer('company-1')

    await waitFor(() => expect(screen.getByText('Acme GmbH')).toBeInTheDocument())
    expect(
      screen.queryByRole('button', { name: 'Show scores explanation' }),
    ).not.toBeInTheDocument()
  })
})

describe('CompanyDetailDrawer recruiter for', () => {
  it('links each job a recruiter publishes to the job drawer', async () => {
    const onOpenJob = vi.fn()
    vi.mocked(companyApi.get).mockResolvedValue(makeDetail({
      company_type: 'RECRUITING_AGENCY',
      recruiter_job_count: 3,
      recruiter_for: [
        {
          company_id: 'hiring-1',
          name: 'Acme GmbH',
          job_count: 2,
          jobs: [
            { id: 'job-1', title: 'Senior Backend Engineer', location: 'Berlin' },
            { id: 'job-2', title: 'Platform Engineer', location: 'Munich' },
          ],
        },
        {
          company_id: 'hiring-2',
          name: 'Beta GmbH',
          job_count: 1,
          jobs: [{ id: 'job-3', title: 'Data Engineer', location: 'Berlin' }],
        },
      ],
    }))
    renderDrawer('company-1', vi.fn(), vi.fn(), onOpenJob)

    await waitFor(() => expect(screen.getByText('Recruiter for 3 jobs')).toBeInTheDocument())
    const acmeLink = screen.getByRole('link', { name: 'Acme GmbH' })
    expect(acmeLink).toHaveAttribute('href', '/companies?company=hiring-1')
    expect(screen.getByText('Beta GmbH')).toBeInTheDocument()
    expect(screen.getByText('2 jobs')).toBeInTheDocument()
    expect(screen.getByText('1 job')).toBeInTheDocument()

    const jobLink = screen.getByRole('link', { name: 'Senior Backend Engineer' })
    expect(jobLink).toHaveAttribute('href', '/jobs?job=job-1')
    fireEvent.click(jobLink)
    expect(onOpenJob).toHaveBeenCalledWith('job-1')
    expect(screen.getByRole('link', { name: 'Platform Engineer' })).toHaveAttribute('href', '/jobs?job=job-2')
    expect(screen.getByRole('link', { name: 'Data Engineer' })).toHaveAttribute('href', '/jobs?job=job-3')
  })

  it('does not render the section for non-recruiters', async () => {
    vi.mocked(companyApi.get).mockResolvedValue(makeDetail({ company_type: 'PRODUCT_COMPANY' }))
    renderDrawer('company-1')

    await waitFor(() => expect(screen.getByText('Acme GmbH')).toBeInTheDocument())
    expect(screen.queryByText(/Recruiter for/)).not.toBeInTheDocument()
  })
})

describe('CompanyDetailDrawer header jobs badge', () => {
  it('shows the listed-jobs count for recruiter companies', async () => {
    vi.mocked(companyApi.get).mockResolvedValue(makeDetail({
      company_type: 'RECRUITING_AGENCY',
      job_count: 0,
      recruiter_job_count: 7,
    }))
    renderDrawer('company-1')

    await waitFor(() => expect(screen.getByText('Acme GmbH')).toBeInTheDocument())
    expect(screen.getByText('7 listed')).toBeInTheDocument()
  })

  it('shows the hiring job count for product companies', async () => {
    vi.mocked(companyApi.get).mockResolvedValue(makeDetail({
      company_type: 'PRODUCT_COMPANY',
      job_count: 3,
      recruiter_job_count: 0,
    }))
    renderDrawer('company-1')

    await waitFor(() => expect(screen.getByText('Acme GmbH')).toBeInTheDocument())
    expect(screen.getByText('3 jobs')).toBeInTheDocument()
  })
})
