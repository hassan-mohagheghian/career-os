import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import OpportunitiesSection from './OpportunitiesSection'

describe('OpportunitiesSection', () => {
  const defaultProps = {
    data: null,
    refreshing: {},
    onRefresh: vi.fn(),
    onOpenDrawer: vi.fn(),
    status: {},
    localHistory: [],
    singleRunning: null,
    onCancel: vi.fn(),
  }

  it('renders Opportunities Intelligence header', () => {
    render(<OpportunitiesSection {...defaultProps} />)
    expect(screen.getByText('Opportunities Intelligence')).toBeInTheDocument()
  })

  it('renders Refresh button', () => {
    render(<OpportunitiesSection {...defaultProps} />)
    expect(screen.getByText('Refresh')).toBeInTheDocument()
  })

  it('renders funnel columns', () => {
    render(<OpportunitiesSection {...defaultProps} />)
    expect(screen.getByText('Apply Now')).toBeInTheDocument()
    expect(screen.getByText('High Potential')).toBeInTheDocument()
    expect(screen.getByText('Consider')).toBeInTheDocument()
    expect(screen.getByText('Low Priority')).toBeInTheDocument()
  })

  it('renders "No jobs" in empty funnel columns', () => {
    render(<OpportunitiesSection {...defaultProps} />)
    const noJobs = screen.getAllByText('No jobs')
    expect(noJobs.length).toBe(4)
  })

  it('renders jobs in funnel when data provided', () => {
    const data = {
      opportunities: {
        funnel: {
          applyNow: [{ num: 1, company: 'TechCorp', role: 'Engineer', location: 'Berlin', overallScore: 90, visaProbability: 'BEST' }],
          highPotential: [],
          consider: [],
          lowPriority: [],
        },
      },
    }
    render(<OpportunitiesSection {...defaultProps} data={data} />)
    expect(screen.getByText('TechCorp')).toBeInTheDocument()
    expect(screen.getByText('90')).toBeInTheDocument()
  })

  it('renders insights when provided', () => {
    const data = {
      opportunities: {
        insights: [{ observation: 'Market is hot for React devs', evidence: 'High demand', action: 'Apply now' }],
      },
    }
    render(<OpportunitiesSection {...defaultProps} data={data} />)
    expect(screen.getByText('Insights')).toBeInTheDocument()
    expect(screen.getByText('Market is hot for React devs')).toBeInTheDocument()
  })

  it('renders best jobs this week', () => {
    const data = {
      opportunities: {
        bestJobsThisWeek: [{ num: 1, company: 'GoodCo', role: 'Dev', location: 'Remote', overallScore: 85 }],
      },
    }
    render(<OpportunitiesSection {...defaultProps} data={data} />)
    expect(screen.getByText('Best Jobs This Week')).toBeInTheDocument()
    expect(screen.getByText('GoodCo')).toBeInTheDocument()
  })

  it('renders multi-role companies', () => {
    const data = {
      opportunities: {
        multiRoleCompanies: [{ company: 'BigTech', count: 3, roles: ['Frontend', 'Backend', 'Full Stack'] }],
      },
    }
    render(<OpportunitiesSection {...defaultProps} data={data} />)
    expect(screen.getByText('Multi-Role Companies')).toBeInTheDocument()
    expect(screen.getByText('BigTech')).toBeInTheDocument()
  })

  it('renders missed opportunities', () => {
    const data = {
      opportunities: {
        missedOpportunities: [{ num: 1, company: 'MissedCo', role: 'Dev', location: 'NYC', overallScore: 70 }],
      },
    }
    render(<OpportunitiesSection {...defaultProps} data={data} />)
    expect(screen.getByText('Missed Opportunities')).toBeInTheDocument()
  })

  it('renders generation history', () => {
    const history = [{ id: 'h1', source: 'opportunities', status: 'completed', created_at: '2026-07-20T10:00:00Z' }]
    render(<OpportunitiesSection {...defaultProps} localHistory={history} />)
    expect(screen.getByText('Generation History')).toBeInTheDocument()
  })

  it('renders single running generation', () => {
    const singleRunning = { title: 'Analyzing...', source: 'opportunities', status: 'running' }
    render(<OpportunitiesSection {...defaultProps} singleRunning={singleRunning} />)
    expect(screen.getByText('Analyzing...')).toBeInTheDocument()
  })
})
