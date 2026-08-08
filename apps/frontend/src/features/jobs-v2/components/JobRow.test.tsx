import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import { JobRow } from './JobRow'
import type { JobListItem } from '@/entities/job/types'

function makeJob(overrides: Partial<JobListItem> = {}): JobListItem {
  return {
    id: 'job-1',
    title: 'Engineer',
    company_name: 'Acme',
    location: 'Berlin',
    remote: false,
    visa_sponsorship: false,
    job_status: 'imported',
    latest_processing_execution: null,
    scores: { overall: null, fit: null, success: null },
    recommendation: null,
    pinned: false,
    updated_at: null,
    created_at: '2026-08-01T00:00:00Z',
    ...overrides,
  }
}

function renderRow(job: JobListItem, overrides: Record<string, unknown> = {}) {
  const props = {
    job,
    onProcessV2: vi.fn(),
    onViewDetails: vi.fn(),
    onEdit: vi.fn(),
    onDelete: vi.fn(),
    onTogglePinned: vi.fn(),
    ...overrides,
  }
  return render(<JobRow {...(props as any)} />)
}

describe('JobRow pinned', () => {
  it('renders the pinned toggle with the job pinned state', () => {
    renderRow(makeJob({ pinned: true }), { showPinnedColumn: true })
    expect(screen.getByLabelText('Unpin job')).toBeInTheDocument()
  })

  it('calls onTogglePinned when the pin is clicked and stops row selection', () => {
    const onTogglePinned = vi.fn()
    const onViewDetails = vi.fn()
    renderRow(makeJob(), { onTogglePinned, onViewDetails, showPinnedColumn: true })

    fireEvent.click(screen.getByLabelText('Pin job for attention'))

    expect(onTogglePinned).toHaveBeenCalled()
    expect(onViewDetails).not.toHaveBeenCalled()
  })

  it('hides the pinned toggle when the column is off', () => {
    renderRow(makeJob({ pinned: true }), { showPinnedColumn: false })
    expect(screen.queryByLabelText('Unpin job')).not.toBeInTheDocument()
    expect(screen.queryByLabelText('Pin job for attention')).not.toBeInTheDocument()
  })
})

describe('JobRow row-number column', () => {
  it('renders no row number when the column is off', () => {
    renderRow(makeJob())
    expect(screen.queryByText('3')).not.toBeInTheDocument()
  })

  it('renders the row number when the column is shown', () => {
    renderRow(makeJob(), { showRowNumberColumn: true, rowNumber: 3 })
    expect(screen.getByText('3')).toBeInTheDocument()
  })
})

describe('JobRow recommendation', () => {
  it('renders the recommendation badge', () => {
    renderRow(makeJob({ recommendation: 'apply' }))
    expect(screen.getByText('Apply')).toBeInTheDocument()
  })

  it('renders an em dash when there is no recommendation', () => {
    const { container } = renderRow(makeJob({ recommendation: null }))
    expect(container.textContent).toContain('—')
  })
})

describe('JobRow grade', () => {
  it('renders a grade badge derived from the overall score', () => {
    renderRow(makeJob({ scores: { overall: 92, fit: 90, success: 85 } }))
    expect(screen.getByText('A++')).toBeInTheDocument()
  })

  it('renders an em dash when there is no overall score', () => {
    const { container } = renderRow(makeJob())
    expect(container.textContent).toContain('—')
  })
})
