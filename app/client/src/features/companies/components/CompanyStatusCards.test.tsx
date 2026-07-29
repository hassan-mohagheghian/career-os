import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import CompanyPendingCard from './CompanyPendingCard'
import CompanyQueuedCard from './CompanyQueuedCard'
import CompanyProcessingCard from './CompanyProcessingCard'
import CompanyFailedCard from './CompanyFailedCard'
import CompanyCompletedCard from './CompanyCompletedCard'

vi.mock('@/shared/ui/tooltip', () => ({
  TooltipProvider: ({ children }: any) => <>{children}</>,
  Tooltip: ({ children }: any) => <>{children}</>,
  TooltipTrigger: ({ children, ...props }: any) => <span {...props}>{children}</span>,
  TooltipContent: ({ children }: any) => <div>{children}</div>,
}))

const baseItem = {
  id: 1, company_name: 'TechCorp',
  step_fetch: 0, step_extract: 0, step_analyze: 0, step_save: 0, step_done: 0,
}

describe('CompanyPendingCard', () => {
  it('renders company name and pending status', () => {
    render(<CompanyPendingCard item={{ ...baseItem, status: 'pending' }} />)
    expect(screen.getByText('TechCorp')).toBeInTheDocument()
    expect(screen.getByText('pending')).toBeInTheDocument()
  })

  it('renders Start button when onProcess is provided', () => {
    render(<CompanyPendingCard item={{ ...baseItem, status: 'pending' }} onProcess={vi.fn()} />)
    expect(screen.getByText('Start')).toBeInTheDocument()
  })
})

describe('CompanyQueuedCard', () => {
  it('renders queued status', () => {
    render(<CompanyQueuedCard item={{ ...baseItem, status: 'queued' }} />)
    expect(screen.getByText('queued')).toBeInTheDocument()
  })
})

describe('CompanyProcessingCard', () => {
  it('renders processing status text', () => {
    render(<CompanyProcessingCard item={{ ...baseItem, status: 'processing' }} />)
    expect(screen.getByText('Fetching...')).toBeInTheDocument()
  })
})

describe('CompanyFailedCard', () => {
  it('renders failed status with error', () => {
    render(<CompanyFailedCard item={{ ...baseItem, status: 'failed', error: 'API error' }} />)
    expect(screen.getByText('API error')).toBeInTheDocument()
  })

  it('renders Retry button when onProcess is provided', () => {
    render(<CompanyFailedCard item={{ ...baseItem, status: 'failed' }} onProcess={vi.fn()} />)
    expect(screen.getByTitle('Retry')).toBeInTheDocument()
  })
})

describe('CompanyCompletedCard', () => {
  it('renders done status', () => {
    render(<CompanyCompletedCard item={{ ...baseItem, status: 'done', step_done: 1 }} />)
    expect(screen.getByText('done')).toBeInTheDocument()
  })
})
