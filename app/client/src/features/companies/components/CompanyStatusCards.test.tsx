import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import CompanyCreatedCard from './CompanyCreatedCard'
import CompanyPendingCard from './CompanyPendingCard'
import CompanyQueuedCard from './CompanyQueuedCard'
import CompanyProcessingCard from './CompanyProcessingCard'
import CompanyFailedCard from './CompanyFailedCard'
import CompanyProcessedCard from './CompanyProcessedCard'

vi.mock('@/shared/ui/tooltip', () => ({
  TooltipProvider: ({ children }: any) => <>{children}</>,
  Tooltip: ({ children }: any) => <>{children}</>,
  TooltipTrigger: ({ children, asChild, ...props }: any) => <span {...props}>{children}</span>,
  TooltipContent: ({ children }: any) => <div>{children}</div>,
}))

const baseItem = {
  id: 1, company_name: 'TechCorp',
  step_fetch: 0, step_extract: 0, step_analyze: 0, step_save: 0, step_done: 0,
}

describe('CompanyCreatedCard', () => {
  it('renders company name and created status', () => {
    render(<CompanyCreatedCard item={{ ...baseItem, status: 'created' }} />)
    expect(screen.getByText('TechCorp')).toBeInTheDocument()
    expect(screen.getByText('created')).toBeInTheDocument()
  })
})

describe('CompanyPendingCard', () => {
  it('renders company name and pending status', () => {
    render(<CompanyPendingCard item={{ ...baseItem, status: 'pending' }} />)
    expect(screen.getByText('TechCorp')).toBeInTheDocument()
    expect(screen.getByText('pending')).toBeInTheDocument()
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
    expect(screen.getByText('Processing...')).toBeInTheDocument()
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

describe('CompanyProcessedCard', () => {
  it('renders processed status', () => {
    render(<CompanyProcessedCard item={{ ...baseItem, status: 'processed', step_done: 1 }} />)
    expect(screen.getByText('processed')).toBeInTheDocument()
  })
})
