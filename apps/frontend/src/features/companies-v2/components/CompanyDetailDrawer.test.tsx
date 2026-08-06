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

function renderDrawer(companyId: string | null, onOpenChange: (id: string | null) => void = vi.fn(), onEdit: (id: string) => void = vi.fn()) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={qc}>
      <CompanyDetailDrawer
        companyId={companyId}
        onOpenChange={onOpenChange}
        onDelete={vi.fn()}
        onReprocess={vi.fn()}
        onEdit={onEdit}
        onRelate={vi.fn()}
        relatePending={false}
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

  it('shows the no-scores placeholder for unprocessed companies', async () => {
    vi.mocked(companyApi.get).mockResolvedValue(makeDetail({
      scores: null,
      intelligence: null,
    }))
    renderDrawer('company-1')

    await waitFor(() => expect(screen.getByText('No scores available yet.')).toBeInTheDocument())
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
})

describe('CompanyDetailDrawer recruiter for', () => {
  it('shows the hiring companies a recruiter publishes for', async () => {
    vi.mocked(companyApi.get).mockResolvedValue(makeDetail({
      company_type: 'RECRUITING_AGENCY',
      recruiter_job_count: 3,
      recruiter_for: [
        { company_id: 'hiring-1', name: 'Acme GmbH', job_count: 2 },
        { company_id: 'hiring-2', name: 'Beta GmbH', job_count: 1 },
      ],
    }))
    renderDrawer('company-1')

    await waitFor(() => expect(screen.getByText('Recruiter for 3 jobs')).toBeInTheDocument())
    const acmeLink = screen.getByRole('link', { name: 'Acme GmbH' })
    expect(acmeLink).toHaveAttribute('href', '/companies?company=hiring-1')
    expect(screen.getByText('Beta GmbH')).toBeInTheDocument()
    expect(screen.getByText('2 jobs')).toBeInTheDocument()
    expect(screen.getByText('1 job')).toBeInTheDocument()
  })

  it('does not render the section for non-recruiters', async () => {
    vi.mocked(companyApi.get).mockResolvedValue(makeDetail({ company_type: 'PRODUCT_COMPANY' }))
    renderDrawer('company-1')

    await waitFor(() => expect(screen.getByText('Acme GmbH')).toBeInTheDocument())
    expect(screen.queryByText(/Recruiter for/)).not.toBeInTheDocument()
  })
})
