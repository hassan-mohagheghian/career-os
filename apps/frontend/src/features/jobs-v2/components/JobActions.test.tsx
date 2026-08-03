import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import { JobActions } from './JobActions'
import { TooltipProvider } from '@/shared/ui/tooltip'

function renderActions(props: Partial<Parameters<typeof JobActions>[0]> = {}) {
  const base = {
    processingStatus: null,
    onProcessV2: vi.fn(),
    onViewDetails: vi.fn(),
    onEdit: vi.fn(),
    onDelete: vi.fn(),
    onRetry: vi.fn(),
    onCancel: vi.fn(),
  }
  const merged = { ...base, ...props }
  return render(
    <TooltipProvider>
      <JobActions {...merged} />
    </TooltipProvider>
  )
}

describe('JobActions', () => {
  it('never renders text labels for actions', () => {
    renderActions()
    const banned = ['Process V2', 'Details', 'View Progress', 'View Results', 'Reprocess', 'Retry', 'Cancel', 'Edit', 'Delete', 'Process']
    for (const label of banned) {
      expect(screen.queryByText(label)).not.toBeInTheDocument()
    }
  })

  it('renders Edit icon button for created status', () => {
    renderActions({ processingStatus: null })
    expect(screen.getByRole('button', { name: 'Edit' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Process' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Details' })).toBeInTheDocument()
  })

  it('calls onEdit when Edit button clicked', () => {
    const onEdit = vi.fn()
    renderActions({ onEdit })
    fireEvent.click(screen.getByRole('button', { name: 'Edit' }))
    expect(onEdit).toHaveBeenCalled()
  })

  it('renders Delete button and calls onDelete', () => {
    const onDelete = vi.fn()
    renderActions({ onDelete })
    const del = screen.getByRole('button', { name: 'Delete' })
    expect(del).toBeInTheDocument()
    fireEvent.click(del)
    expect(onDelete).toHaveBeenCalled()
  })

  it('renders View Progress and Edit for running', () => {
    renderActions({ processingStatus: 'running' })
    expect(screen.getByRole('button', { name: 'View Progress' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Edit' })).toBeInTheDocument()
  })

  it('renders View Results, Reprocess and Edit for completed', () => {
    renderActions({ processingStatus: 'completed' })
    expect(screen.getByRole('button', { name: 'View Results' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Reprocess' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Edit' })).toBeInTheDocument()
  })

  it('renders Retry, Details and Edit for failed', () => {
    renderActions({ processingStatus: 'failed' })
    expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Details' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Edit' })).toBeInTheDocument()
  })

  it('renders Cancel and Edit for queued', () => {
    renderActions({ processingStatus: 'queued' })
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Edit' })).toBeInTheDocument()
  })

  it('calls onProcessV2 when Process button clicked', () => {
    const onProcessV2 = vi.fn()
    renderActions({ processingStatus: null, onProcessV2 })
    fireEvent.click(screen.getByRole('button', { name: 'Process' }))
    expect(onProcessV2).toHaveBeenCalled()
  })
})