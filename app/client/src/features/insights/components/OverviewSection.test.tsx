import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import OverviewSection from './OverviewSection'

describe('OverviewSection', () => {
  const defaultProps = {
    data: null,
    refreshing: {},
    onRefresh: vi.fn(),
    status: {},
    localHistory: [],
    singleRunning: null,
    onCancel: vi.fn(),
  }

  it('renders Career Command Center header', () => {
    render(<OverviewSection {...defaultProps} />)
    expect(screen.getByText('Career Command Center')).toBeInTheDocument()
  })

  it('renders Refresh button', () => {
    render(<OverviewSection {...defaultProps} />)
    expect(screen.getByText('Refresh')).toBeInTheDocument()
  })

  it('calls onRefresh when refresh clicked', () => {
    const onRefresh = vi.fn()
    render(<OverviewSection {...defaultProps} onRefresh={onRefresh} />)
    screen.getByText('Refresh').click()
    expect(onRefresh).toHaveBeenCalled()
  })

  it('renders stat cards with zero values by default', () => {
    render(<OverviewSection {...defaultProps} />)
    expect(screen.getByText('Total Jobs')).toBeInTheDocument()
    expect(screen.getByText('High Match')).toBeInTheDocument()
    expect(screen.getByText('Apply Now')).toBeInTheDocument()
    expect(screen.getByText('Visa Friendly')).toBeInTheDocument()
    expect(screen.getByText('Target Companies')).toBeInTheDocument()
    expect(screen.getByText('Skill Match')).toBeInTheDocument()
  })

  it('renders Career Health Score card', () => {
    render(<OverviewSection {...defaultProps} />)
    expect(screen.getByText('Career Health Score')).toBeInTheDocument()
  })

  it('renders Recommended Next Actions card', () => {
    render(<OverviewSection {...defaultProps} />)
    expect(screen.getByText('Recommended Next Actions')).toBeInTheDocument()
  })

  it('renders "Generate intelligence to see recommended actions" when no actions', () => {
    render(<OverviewSection {...defaultProps} />)
    expect(screen.getByText('Generate intelligence to see recommended actions')).toBeInTheDocument()
  })

  it('renders action cards when data has nextActions', () => {
    const data = {
      overview: {
        position: { totalJobs: 10, highMatchJobs: 3 },
        careerHealthScore: { overall: 75, breakdown: {} },
        nextActions: [
          { action: 'Apply to 5 jobs', reason: 'High match rate', impact: 'high', priority: 1 },
        ],
      },
    }
    render(<OverviewSection {...defaultProps} data={data} />)
    expect(screen.getByText('Apply to 5 jobs')).toBeInTheDocument()
  })

  it('renders skill gaps when present', () => {
    const data = {
      overview: {
        position: { biggestSkillGaps: ['Rust', 'Go'] },
      },
    }
    render(<OverviewSection {...defaultProps} data={data} />)
    expect(screen.getByText('Biggest Skill Gaps')).toBeInTheDocument()
    expect(screen.getByText('Rust')).toBeInTheDocument()
    expect(screen.getByText('Go')).toBeInTheDocument()
  })

  it('renders generation history', () => {
    const history = [{ id: 'h1', source: 'overview', status: 'completed', created_at: '2026-07-20T10:00:00Z' }]
    render(<OverviewSection {...defaultProps} localHistory={history} />)
    expect(screen.getByText('Generation History')).toBeInTheDocument()
  })

  it('renders single running generation', () => {
    const singleRunning = { title: 'Generating...', source: 'overview', status: 'running' }
    render(<OverviewSection {...defaultProps} singleRunning={singleRunning} />)
    expect(screen.getByText('Generating...')).toBeInTheDocument()
  })

  it('renders breakdown bars', () => {
    const data = {
      overview: {
        careerHealthScore: {
          overall: 80,
          breakdown: { jobMarketFit: 70, companyFit: 60, visaProbability: 85, skillAlignment: 75, networkingStatus: 50 },
        },
      },
    }
    render(<OverviewSection {...defaultProps} data={data} />)
    expect(screen.getByText('Job Market Fit')).toBeInTheDocument()
    expect(screen.getByText('Company Fit')).toBeInTheDocument()
    expect(screen.getByText('Visa Probability')).toBeInTheDocument()
    expect(screen.getByText('Skill Alignment')).toBeInTheDocument()
    expect(screen.getByText('Networking Status')).toBeInTheDocument()
  })
})
