import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import { CompanyRow } from './CompanyRow'
import type { CompanyListItem } from '@/entities/company/types'

function makeCompany(overrides: Partial<CompanyListItem> = {}): CompanyListItem {
  return {
    id: 'company-1',
    name: 'Acme GmbH',
    industry: 'Software',
    city: 'Berlin',
    country: 'Germany',
    company_size: '50-200',
    company_type: 'PRODUCT_COMPANY',
    logo_url: null,
    website: null,
    description: null,
    job_count: 3,
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
    ...overrides,
  }
}

function renderRow(company: CompanyListItem) {
  return render(
    <CompanyRow
      company={company}
      onViewDetails={vi.fn()}
      onReprocess={vi.fn()}
      onEdit={vi.fn()}
      onDelete={vi.fn()}
      onTogglePinned={vi.fn()}
    />
  )
}

describe('CompanyRow scores', () => {
  it('renders the processing-computed fit, success and overall values', () => {
    renderRow(makeCompany({ scores: { overall: 80, fit: 88, success: 72, overall_grade: 'A+' } }))

    expect(screen.getByText('88')).toBeInTheDocument()
    expect(screen.getByText('72')).toBeInTheDocument()
    expect(screen.getByText('80')).toBeInTheDocument()
    expect(screen.getByText('A+')).toBeInTheDocument()
  })

  it('shows the overall_grade computed by processing when present', () => {
    renderRow(makeCompany({ scores: { overall: 80, fit: 88, success: 72, overall_grade: 'A+' } }))
    expect(screen.getByText('A+')).toBeInTheDocument()
  })

  it('falls back to deriving the grade from the overall score', () => {
    renderRow(makeCompany({ scores: { overall: 85, fit: 88, success: 72, overall_grade: null } }))
    expect(screen.getByText('A+')).toBeInTheDocument()
  })

  it('renders placeholders when there is no processing score', () => {
    renderRow(makeCompany({ scores: { overall: null, fit: null, success: null, overall_grade: null } }))

    expect(screen.getAllByText('—').length).toBeGreaterThan(0)
    expect(screen.queryByText('A+')).not.toBeInTheDocument()
  })

  it('shows the alias badge for alias companies', () => {
    renderRow(makeCompany({
      scores: { overall: 80, fit: 88, success: 72, overall_grade: 'A+' },
      is_alias: true,
      main_company: { id: 'company-2', name: 'Acme SE' },
      parent_company_id: 'company-2',
    }))
    expect(screen.getByText('alias')).toBeInTheDocument()
  })
})

describe('CompanyRow pinned', () => {
  it('renders the pinned toggle with the company pinned state', () => {
    render(
      <CompanyRow
        company={makeCompany({ pinned: true })}
        onViewDetails={vi.fn()}
        onReprocess={vi.fn()}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
        onTogglePinned={vi.fn()}
        showPinnedColumn
      />
    )
    expect(screen.getByLabelText('Unpin company')).toBeInTheDocument()
  })

  it('calls onTogglePinned when the pin is clicked and stops row selection', () => {
    const onTogglePinned = vi.fn()
    const onViewDetails = vi.fn()
    render(
      <CompanyRow
        company={makeCompany()}
        onViewDetails={onViewDetails}
        onReprocess={vi.fn()}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
        onTogglePinned={onTogglePinned}
        showPinnedColumn
      />
    )

    fireEvent.click(screen.getByLabelText('Pin company for attention'))

    expect(onTogglePinned).toHaveBeenCalled()
    expect(onViewDetails).not.toHaveBeenCalled()
  })

  it('hides the pinned toggle when the column is off', () => {
    render(
      <CompanyRow
        company={makeCompany({ pinned: true })}
        onViewDetails={vi.fn()}
        onReprocess={vi.fn()}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
        onTogglePinned={vi.fn()}
        showPinnedColumn={false}
      />
    )
    expect(screen.queryByLabelText('Unpin company')).not.toBeInTheDocument()
    expect(screen.queryByLabelText('Pin company for attention')).not.toBeInTheDocument()
  })
})

describe('CompanyRow status', () => {
  it('renders the shared StatusBadge for the execution status', () => {
    renderRow(makeCompany({ processing: { status: 'running', current_node: null, progress_pct: 40, error: null } }))
    expect(screen.getByText('Running')).toBeInTheDocument()
  })

  it('renders a dash when there is no execution status', () => {
    renderRow(makeCompany())
    expect(screen.getAllByText('—').length).toBeGreaterThan(0)
  })
})

describe('CompanyRow jobs column', () => {
  it('shows job_count for product companies', () => {
    renderRow(makeCompany({ company_type: 'PRODUCT_COMPANY', job_count: 3, recruiter_job_count: 0 }))
    expect(screen.getByText('3')).toBeInTheDocument()
  })

  it('shows recruiter_job_count for recruiter companies', () => {
    renderRow(makeCompany({
      company_type: 'RECRUITING_AGENCY',
      job_count: 0,
      recruiter_job_count: 7,
    }))
    expect(screen.getByText('7')).toBeInTheDocument()
    expect(screen.getByTitle('7 jobs listed for clients')).toBeInTheDocument()
  })

  it('shows a dash when a recruiter has no listed jobs', () => {
    renderRow(makeCompany({ company_type: 'STAFFING_COMPANY', job_count: 0, recruiter_job_count: 0 }))
    expect(screen.getAllByText('—').length).toBeGreaterThan(0)
  })
})

describe('CompanyRow recruiter tint', () => {
  it('marks recruiter rows with the purple tint attribute', () => {
    const { container } = renderRow(makeCompany({
      company_type: 'RECRUITING_AGENCY',
      recruiter_job_count: 3,
    }))
    expect(container.querySelector('[data-recruiter="true"]')).toBeInTheDocument()
  })

  it('does not tint product company rows', () => {
    const { container } = renderRow(makeCompany({
      company_type: 'PRODUCT_COMPANY',
      recruiter_job_count: 0,
    }))
    expect(container.querySelector('[data-recruiter="false"]')).toBeInTheDocument()
  })

  it('tints companies detected as recruiters by listed job count', () => {
    const { container } = renderRow(makeCompany({
      company_type: 'PRODUCT_COMPANY',
      recruiter_job_count: 2,
    }))
    expect(container.querySelector('[data-recruiter="true"]')).toBeInTheDocument()
  })
})

describe('CompanyRow row-number column', () => {
  it('renders no row number when the column is off', () => {
    renderRow(makeCompany())
    expect(screen.queryByText('5')).not.toBeInTheDocument()
  })

  it('renders the row number when the column is shown', () => {
    render(
      <CompanyRow
        company={makeCompany()}
        onViewDetails={vi.fn()}
        onReprocess={vi.fn()}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
        onTogglePinned={vi.fn()}
        showRowNumberColumn
        rowNumber={5}
      />
    )
    expect(screen.getByText('5')).toBeInTheDocument()
  })
})
