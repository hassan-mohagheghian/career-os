import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import ProcessingItem from './ProcessingItem'

vi.mock('@/shared/ui/tooltip', () => ({
  TooltipProvider: ({ children }: any) => <>{children}</>,
  Tooltip: ({ children }: any) => <>{children}</>,
  TooltipTrigger: ({ children, ...props }: any) => <span {...props}>{children}</span>,
  TooltipContent: ({ children }: any) => <div>{children}</div>,
}))

describe('ProcessingItem', () => {
  const base = { id: 1, job_num: 1, company: 'TechCorp', role: 'Engineer', status: 'pending' }

  it('renders company name', () => {
    render(<ProcessingItem item={base} />)
    expect(screen.getByText('TechCorp')).toBeInTheDocument()
  })

  it('renders job number', () => {
    render(<ProcessingItem item={base} />)
    expect(screen.getByText('#1')).toBeInTheDocument()
  })

  it('renders queued status', () => {
    render(<ProcessingItem item={base} />)
    expect(screen.getByText('0/7')).toBeInTheDocument()
  })

  it('renders processing status', () => {
    render(<ProcessingItem item={{ ...base, status: 'processing' }} />)
    expect(screen.getByText('TechCorp')).toBeInTheDocument()
  })

  it('renders done status', () => {
    render(<ProcessingItem item={{ ...base, status: 'done' }} />)
    expect(screen.getByText('TechCorp')).toBeInTheDocument()
  })

  it('renders failed status with error', () => {
    render(<ProcessingItem item={{ ...base, status: 'failed', error: 'Oops' }} />)
    expect(screen.getByText('Oops')).toBeInTheDocument()
  })

  it('renders web source badge', () => {
    render(<ProcessingItem item={{ ...base, source: 'web' }} />)
    expect(screen.getByText('W')).toBeInTheDocument()
  })

  it('renders rescore source badge', () => {
    render(<ProcessingItem item={{ ...base, source: 'rescore' }} />)
    expect(screen.getByText('R')).toBeInTheDocument()
  })

  it('renders remove button', () => {
    const onDelete = vi.fn()
    render(<ProcessingItem item={base} onDelete={onDelete} />)
    expect(screen.getByTitle('Delete')).toBeInTheDocument()
  })

  it('renders start button for queued items', () => {
    const onProcess = vi.fn()
    render(<ProcessingItem item={base} onProcess={onProcess} />)
    expect(screen.getByText('Start')).toBeInTheDocument()
  })

  it('renders version when present', () => {
    render(<ProcessingItem item={{ ...base, status: 'done', version: 3 }} />)
    expect(screen.getByText('v3')).toBeInTheDocument()
  })

  it('renders step progress', () => {
    render(<ProcessingItem item={{ ...base, status: 'processing', step_fetch: 1, step_validate: 1 }} />)
    expect(screen.getByText('2/7')).toBeInTheDocument()
  })
})
