import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import { JobCard } from '@/shared/components/ProcessedCards'

const mockJob = {
  num: 1,
  company: 'Acme Corp',
  role: 'Senior Backend Engineer',
  location: 'Berlin',
  parsedLocations: ['Berlin'],
  score: 'A',
  success: 'B+',
  match: 'High',
  visa: 'Strong',
  work_type: 'Remote',
  employment_type: 'Full-time',
  applicants: '42',
  posted: '2 days ago',
  stack: 'Python, Django, PostgreSQL',
  url: 'https://example.com/job/1',
  workflow_log: '[]',
  rescoring: 0,
}

function renderCard(props = {}) {
  const defaults = {
    job: mockJob,
    rank: 1,
    onClick: vi.fn(),
    onProcess: vi.fn(),
    onDelete: vi.fn(),
    onViewWorkflow: vi.fn(),
  }
  return render(<JobCard {...defaults} {...props} />)
}

describe('JobCard action buttons', () => {
  it('renders the card with job info', () => {
    renderCard()
    expect(screen.getByText('Acme Corp')).toBeInTheDocument()
    expect(screen.getByText('Senior Backend Engineer')).toBeInTheDocument()
    expect(screen.getAllByText('A').length).toBeGreaterThan(0)
  })

  it('action buttons container is hidden by default (opacity-0)', () => {
    renderCard()
    const actionsContainer = screen.getByTitle('Process').closest('div[class*="opacity-0"]')
    expect(actionsContainer).toBeInTheDocument()
    expect(actionsContainer.className).toContain('opacity-0')
  })

  it('action buttons become visible on card hover', () => {
    renderCard()
    const card = document.querySelector('.group\\/card')
    expect(card).toBeInTheDocument()
    const actionsContainer = screen.getByTitle('Process').closest('div[class*="opacity-0"]')
    expect(actionsContainer.className).toContain('group-hover/card:opacity-100')
  })

  it('all 3 action buttons exist: Process, Workflow, Delete', () => {
    const jobWithLogs = { ...mockJob, workflow_log: JSON.stringify([{ step: 'fetch', msg: 'done' }]) }
    renderCard({ job: jobWithLogs })
    expect(screen.getByTitle('Process')).toBeInTheDocument()
    expect(screen.getByTitle('Workflow')).toBeInTheDocument()
    expect(screen.getByTitle('Delete')).toBeInTheDocument()
  })

  it('Workflow button only appears when job has workflow logs', () => {
    const jobWithLogs = { ...mockJob, workflow_log: JSON.stringify([{ step: 'fetch', msg: 'done' }]) }
    renderCard({ job: jobWithLogs })
    const actionsDiv = screen.getByTitle('Process').closest('div')
    const buttons = actionsDiv.querySelectorAll('button')
    expect(buttons.length).toBe(3)
  })

  it('Workflow button is absent when job has no logs', () => {
    renderCard()
    const actionsDiv = screen.getByTitle('Process').closest('div')
    const buttons = actionsDiv.querySelectorAll('button')
    expect(buttons.length).toBe(2)
  })

  it('action buttons use group-hover/card for visibility toggle', () => {
    renderCard()
    const actionsContainer = screen.getByTitle('Process').closest('div[class*="opacity-0"]')
    expect(actionsContainer.className).toContain('opacity-0')
    expect(actionsContainer.className).toContain('group-hover/card:opacity-100')
    expect(actionsContainer.className).toContain('transition-opacity')
  })

  it('card has group/card class for hover grouping', () => {
    renderCard()
    const card = document.querySelector('.group\\/card')
    expect(card).toBeInTheDocument()
  })

  it('clicking action buttons does not trigger card onClick', () => {
    const onClick = vi.fn()
    renderCard({ onClick })

    fireEvent.click(screen.getByTitle('Process'))
    fireEvent.click(screen.getByTitle('Delete'))

    expect(onClick).not.toHaveBeenCalled()
  })

  it('onProcess is called with job.num when Process button clicked', () => {
    const onProcess = vi.fn()
    renderCard({ onProcess })
    fireEvent.click(screen.getByTitle('Process'))
    expect(onProcess).toHaveBeenCalledWith(1)
  })

  it('onDelete is called with job.num when Delete button clicked', () => {
    const onDelete = vi.fn()
    renderCard({ onDelete })
    fireEvent.click(screen.getByTitle('Delete'))
    expect(onDelete).toHaveBeenCalledWith(1)
  })

  it('supports legacy onRescore prop', () => {
    const onRescore = vi.fn()
    renderCard({ onProcess: undefined, onRequeue: undefined, onRescore })
    fireEvent.click(screen.getByTitle('Process'))
    expect(onRescore).toHaveBeenCalledWith(1)
  })

  it('onRequeue takes priority over onRescore', () => {
    const onRescore = vi.fn()
    const onRequeue = vi.fn()
    renderCard({ onProcess: undefined, onRescore, onRequeue })
    fireEvent.click(screen.getByTitle('Process'))
    expect(onRequeue).toHaveBeenCalledWith(1)
    expect(onRescore).not.toHaveBeenCalled()
  })

  it('renders rescoring badge when rescoring is active', () => {
    renderCard({ job: { ...mockJob, rescoring: 1 } })
    expect(screen.getByText('Rescore')).toBeInTheDocument()
  })
})
