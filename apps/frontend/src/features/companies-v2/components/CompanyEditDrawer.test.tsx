import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { CompanyEditDrawer } from './CompanyEditDrawer'
import { companyApi } from '@/entities/company/api'
import type { CompanyDetail } from '@/entities/company/types'

vi.mock('@/entities/company/api', () => ({
  companyApi: {
    get: vi.fn(),
    update: vi.fn(),
  },
}))

function makeDetail(overrides: Partial<CompanyDetail> = {}): CompanyDetail {
  return {
    id: 'company-1',
    name: 'Acme GmbH',
    company_type: 'PRODUCT_COMPANY',
    notes: [],
    links: [],
    ...overrides,
  }
}

function renderDrawer(companyId: string | null, onOpenChange: (id: string | null) => void = vi.fn()) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={qc}>
      <CompanyEditDrawer companyId={companyId} onOpenChange={onOpenChange} />
    </QueryClientProvider>
  )
}

async function openTypeSelect() {
  fireEvent.click(document.getElementById('company-type') as HTMLElement)
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('CompanyEditDrawer company type select', () => {
  it('reflects the company current type and submits the chosen fixed type', async () => {
    vi.mocked(companyApi.get).mockResolvedValue(makeDetail({ company_type: 'RECRUITING_AGENCY' }))
    vi.mocked(companyApi.update).mockResolvedValue(makeDetail())
    renderDrawer('company-1')

    await waitFor(() => expect(screen.getByText('Recruiting Agency')).toBeInTheDocument())

    await openTypeSelect()
    fireEvent.click(await screen.findByText('Staffing Company'))

    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() =>
      expect(companyApi.update).toHaveBeenCalledWith(
        'company-1',
        expect.objectContaining({ company_type: 'STAFFING_COMPANY' }),
      ),
    )
  })

  it('shows all five fixed options plus Not set', async () => {
    vi.mocked(companyApi.get).mockResolvedValue(makeDetail({ company_type: null }))
    renderDrawer('company-1')

    await waitFor(() => expect(screen.getByText('Not set')).toBeInTheDocument())

    await openTypeSelect()
    for (const label of [
      'Product Company',
      'Recruiting Agency',
      'Staffing Company',
      'Consulting Company',
      'Unknown',
    ]) {
      expect(await screen.findByText(label)).toBeInTheDocument()
    }
  })

  it('submits null when Not set is selected for a null company type', async () => {
    vi.mocked(companyApi.get).mockResolvedValue(makeDetail({ company_type: null }))
    vi.mocked(companyApi.update).mockResolvedValue(makeDetail())
    renderDrawer('company-1')

    await waitFor(() => expect(screen.getByText('Not set')).toBeInTheDocument())
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() =>
      expect(companyApi.update).toHaveBeenCalledWith(
        'company-1',
        expect.objectContaining({ company_type: null }),
      ),
    )
  })
})