import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
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

function renderDrawer(companyId: string | null, onOpenChange: (id: string | null) => void = vi.fn()) {
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
          company_fit_score: 77,
          company_success_score: 66,
          company_overall_score: 72,
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
