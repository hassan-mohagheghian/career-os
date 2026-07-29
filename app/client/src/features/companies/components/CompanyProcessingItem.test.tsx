import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import CompanyProcessingItem from './CompanyProcessingItem'

vi.mock('@/shared/ui/tooltip', () => ({
  TooltipProvider: ({ children }: any) => <>{children}</>,
  Tooltip: ({ children }: any) => <>{children}</>,
  TooltipTrigger: ({ children, ...props }: any) => <span {...props}>{children}</span>,
  TooltipContent: ({ children }: any) => <div>{children}</div>,
}))

describe('CompanyProcessingItem', () => {
  const base = { id: 1, company_name: 'TechCorp', status: 'pending' }

  it('renders company name', () => {
    render(<CompanyProcessingItem item={base} />)
    expect(screen.getByText('TechCorp')).toBeInTheDocument()
  })

  it('renders pending status', () => {
    render(<CompanyProcessingItem item={base} />)
    expect(screen.getByText('pending')).toBeInTheDocument()
  })

  it('renders processing status', () => {
    render(<CompanyProcessingItem item={{ ...base, status: 'processing' }} />)
    expect(screen.getByText('TechCorp')).toBeInTheDocument()
  })

  it('renders done status', () => {
    render(<CompanyProcessingItem item={{ ...base, status: 'done' }} />)
    expect(screen.getByText('done')).toBeInTheDocument()
  })

  it('renders failed status', () => {
    render(<CompanyProcessingItem item={{ ...base, status: 'failed' }} />)
    expect(screen.getByText('Failed')).toBeInTheDocument()
  })

  it('renders remove button', () => {
    const onDelete = vi.fn()
    render(<CompanyProcessingItem item={base} onDelete={onDelete} />)
    expect(screen.getByTitle('Delete')).toBeInTheDocument()
  })

  it('renders start button for pending items', () => {
    const onProcess = vi.fn()
    render(<CompanyProcessingItem item={base} onProcess={onProcess} />)
    expect(screen.getByText('Start')).toBeInTheDocument()
  })
})
