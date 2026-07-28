import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import DetailsTab from './DetailsTab'

const mockJob = {
  num: 1,
  role: 'Senior Engineer',
  company_name: 'TechCorp',
  location: 'Berlin',
  structured_description: JSON.stringify({
    requirements: ['5+ years experience', 'React expertise'],
    responsibilities: ['Build microservices'],
    nice_to_have: ['TypeScript'],
  }),
}

describe('DetailsTab', () => {
  it('renders Application Tracking header', () => {
    render(<DetailsTab job={mockJob} onUpdateJob={vi.fn()} />)
    expect(screen.getByText('Application Tracking')).toBeInTheDocument()
  })

  it('renders Applied label', () => {
    render(<DetailsTab job={mockJob} onUpdateJob={vi.fn()} />)
    expect(screen.getByText('Applied:')).toBeInTheDocument()
  })

  it('renders requirements from structured_description', () => {
    render(<DetailsTab job={mockJob} onUpdateJob={vi.fn()} />)
    expect(screen.getByText('5+ years experience')).toBeInTheDocument()
    expect(screen.getByText('React expertise')).toBeInTheDocument()
  })

  it('renders responsibilities from structured_description', () => {
    render(<DetailsTab job={mockJob} onUpdateJob={vi.fn()} />)
    expect(screen.getByText('Build microservices')).toBeInTheDocument()
  })

  it('renders nice_to_have from structured_description', () => {
    render(<DetailsTab job={mockJob} onUpdateJob={vi.fn()} />)
    expect(screen.getByText('TypeScript')).toBeInTheDocument()
  })

  it('handles missing structured_description', () => {
    const noSd = { num: 1, role: 'Dev' }
    render(<DetailsTab job={noSd} onUpdateJob={vi.fn()} />)
    expect(screen.getByText('Application Tracking')).toBeInTheDocument()
  })

  it('handles invalid JSON in structured_description', () => {
    const badSd = { num: 1, structured_description: '{bad json' }
    render(<DetailsTab job={badSd} onUpdateJob={vi.fn()} />)
    expect(screen.getByText('Application Tracking')).toBeInTheDocument()
  })
})
