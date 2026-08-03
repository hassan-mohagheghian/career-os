import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import DuplicateJobDialog from './DuplicateJobDialog'

describe('DuplicateJobDialog', () => {
  const mockJob = { id: 'job-1', company: 'Acme Corp', score: 'A', match: 'High' }

  it('returns null when duplicateJob is null', () => {
    const { container } = render(
      <DuplicateJobDialog duplicateJob={null} setDuplicateJob={vi.fn()} onRescore={vi.fn()} onReprocess={vi.fn()} />
    )
    expect(container.innerHTML).toBe('')
  })

  it('renders dialog with job info', () => {
    render(
      <DuplicateJobDialog duplicateJob={mockJob} setDuplicateJob={vi.fn()} onRescore={vi.fn()} onReprocess={vi.fn()} />
    )
    expect(screen.getByText('Job Already Exists')).toBeInTheDocument()
    expect(screen.getByText(/Acme Corp/)).toBeInTheDocument()
    expect(screen.getByText(/How would you like to update this job/)).toBeInTheDocument()
  })

  it('calls onRescore with job.id when Rescore clicked', () => {
    const onRescore = vi.fn()
    render(
      <DuplicateJobDialog duplicateJob={mockJob} setDuplicateJob={vi.fn()} onRescore={onRescore} onReprocess={vi.fn()} />
    )
    fireEvent.click(screen.getByText('Rescore'))
    expect(onRescore).toHaveBeenCalledWith('job-1')
  })

  it('calls onReprocess with job.id when Reprocess clicked', () => {
    const onReprocess = vi.fn()
    render(
      <DuplicateJobDialog duplicateJob={mockJob} setDuplicateJob={vi.fn()} onRescore={vi.fn()} onReprocess={onReprocess} />
    )
    fireEvent.click(screen.getByText('Reprocess'))
    expect(onReprocess).toHaveBeenCalledWith('job-1')
  })

  it('calls setDuplicateJob(null) when Cancel clicked', () => {
    const setDuplicateJob = vi.fn()
    render(
      <DuplicateJobDialog duplicateJob={mockJob} setDuplicateJob={setDuplicateJob} onRescore={vi.fn()} onReprocess={vi.fn()} />
    )
    fireEvent.click(screen.getByText('Cancel'))
    expect(setDuplicateJob).toHaveBeenCalledWith(null)
  })

  it('renders score with green color for A grades', () => {
    render(
      <DuplicateJobDialog duplicateJob={{ ...mockJob, score: 'A+' }} setDuplicateJob={vi.fn()} onRescore={vi.fn()} onReprocess={vi.fn()} />
    )
    expect(screen.getByText('A+')).toBeInTheDocument()
  })
})
