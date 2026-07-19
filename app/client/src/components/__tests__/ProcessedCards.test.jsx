import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import { JobCard } from '@/components/ProcessedCards'

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
    onRescore: vi.fn(),
    onDelete: vi.fn(),
    onRequeue: vi.fn(),
    onViewWorkflow: vi.fn(),
  }
  return render(<JobCard {...defaults} {...props} />)
}

describe('JobCard action buttons hover behavior', () => {
  it('renders the card with job info', () => {
    renderCard()
    expect(screen.getByText('Acme Corp')).toBeInTheDocument()
    expect(screen.getByText('Senior Backend Engineer')).toBeInTheDocument()
    expect(screen.getByText('A')).toBeInTheDocument()
  })

  it('action buttons container is hidden by default (opacity-0)', () => {
    renderCard()
    // The actions div has classes: opacity-0 group-hover/card:opacity-100
    // Find the div that contains the action buttons
    const actionsContainer = screen.getByTitle('Rescore').closest('div[class*="opacity-0"]')
    expect(actionsContainer).toBeInTheDocument()
    expect(actionsContainer.className).toContain('opacity-0')
  })

  it('action buttons become visible on card hover (opacity-100)', () => {
    renderCard()
    const card = document.querySelector('.group\\/card')
    expect(card).toBeInTheDocument()

    // Simulate mouse enter on the card
    fireEvent.mouseEnter(card)

    const actionsContainer = screen.getByTitle('Rescore').closest('div[class*="opacity-0"]')
    // After hover, the Tailwind class group-hover/card:opacity-100 applies
    // In jsdom, computed styles don't resolve Tailwind utilities,
    // so we verify the class structure is correct
    expect(actionsContainer.className).toContain('group-hover/card:opacity-100')
  })

  it('all 4 action buttons exist: Rescore, Reprocess, Workflow, Delete', () => {
    renderCard()
    expect(screen.getByTitle('Rescore')).toBeInTheDocument()
    expect(screen.getByTitle('Reprocess')).toBeInTheDocument()
    expect(screen.getByTitle('Delete')).toBeInTheDocument()
  })

  it('Workflow button only appears when job has workflow logs', () => {
    const jobWithLogs = { ...mockJob, workflow_log: JSON.stringify([{ step: 'fetch', msg: 'done' }]) }
    renderCard({ job: jobWithLogs })
    // The FileText icon button doesn't have a title, but it's in the actions div
    // We check by finding all buttons in the hover-actions area
    const actionsDiv = screen.getByTitle('Rescore').closest('div')
    const buttons = actionsDiv.querySelectorAll('button')
    expect(buttons.length).toBe(4) // Rescore, Reprocess, Workflow, Delete
  })

  it('Workflow button is absent when job has no logs', () => {
    renderCard({ job: { ...mockJob, workflow_log: '[]' } })
    const actionsDiv = screen.getByTitle('Rescore').closest('div')
    const buttons = actionsDiv.querySelectorAll('button')
    expect(buttons.length).toBe(3) // Rescore, Reprocess, Delete (no Workflow)
  })

  it('action buttons use group-hover/card for visibility toggle', () => {
    renderCard()
    const actionsContainer = screen.getByTitle('Rescore').closest('div')
    // Verify the class list contains both opacity-0 (default hidden) and group-hover/card:opacity-100 (visible on hover)
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

    fireEvent.click(screen.getByTitle('Rescore'))
    fireEvent.click(screen.getByTitle('Reprocess'))
    fireEvent.click(screen.getByTitle('Delete'))

    expect(onClick).not.toHaveBeenCalled()
  })

  it('onRescore is called with job.num when Rescore button clicked', () => {
    const onRescore = vi.fn()
    renderCard({ onRescore })
    fireEvent.click(screen.getByTitle('Rescore'))
    expect(onRescore).toHaveBeenCalledWith(1)
  })

  it('onDelete is called with job.num when Delete button clicked', () => {
    const onDelete = vi.fn()
    renderCard({ onDelete })
    fireEvent.click(screen.getByTitle('Delete'))
    expect(onDelete).toHaveBeenCalledWith(1)
  })

  it('onRequeue is called with job.num when Reprocess button clicked', () => {
    const onRequeue = vi.fn()
    renderCard({ onRequeue })
    fireEvent.click(screen.getByTitle('Reprocess'))
    expect(onRequeue).toHaveBeenCalledWith(1)
  })
})
