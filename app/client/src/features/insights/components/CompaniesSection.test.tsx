import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import CompaniesSection from './CompaniesSection'

vi.mock('@/shared/components/GenerationProgressCard', () => ({
  default: ({ title }: any) => <div data-testid="gen-progress">{title}</div>,
  STEP_CONFIGS: { insights: { steps: [] } },
}))

describe('CompaniesSection', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn(() =>
      Promise.resolve({ ok: true, json: () => Promise.resolve([]) })
    ))
  })

  const defaultProps = {
    data: null,
    refreshing: {},
    onRefresh: vi.fn(),
    onOpenCompany: vi.fn(),
    onAddCompany: vi.fn(),
    status: {},
    localHistory: [],
    singleRunning: null,
    onCancel: vi.fn(),
  }

  it('renders Company Intelligence header', async () => {
    render(<CompaniesSection {...defaultProps} />)
    expect(screen.getByText('Company Intelligence')).toBeInTheDocument()
  })

  it('renders Refresh button', async () => {
    render(<CompaniesSection {...defaultProps} />)
    expect(screen.getByText('Refresh')).toBeInTheDocument()
  })

  it('renders empty state for product companies', async () => {
    render(<CompaniesSection {...defaultProps} />)
    await waitFor(() => {
      expect(screen.getByText('No product companies analyzed')).toBeInTheDocument()
    })
  })

  it('renders empty state for recruiting companies', async () => {
    render(<CompaniesSection {...defaultProps} />)
    await waitFor(() => {
      expect(screen.getByText('No recruiting companies analyzed')).toBeInTheDocument()
    })
  })

  it('renders product companies when data provided', async () => {
    const data = {
      companies: {
        productCompanies: [{ company: 'TechCorp', visaStrength: 'BEST', fitScore: 85, engineeringCulture: 'Agile', technologyAlignment: 'React' }],
        recruitingCompanies: [],
      },
    }
    render(<CompaniesSection {...defaultProps} data={data} />)
    await waitFor(() => {
      expect(screen.getByText('TechCorp')).toBeInTheDocument()
    })
    expect(screen.getByText('Product Companies')).toBeInTheDocument()
  })

  it('renders recruiting companies', async () => {
    const data = {
      companies: {
        productCompanies: [],
        recruitingCompanies: [{ company: 'RecruitCo', relevantJobs: 5, internationalHiring: 'Yes' }],
      },
    }
    render(<CompaniesSection {...defaultProps} data={data} />)
    await waitFor(() => {
      expect(screen.getByText('RecruitCo')).toBeInTheDocument()
    })
    expect(screen.getByText('Recruiting / Staffing')).toBeInTheDocument()
  })

  it('renders top targets', async () => {
    const data = {
      companies: {
        topTargets: [{ rank: 1, company: 'TopCo', fit: 90, visa: 'BEST', reason: 'Great match' }],
        productCompanies: [],
        recruitingCompanies: [],
      },
    }
    render(<CompaniesSection {...defaultProps} data={data} />)
    await waitFor(() => {
      expect(screen.getByText('Top Targets')).toBeInTheDocument()
    })
    expect(screen.getByText('TopCo')).toBeInTheDocument()
  })

  it('renders generation history', async () => {
    const history = [{ id: 'h1', source: 'companies', status: 'completed', created_at: '2026-07-20T10:00:00Z' }]
    render(<CompaniesSection {...defaultProps} localHistory={history} />)
    await waitFor(() => {
      expect(screen.getByText('Generation History')).toBeInTheDocument()
    })
  })

  it('renders single running generation', async () => {
    const singleRunning = { title: 'Analyzing companies...', source: 'companies', status: 'running' }
    render(<CompaniesSection {...defaultProps} singleRunning={singleRunning} />)
    await waitFor(() => {
      expect(screen.getByText('Analyzing companies...')).toBeInTheDocument()
    })
  })
})
