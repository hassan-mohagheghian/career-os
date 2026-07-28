import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import SkillsIntelDashboard from './SkillsIntelDashboard'

describe('SkillsIntelDashboard', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn(() =>
      Promise.resolve({ ok: true, json: () => Promise.resolve({}) })
    ))
  })

  const defaultProps = {
    refreshing: {},
    onRefresh: vi.fn(),
    status: {},
    onOpenDrawer: vi.fn(),
    localHistory: [],
    singleRunning: null,
    onCancel: vi.fn(),
  }

  it('renders Skills Intelligence header', async () => {
    render(<SkillsIntelDashboard {...defaultProps} />)
    expect(screen.getByText('Skills Intelligence')).toBeInTheDocument()
  })

  it('renders overview stat cards', async () => {
    render(<SkillsIntelDashboard {...defaultProps} />)
    expect(screen.getByText('Total Skills')).toBeInTheDocument()
    expect(screen.getByText('Strengths')).toBeInTheDocument()
    expect(screen.getByText('Skill Gaps')).toBeInTheDocument()
    expect(screen.getByText('High ROI')).toBeInTheDocument()
    expect(screen.getByText('Roadmaps')).toBeInTheDocument()
  })

  it('renders readiness gauge', async () => {
    render(<SkillsIntelDashboard {...defaultProps} />)
    expect(screen.getByText('Readiness')).toBeInTheDocument()
  })

  it('renders Category Breakdown', async () => {
    render(<SkillsIntelDashboard {...defaultProps} />)
    await waitFor(() => {
      expect(screen.getByText('Category Breakdown')).toBeInTheDocument()
    })
  })

  it('renders Skill Gap Matrix', async () => {
    render(<SkillsIntelDashboard {...defaultProps} />)
    await waitFor(() => {
      expect(screen.getByText('Skill Gap Matrix')).toBeInTheDocument()
    })
  })

  it('renders Recommendations section', async () => {
    render(<SkillsIntelDashboard {...defaultProps} />)
    await waitFor(() => {
      expect(screen.getByText('Recommendations')).toBeInTheDocument()
    })
  })

  it('renders Learning Roadmap', async () => {
    render(<SkillsIntelDashboard {...defaultProps} />)
    await waitFor(() => {
      expect(screen.getByText('Learning Roadmap')).toBeInTheDocument()
    })
  })

  it('renders category filter tabs', async () => {
    render(<SkillsIntelDashboard {...defaultProps} />)
    expect(screen.getByText('All Gaps')).toBeInTheDocument()
  })

  it('renders generation history', async () => {
    const history = [{ id: 'h1', source: 'skills_intel', status: 'completed', created_at: '2026-07-20T10:00:00Z' }]
    render(<SkillsIntelDashboard {...defaultProps} localHistory={history} />)
    await waitFor(() => {
      expect(screen.getByText('Generation History')).toBeInTheDocument()
    })
  })

  it('renders single running generation', async () => {
    const singleRunning = { title: 'Analyzing skills...', source: 'skills_intel', status: 'running' }
    render(<SkillsIntelDashboard {...defaultProps} singleRunning={singleRunning} />)
    await waitFor(() => {
      expect(screen.getByText('Analyzing skills...')).toBeInTheDocument()
    })
  })
})
