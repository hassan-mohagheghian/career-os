import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom'
import { CompaniesToolbar } from './CompaniesToolbar'
import type { CompanyListItem } from '@/entities/company/types'

function makeCompany(id: string): CompanyListItem {
  return {
    id,
    name: `Company ${id}`,
    industry: 'Software',
    city: 'Berlin',
    country: 'Germany',
    company_size: '50-200',
    company_type: 'PRODUCT_COMPANY',
    logo_url: null,
    website: null,
    description: null,
    job_count: 0,
    recruiter_job_count: 0,
    scores: { overall: null, fit: null, success: null, overall_grade: null },
    processing: { status: null, current_node: null, progress_pct: null, error: null },
    latest_processing_execution: null,
    parent_company_id: null,
    main_company: null,
    alias_count: 0,
    is_alias: false,
    pinned: false,
    updated_at: null,
    created_at: '2026-08-01T00:00:00Z',
  }
}

function renderToolbar(overrides: Record<string, unknown> = {}) {
  const props = {
    query: '',
    onQueryChange: vi.fn(),
    filterIndustry: '',
    onFilterIndustryChange: vi.fn(),
    filterStatus: '',
    onFilterStatusChange: vi.fn(),
    filterPinned: false,
    onFilterPinnedChange: vi.fn(),
    items: [makeCompany('company-1'), makeCompany('company-2')],
    activeFilterCount: 0,
    onClearFilters: vi.fn(),
    ...overrides,
  }
  return render(<CompaniesToolbar {...(props as any)} />)
}

describe('CompaniesToolbar status filter', () => {
  it('renders a Status dropdown', () => {
    renderToolbar()
    expect(screen.getByText('Status')).toBeInTheDocument()
  })

  it('reports a selected status', () => {
    const onFilterStatusChange = vi.fn()
    renderToolbar({ onFilterStatusChange })
    fireEvent.click(screen.getByText('Status'))
    fireEvent.click(screen.getByText('Processed'))
    expect(onFilterStatusChange).toHaveBeenCalledWith('processed')
  })

  it('shows the active status label', () => {
    renderToolbar({ filterStatus: 'failed' })
    expect(screen.getByText('Failed')).toBeInTheDocument()
  })
})

describe('CompaniesToolbar pinned filter', () => {
  it('renders the pinned toggle', () => {
    renderToolbar()
    expect(screen.getByLabelText('Show pinned companies only')).toBeInTheDocument()
  })

  it('toggles the pinned filter on click', () => {
    const onFilterPinnedChange = vi.fn()
    renderToolbar({ onFilterPinnedChange })

    fireEvent.click(screen.getByLabelText('Show pinned companies only'))

    expect(onFilterPinnedChange).toHaveBeenCalledWith(true)
  })

  it('toggles the pinned filter off when active', () => {
    const onFilterPinnedChange = vi.fn()
    renderToolbar({ filterPinned: true, onFilterPinnedChange })

    fireEvent.click(screen.getByLabelText('Show pinned companies only'))

    expect(onFilterPinnedChange).toHaveBeenCalledWith(false)
  })
})

describe('CompaniesToolbar columns toggle', () => {
  it('renders a Columns dropdown when a toggle handler is provided', () => {
    renderToolbar({ onTogglePinnedColumn: vi.fn() })
    expect(screen.getByText('Columns')).toBeInTheDocument()
  })

  it('does not render the Columns dropdown without a toggle handler', () => {
    renderToolbar()
    expect(screen.queryByText('Columns')).not.toBeInTheDocument()
  })

  it('shows the Pinned option checked when the column is visible', async () => {
    const user = userEvent.setup()
    renderToolbar({ showPinnedColumn: true, onTogglePinnedColumn: vi.fn() })
    await user.click(screen.getByText('Columns'))
    const menu = await screen.findByRole('menu')
    expect(within(menu).getByText('Pinned')).toBeInTheDocument()
  })

  it('reports a column toggle when the Pinned option is clicked', async () => {
    const user = userEvent.setup()
    const onTogglePinnedColumn = vi.fn()
    renderToolbar({ showPinnedColumn: false, onTogglePinnedColumn })
    await user.click(screen.getByText('Columns'))
    const option = within(await screen.findByRole('menu')).getByText('Pinned')
    await user.click(option)
    expect(onTogglePinnedColumn).toHaveBeenCalledWith(true)
  })

  it('shows the Row number option and reports its toggle', async () => {
    const user = userEvent.setup()
    const onToggleRowNumberColumn = vi.fn()
    renderToolbar({ showRowNumberColumn: false, onToggleRowNumberColumn, onTogglePinnedColumn: vi.fn() })
    await user.click(screen.getByText('Columns'))
    const option = within(await screen.findByRole('menu')).getByText('Row number')
    await user.click(option)
    expect(onToggleRowNumberColumn).toHaveBeenCalledWith(true)
  })
})
