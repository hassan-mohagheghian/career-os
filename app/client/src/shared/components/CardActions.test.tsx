import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import CardActions from './CardActions'

describe('CardActions — job processing variant (size=sm)', () => {
  const base = {
    onDelete: vi.fn(),
    onProcess: vi.fn(),
    onCancel: vi.fn(),
    onReset: vi.fn(),
  }

  it('created status: shows Start text button, Reset, Delete', () => {
    render(<CardActions {...base} status="created" size="sm" />)
    expect(screen.getByText('Start')).toBeInTheDocument()
    expect(screen.getByTitle('Reset')).toBeInTheDocument()
    expect(screen.getByTitle('Delete')).toBeInTheDocument()
    expect(screen.queryByTitle('Cancel')).not.toBeInTheDocument()
  })

  it('queued status: shows Start text button, Reset, Delete', () => {
    render(<CardActions {...base} status="queued" size="sm" />)
    expect(screen.getByText('Start')).toBeInTheDocument()
    expect(screen.getByTitle('Delete')).toBeInTheDocument()
  })

  it('active status: shows Cancel, Reset, Delete', () => {
    render(<CardActions {...base} status="fetching" size="sm" />)
    expect(screen.getByTitle('Cancel')).toBeInTheDocument()
    expect(screen.getByTitle('Reset')).toBeInTheDocument()
    expect(screen.getByTitle('Delete')).toBeInTheDocument()
    expect(screen.queryByText('Start')).not.toBeInTheDocument()
  })

  it('failed status: shows Retry, Copy error, Reset, Delete', () => {
    render(<CardActions {...base} status="failed" size="sm" error="Something broke" />)
    expect(screen.getByTitle('Retry')).toBeInTheDocument()
    expect(screen.getByTitle('Copy error')).toBeInTheDocument()
    expect(screen.getByTitle('Reset')).toBeInTheDocument()
    expect(screen.getByTitle('Delete')).toBeInTheDocument()
  })

  it('completed status: shows Process icon button, Delete', () => {
    render(<CardActions {...base} status="completed" size="sm" />)
    expect(screen.getByTitle('Process')).toBeInTheDocument()
    expect(screen.getByTitle('Delete')).toBeInTheDocument()
    expect(screen.queryByText('Start')).not.toBeInTheDocument()
  })
})

describe('CardActions — completed card variant (size=md)', () => {
  const base = {
    onDelete: vi.fn(),
    onProcess: vi.fn(),
    onReset: vi.fn(),
  }

  it('completed status: shows Process icon button, Delete', () => {
    render(<CardActions {...base} status="completed" size="md" />)
    expect(screen.getByTitle('Process')).toBeInTheDocument()
    expect(screen.getByTitle('Delete')).toBeInTheDocument()
  })

  it('only Delete when onProcess is missing', () => {
    render(<CardActions status="completed" size="md" onDelete={vi.fn()} />)
    expect(screen.queryByTitle('Process')).not.toBeInTheDocument()
    expect(screen.getByTitle('Delete')).toBeInTheDocument()
  })

  it('renders nothing when no callbacks provided', () => {
    const { container } = render(<CardActions status="completed" size="md" />)
    expect(container.firstChild).toBeNull()
  })

  it('stopPropagation prevents parent click', () => {
    const parentClick = vi.fn()
    render(
      <div onClick={parentClick}>
        <CardActions status="completed" size="md" onDelete={vi.fn()} onProcess={vi.fn()} />
      </div>
    )
    fireEvent.click(screen.getByTitle('Delete'))
    expect(parentClick).not.toHaveBeenCalled()
    fireEvent.click(screen.getByTitle('Process'))
    expect(parentClick).not.toHaveBeenCalled()
  })

  it('shows Workflow button when hasWorkflowLogs is true', () => {
    render(<CardActions {...base} status="completed" size="md" hasWorkflowLogs onViewWorkflow={vi.fn()} />)
    expect(screen.getByTitle('Workflow')).toBeInTheDocument()
  })
})
