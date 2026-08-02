import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import CompanyDrawer from './CompanyDrawer'

const mockCompany = {
  id: 1,
  name: 'TechCorp',
  industry: 'Technology',
  city: 'Berlin',
  country: 'Germany',
  company_size: '500',
  company_type: 'PRODUCT_COMPANY',
  website: 'https://techcorp.com',
  job_count: 5,
  description: 'A leading tech company',
  scores: {
    company_fit_score: 82,
    company_success_score: 75,
    company_overall_score: 78,
    overall_grade: 'A',
    fit_explanation: 'Good match',
    success_explanation: 'High chance',
    fit_positive_factors: ['Strong tech stack'],
    fit_negative_factors: ['Remote only'],
    success_positive_factors: ['Active hiring'],
    success_negative_factors: [],
  },
  intelligence: {
    overview: { founded: '2010', headquarters: 'Berlin', size: '500', products: 'Cloud platform', countries: ['Germany', 'USA'] },
    culture_analysis: { engineering_org: 'Flat', team_structure: 'Squads', methodology: 'Agile' },
    technology_analysis: { backend: ['Python', 'Go'], frontend: ['React'], infrastructure: ['AWS'], tech_match_score: 85, matches_profile: 'Yes' },
    benefits_analysis: { remote_policy: 'Hybrid', vacation: '30 days', benefits: ['Health', 'Gym'] },
    visa_analysis: { relocation_recommendation: 'HIGH', sponsorship_history: 'Yes', international_hiring: true, positive_signals: ['Sponsors visa'], risks: [] },
    career_analysis: { senior_opportunities: 'Yes', growth_potential: 'High' },
    recommendation: {},
  },
}

describe('CompanyDrawer', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn(() =>
      Promise.resolve({ ok: true, json: () => Promise.resolve([]) })
    ))
  })

  it('returns null when company is null', () => {
    const { container } = render(
      <CompanyDrawer company={null} onClose={vi.fn()} onDelete={vi.fn()} onReprocess={vi.fn()} />
    )
    expect(container.innerHTML).toBe('')
  })

  it('renders company name when provided', () => {
    render(
      <CompanyDrawer company={mockCompany} onClose={vi.fn()} onDelete={vi.fn()} onReprocess={vi.fn()} />
    )
    expect(screen.getByText('TechCorp')).toBeInTheDocument()
  })

  it('renders overall grade', () => {
    render(
      <CompanyDrawer company={mockCompany} onClose={vi.fn()} onDelete={vi.fn()} onReprocess={vi.fn()} />
    )
    expect(screen.getByText('A')).toBeInTheDocument()
  })

  it('renders industry', () => {
    render(
      <CompanyDrawer company={mockCompany} onClose={vi.fn()} onDelete={vi.fn()} onReprocess={vi.fn()} />
    )
    expect(screen.getByText('Technology')).toBeInTheDocument()
  })

  it('renders tabs', () => {
    render(
      <CompanyDrawer company={mockCompany} onClose={vi.fn()} onDelete={vi.fn()} onReprocess={vi.fn()} />
    )
    expect(screen.getByText('Original Notes')).toBeInTheDocument()
    expect(screen.getByText('Intelligence')).toBeInTheDocument()
    expect(screen.getByText('Scores')).toBeInTheDocument()
    expect(screen.getByText(/Jobs/)).toBeInTheDocument()
  })

  it('renders delete button', () => {
    render(
      <CompanyDrawer company={mockCompany} onClose={vi.fn()} onDelete={vi.fn()} onReprocess={vi.fn()} />
    )
    expect(screen.getByText('Delete')).toBeInTheDocument()
  })

  it('renders reprocess button', () => {
    render(
      <CompanyDrawer company={mockCompany} onClose={vi.fn()} onDelete={vi.fn()} onReprocess={vi.fn()} />
    )
    expect(screen.getByText('Reprocess')).toBeInTheDocument()
  })

  it('renders website link', () => {
    render(
      <CompanyDrawer company={mockCompany} onClose={vi.fn()} onDelete={vi.fn()} onReprocess={vi.fn()} />
    )
    expect(screen.getByText('Website')).toBeInTheDocument()
  })

  it('renders location badge', () => {
    render(
      <CompanyDrawer company={mockCompany} onClose={vi.fn()} onDelete={vi.fn()} onReprocess={vi.fn()} />
    )
    expect(screen.getByText('Berlin, Germany')).toBeInTheDocument()
  })

  it('renders company size badge', () => {
    render(
      <CompanyDrawer company={mockCompany} onClose={vi.fn()} onDelete={vi.fn()} onReprocess={vi.fn()} />
    )
    expect(screen.getByText('500')).toBeInTheDocument()
  })

  it('renders fit score', () => {
    render(
      <CompanyDrawer company={mockCompany} onClose={vi.fn()} onDelete={vi.fn()} onReprocess={vi.fn()} />
    )
    expect(screen.getByText('82')).toBeInTheDocument()
  })

  it('renders success score', () => {
    render(
      <CompanyDrawer company={mockCompany} onClose={vi.fn()} onDelete={vi.fn()} onReprocess={vi.fn()} />
    )
    expect(screen.getByText('75')).toBeInTheDocument()
  })
})
