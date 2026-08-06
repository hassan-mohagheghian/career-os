import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { CompanyPicker } from './CompanyPicker'
import { companyApi } from '@/entities/company/api'

vi.mock('@/entities/company/api', () => ({
  companyApi: {
    listInfinite: vi.fn(),
  },
}))

const companies = {
  items: [
    { id: 'c-1', name: 'Acme GmbH', logo_url: null },
    { id: 'c-2', name: 'Initech', logo_url: null },
  ],
  next_cursor: null,
  has_more: false,
  total_items: 2,
}

beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(companyApi.listInfinite).mockResolvedValue(companies as any)
})

function renderPicker(props: Record<string, unknown> = {}) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <CompanyPicker companyId={null} companyName={null} onSelect={vi.fn()} {...(props as object)} />
    </QueryClientProvider>
  )
}

describe('CompanyPicker', () => {
  it('shows "Set company" when no company is linked', () => {
    renderPicker()
    expect(screen.getByRole('button', { name: 'Change company' })).toHaveTextContent('Set company')
  })

  it('lists companies and calls onSelect when one is picked', async () => {
    const onSelect = vi.fn()
    renderPicker({ onSelect })
    fireEvent.click(screen.getByRole('button', { name: 'Change company' }))
    await waitFor(() => expect(screen.getByText('Acme GmbH')).toBeInTheDocument())
    fireEvent.click(screen.getByText('Acme GmbH'))
    expect(onSelect).toHaveBeenCalledWith('c-1')
  })

  it('offers Unlink when a company is linked and unlinks', async () => {
    const onSelect = vi.fn()
    renderPicker({ companyId: 'c-1', companyName: 'Acme GmbH', onSelect })
    fireEvent.click(screen.getByRole('button', { name: 'Change company' }))
    await waitFor(() => expect(screen.getByText('Unlink company')).toBeInTheDocument())
    fireEvent.click(screen.getByText('Unlink company'))
    expect(onSelect).toHaveBeenCalledWith(null)
  })
})
