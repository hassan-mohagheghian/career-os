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
    favorite: false,
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
    onToggleFavorite: vi.fn(),
    ...overrides,
  }
  return render(<JobRow {...(props as any)} />)
}

describe('JobRow favorites', () => {
  it('renders the favorite toggle with the job favorite state', () => {
    renderRow(makeJob({ favorite: true }))
    expect(screen.getByLabelText('Remove from favorites')).toBeInTheDocument()
  })

  it('calls onToggleFavorite when the star is clicked and stops row selection', () => {
    const onToggleFavorite = vi.fn()
    const onViewDetails = vi.fn()
    renderRow(makeJob(), { onToggleFavorite, onViewDetails })

    fireEvent.click(screen.getByLabelText('Add to favorites'))

    expect(onToggleFavorite).toHaveBeenCalled()
    expect(onViewDetails).not.toHaveBeenCalled()
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
