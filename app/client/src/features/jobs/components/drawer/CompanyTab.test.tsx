import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import CompanyTab from './CompanyTab'

const mockJob = { num: 1, role: 'Dev', linked_company: null }
const mockCompanies = []

describe('CompanyTab', () => {
  it('renders no company linked message', () => {
    render(<CompanyTab job={mockJob} companies={mockCompanies} />)
    expect(screen.getByText('No company linked')).toBeInTheDocument()
  })

  it('renders Link Company button', () => {
    render(<CompanyTab job={mockJob} companies={mockCompanies} />)
    expect(screen.getByText('Link Company')).toBeInTheDocument()
  })

  it('renders linked company when present', () => {
    const jobWithCompany = {
      num: 1, linked_company: { id: 1, name: 'TechCorp', industry: 'Technology', city: 'Berlin', country: 'Germany' }
    }
    render(<CompanyTab job={jobWithCompany} companies={[]} />)
    expect(screen.getByText('TechCorp')).toBeInTheDocument()
  })

  it('renders company intelligence scores when available', () => {
    const jobWithIntel = {
      num: 1,
      linked_company: {
        id: 1, name: 'TechCorp',
        intelligence: {
          scores: { overall_grade: 'A', company_fit_score: 85, company_success_score: 75, company_overall_score: 80 },
          overview: { description: 'Great company' },
        }
      }
    }
    render(<CompanyTab job={jobWithIntel} companies={[]} />)
    expect(screen.getByText('A')).toBeInTheDocument()
  })

  it('renders Change Company when linked', () => {
    const jobWithCompany = {
      num: 1, linked_company: { id: 1, name: 'TechCorp' }
    }
    render(<CompanyTab job={jobWithCompany} companies={[]} />)
    expect(screen.getByText('Change Company')).toBeInTheDocument()
  })

  it('renders Disconnect button when linked', () => {
    const jobWithCompany = {
      num: 1, linked_company: { id: 1, name: 'TechCorp' }
    }
    render(<CompanyTab job={jobWithCompany} companies={[]} />)
    expect(screen.getByText('Disconnect')).toBeInTheDocument()
  })
})
