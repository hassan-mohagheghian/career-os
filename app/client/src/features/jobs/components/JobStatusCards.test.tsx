import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import JobPendingCard from './JobPendingCard'
import JobQueuedCard from './JobQueuedCard'
import JobProcessingCard from './JobProcessingCard'
import JobFailedCard from './JobFailedCard'
import JobCompletedCard from './JobCompletedCard'

vi.mock('@/shared/ui/tooltip', () => ({
  TooltipProvider: ({ children }: any) => <>{children}</>,
  Tooltip: ({ children }: any) => <>{children}</>,
  TooltipTrigger: ({ children, ...props }: any) => <span {...props}>{children}</span>,
  TooltipContent: ({ children }: any) => <div>{children}</div>,
}))

const baseItem = {
  id: 1, job_num: 1, company: 'TechCorp', source: 'web',
  step_fetch: 0, step_validate: 0, step_extract_raw: 0,
  step_extract_struct: 0, step_summary: 0, step_analyze: 0, step_done: 0,
}

describe('JobPendingCard', () => {
  it('renders company name and created status', () => {
    render(<JobPendingCard item={{ ...baseItem, status: 'created' }} />)
    expect(screen.getByText('TechCorp')).toBeInTheDocument()
    expect(screen.getByText('created')).toBeInTheDocument()
  })

  it('renders Start process button when onProcess is provided', () => {
    render(<JobPendingCard item={{ ...baseItem, status: 'created' }} onProcess={vi.fn()} />)
    expect(screen.getByText('Start')).toBeInTheDocument()
  })
})

describe('JobQueuedCard', () => {
  it('renders queued status text', () => {
    render(<JobQueuedCard item={{ ...baseItem, status: 'queued' }} />)
    expect(screen.getByText('queued')).toBeInTheDocument()
  })

  it('renders Start button', () => {
    render(<JobQueuedCard item={{ ...baseItem, status: 'queued' }} onProcess={vi.fn()} />)
    expect(screen.getByText('Start')).toBeInTheDocument()
  })
})

describe('JobProcessingCard', () => {
  it('renders active status label', () => {
    render(<JobProcessingCard item={{ ...baseItem, status: 'fetching', current_node: 'fetch' }} />)
    expect(screen.getByText('Fetching...')).toBeInTheDocument()
  })

  it('renders Cancel button when onCancel is provided', () => {
    render(<JobProcessingCard item={{ ...baseItem, status: 'fetching' }} onCancel={vi.fn()} />)
    expect(screen.getByTitle('Cancel')).toBeInTheDocument()
  })
})

describe('JobFailedCard', () => {
  it('renders failed status with error', () => {
    render(<JobFailedCard item={{ ...baseItem, status: 'failed', error: 'Timeout' }} />)
    expect(screen.getByText('Timeout')).toBeInTheDocument()
  })

  it('renders Retry button when onProcess is provided', () => {
    render(<JobFailedCard item={{ ...baseItem, status: 'failed' }} onProcess={vi.fn()} />)
    expect(screen.getByTitle('Retry')).toBeInTheDocument()
  })
})

describe('JobCompletedCard', () => {
  it('renders completed status', () => {
    render(<JobCompletedCard item={{ ...baseItem, status: 'completed', step_done: 1 }} />)
    expect(screen.getByText('completed')).toBeInTheDocument()
  })

  it('renders Process button when onProcess is provided', () => {
    render(<JobCompletedCard item={{ ...baseItem, status: 'completed' }} onProcess={vi.fn()} />)
    expect(screen.getByTitle('Process')).toBeInTheDocument()
  })
})
