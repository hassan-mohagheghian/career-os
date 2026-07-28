import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import CompanyCard from './CompanyCard'

const baseCompany = {
  id: 1,
  name: 'TechCorp',
  industry: 'Technology',
  city: 'Berlin',
  country: 'Germany',
  company_size: '500-1000',
  description: 'A leading tech company',
  website: 'https://techcorp.com',
  job_count: 5,
  scores: {
    company_fit_score: 82,
    company_success_score: 75,
    company_overall_score: 78,
    overall_grade: 'A',
  },
}

describe('CompanyCard', () => {
  it('renders company name', () => {
    render(<CompanyCard company={baseCompany} onClick={vi.fn()} />)
    expect(screen.getByText('TechCorp')).toBeInTheDocument()
  })

  it('renders industry', () => {
    render(<CompanyCard company={baseCompany} onClick={vi.fn()} />)
    expect(screen.getByText('Technology')).toBeInTheDocument()
  })

  it('renders location', () => {
    render(<CompanyCard company={baseCompany} onClick={vi.fn()} />)
    expect(screen.getByText('Berlin, Germany')).toBeInTheDocument()
  })

  it('renders company size', () => {
    render(<CompanyCard company={baseCompany} onClick={vi.fn()} />)
    expect(screen.getByText('500-1000')).toBeInTheDocument()
  })

  it('renders job count', () => {
    render(<CompanyCard company={baseCompany} onClick={vi.fn()} />)
    expect(screen.getByText('5')).toBeInTheDocument()
  })

  it('renders website link', () => {
    render(<CompanyCard company={baseCompany} onClick={vi.fn()} />)
    expect(screen.getByText('https://techcorp.com')).toBeInTheDocument()
  })

  it('renders description', () => {
    render(<CompanyCard company={baseCompany} onClick={vi.fn()} />)
    expect(screen.getByText('A leading tech company')).toBeInTheDocument()
  })

  it('renders overall grade', () => {
    render(<CompanyCard company={baseCompany} onClick={vi.fn()} />)
    expect(screen.getByText('A')).toBeInTheDocument()
  })

  it('calls onClick when card clicked', () => {
    const onClick = vi.fn()
    render(<CompanyCard company={baseCompany} onClick={onClick} />)
    fireEvent.click(screen.getByText('TechCorp'))
    expect(onClick).toHaveBeenCalled()
  })

  it('calls onDelete when delete button clicked', () => {
    const onDelete = vi.fn()
    render(<CompanyCard company={baseCompany} onClick={vi.fn()} onDelete={onDelete} />)
    fireEvent.click(screen.getByTitle('Delete'))
    expect(onDelete).toHaveBeenCalledWith(1)
  })

  it('calls onReprocess when reprocess button clicked', () => {
    const onReprocess = vi.fn()
    render(<CompanyCard company={baseCompany} onClick={vi.fn()} onReprocess={onReprocess} />)
    fireEvent.click(screen.getByTitle('Reprocess'))
    expect(onReprocess).toHaveBeenCalledWith(1)
  })

  it('renders default grade when no scores', () => {
    const noScores = { ...baseCompany, scores: {} }
    render(<CompanyCard company={noScores} onClick={vi.fn()} />)
    expect(screen.getByText('—')).toBeInTheDocument()
  })
})
