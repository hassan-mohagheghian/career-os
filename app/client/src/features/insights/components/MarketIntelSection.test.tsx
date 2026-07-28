import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import MarketIntelSection from './MarketIntelSection'

describe('MarketIntelSection', () => {
  const defaultProps = {
    data: null,
    refreshing: {},
    onRefresh: vi.fn(),
    status: {},
    localHistory: [],
    singleRunning: null,
    onCancel: vi.fn(),
  }

  it('renders Market Intelligence header', () => {
    render(<MarketIntelSection {...defaultProps} />)
    expect(screen.getByText('Market Intelligence')).toBeInTheDocument()
  })

  it('renders Refresh button', () => {
    render(<MarketIntelSection {...defaultProps} />)
    expect(screen.getByText('Refresh')).toBeInTheDocument()
  })

  it('renders Cities card', () => {
    render(<MarketIntelSection {...defaultProps} />)
    expect(screen.getByText('Cities')).toBeInTheDocument()
  })

  it('renders countries when data provided', () => {
    const data = {
      market: {
        countries: [{ name: 'Germany', jobCount: 50, percentage: 40 }],
      },
    }
    render(<MarketIntelSection {...defaultProps} data={data} />)
    expect(screen.getByText('Countries')).toBeInTheDocument()
    expect(screen.getByText('Germany')).toBeInTheDocument()
  })

  it('renders remote opportunities when data provided', () => {
    const data = {
      market: {
        remoteOpportunities: { count: 25, percentage: 20, topCompanies: ['RemoteCo'] },
      },
    }
    render(<MarketIntelSection {...defaultProps} data={data} />)
    expect(screen.getByText('Remote')).toBeInTheDocument()
    expect(screen.getByText('25')).toBeInTheDocument()
  })

  it('renders visa friendliness', () => {
    const data = {
      market: {
        visaFriendliness: [{ country: 'Germany', rating: 'excellent' }],
      },
    }
    render(<MarketIntelSection {...defaultProps} data={data} />)
    expect(screen.getByText('Visa')).toBeInTheDocument()
    expect(screen.getByText('Germany')).toBeInTheDocument()
  })

  it('renders market insights', () => {
    const data = {
      market: {
        insights: [{ observation: 'Berlin is booming', action: 'Focus on Berlin' }],
      },
    }
    render(<MarketIntelSection {...defaultProps} data={data} />)
    expect(screen.getByText('Insights')).toBeInTheDocument()
    expect(screen.getByText('Berlin is booming')).toBeInTheDocument()
  })

  it('renders cities with data', () => {
    const data = {
      market: {
        cities: [{ name: 'Berlin', opportunityLevel: 'high', jobCount: 30, topCompanies: ['Co1', 'Co2'], insight: 'Growing market' }],
      },
    }
    render(<MarketIntelSection {...defaultProps} data={data} />)
    expect(screen.getByText('Berlin')).toBeInTheDocument()
    expect(screen.getByText('30 jobs')).toBeInTheDocument()
  })

  it('renders generation history', () => {
    const history = [{ id: 'h1', source: 'market', status: 'completed', created_at: '2026-07-20T10:00:00Z' }]
    render(<MarketIntelSection {...defaultProps} localHistory={history} />)
    expect(screen.getByText('Generation History')).toBeInTheDocument()
  })
})
