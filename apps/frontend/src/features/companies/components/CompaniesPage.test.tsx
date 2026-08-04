import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import CompaniesPage from './CompaniesPage'

const mockCompanies = [
  {
    id: 1, name: 'TechCorp', industry: 'Technology', city: 'Berlin', country: 'Germany',
    company_size: '500', description: 'Tech company', website: 'https://techcorp.com',
    job_count: 5, scores: { overall_grade: 'A', company_fit_score: 80, company_success_score: 75, company_overall_score: 78 },
    created_at: '2026-07-01T00:00:00Z',
  },
]

describe('CompaniesPage', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn(() =>
      Promise.resolve({ ok: true, json: () => Promise.resolve(mockCompanies) })
    ))
  })

  it('renders Add Company header', () => {
    render(<CompaniesPage companies={[]} pending={[]} onRefresh={vi.fn()} onOpenCompany={vi.fn()} />)
    expect(screen.getByText('Add Company')).toBeInTheDocument()
  })

  it('renders Companies header', () => {
    render(<CompaniesPage companies={[]} pending={[]} onRefresh={vi.fn()} onOpenCompany={vi.fn()} />)
    expect(screen.getByText('Companies')).toBeInTheDocument()
  })

  it('renders empty state when no companies', () => {
    render(<CompaniesPage companies={[]} pending={[]} onRefresh={vi.fn()} onOpenCompany={vi.fn()} />)
    expect(screen.getByText('No companies yet')).toBeInTheDocument()
  })

  it('renders company cards', () => {
    render(<CompaniesPage companies={mockCompanies} pending={[]} onRefresh={vi.fn()} onOpenCompany={vi.fn()} />)
    expect(screen.getByText('TechCorp')).toBeInTheDocument()
  })

  it('renders add company form', () => {
    render(<CompaniesPage companies={[]} pending={[]} onRefresh={vi.fn()} onOpenCompany={vi.fn()} />)
    expect(screen.getByText('Add Company')).toBeInTheDocument()
  })

  it('renders sort controls', () => {
    render(<CompaniesPage companies={mockCompanies} pending={[]} onRefresh={vi.fn()} onOpenCompany={vi.fn()} />)
    expect(screen.getByText('Newest')).toBeInTheDocument()
  })

  it('renders search input', () => {
    render(<CompaniesPage companies={mockCompanies} pending={[]} onRefresh={vi.fn()} onOpenCompany={vi.fn()} />)
    expect(screen.getByPlaceholderText('Search by name, industry, city...')).toBeInTheDocument()
  })

  it('filters companies by search', () => {
    render(<CompaniesPage companies={mockCompanies} pending={[]} onRefresh={vi.fn()} onOpenCompany={vi.fn()} />)
    fireEvent.change(screen.getByPlaceholderText('Search by name, industry, city...'), { target: { value: 'Tech' } })
    expect(screen.getByText('TechCorp')).toBeInTheDocument()
  })

  it('shows "No companies match" for non-matching search', () => {
    render(<CompaniesPage companies={mockCompanies} pending={[]} onRefresh={vi.fn()} onOpenCompany={vi.fn()} />)
    fireEvent.change(screen.getByPlaceholderText('Search by name, industry, city...'), { target: { value: 'Nonexistent' } })
    expect(screen.getByText('No companies match your search')).toBeInTheDocument()
  })

  it('sorts companies with NULL scores last regardless of direction', async () => {
    const companies = [
      {
        id: 1, name: 'Alpha', industry: 'Technology', city: 'Berlin', country: 'Germany',
        company_size: '500', description: '', website: '', job_count: 0,
        scores: { visa_score: 50, priority: 'A' },
        created_at: '2026-07-01T00:00:00Z',
      },
      {
        id: 2, name: 'Beta', industry: 'Technology', city: 'Berlin', country: 'Germany',
        company_size: '500', description: '', website: '', job_count: 0,
        scores: { visa_score: null, priority: 'A' },
        created_at: '2026-07-01T00:00:00Z',
      },
      {
        id: 3, name: 'Gamma', industry: 'Technology', city: 'Berlin', country: 'Germany',
        company_size: '500', description: '', website: '', job_count: 0,
        scores: { visa_score: 90, priority: 'A' },
        created_at: '2026-07-01T00:00:00Z',
      },
    ]
    const { container } = render(
      <CompaniesPage companies={companies} pending={[]} onRefresh={vi.fn()} onOpenCompany={vi.fn()} />
    )

    const namesInOrder = () =>
      Array.from(container.querySelectorAll('span.truncate')).map(el => el.textContent)

    fireEvent.click(screen.getAllByRole('combobox')[0])
    fireEvent.click(await screen.findByRole('option', { name: 'Visa Score' }))

    expect(namesInOrder()).toEqual(['Gamma', 'Alpha', 'Beta'])

    fireEvent.click(screen.getByText('↓'))

    expect(namesInOrder()).toEqual(['Alpha', 'Gamma', 'Beta'])
  })
})
