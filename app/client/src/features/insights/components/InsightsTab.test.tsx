import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import InsightsTab from './InsightsTab'

vi.mock('@/shared/hooks', () => ({
  useLocalHistory: () => ({ items: [], singleRunning: null }),
}))

describe('InsightsTab', () => {
  const defaultProps = {
    data: null,
    status: {},
    progress: { running: false },
    activeTab: 'overview',
    setActiveTab: vi.fn(),
    refreshing: {},
    error: null,
    onRefreshAll: vi.fn(),
    onRefreshSection: vi.fn(),
    onOpenDrawer: vi.fn(),
    onOpenCompany: vi.fn(),
    onAddCompany: vi.fn(),
    onCancel: vi.fn(),
  }

  it('renders Insights header', () => {
    render(<InsightsTab {...defaultProps} />)
    expect(screen.getByText('Insights')).toBeInTheDocument()
  })

  it('renders tab triggers', () => {
    render(<InsightsTab {...defaultProps} />)
    expect(screen.getByText('Overview')).toBeInTheDocument()
    expect(screen.getByText('Skills')).toBeInTheDocument()
    expect(screen.getByText('Opportunities')).toBeInTheDocument()
    expect(screen.getByText('Companies')).toBeInTheDocument()
    expect(screen.getByText('Market')).toBeInTheDocument()
    expect(screen.getByText('Networking')).toBeInTheDocument()
  })

  it('renders Generate All button when not running', () => {
    render(<InsightsTab {...defaultProps} />)
    expect(screen.getByText('Generate All')).toBeInTheDocument()
  })

  it('renders empty state when no data', () => {
    render(<InsightsTab {...defaultProps} />)
    expect(screen.getByText('No insights yet')).toBeInTheDocument()
  })

  it('renders Generate Intelligence button in empty state', () => {
    render(<InsightsTab {...defaultProps} />)
    expect(screen.getByText('Generate Intelligence')).toBeInTheDocument()
  })

  it('renders Generating when running', () => {
    render(<InsightsTab {...defaultProps} progress={{ running: true }} />)
    expect(screen.getByText('Generating...')).toBeInTheDocument()
  })

  it('renders sub-sections when data is provided', () => {
    const data = { overview: { position: { totalJobs: 10 } } }
    render(<InsightsTab {...defaultProps} data={data} activeTab="overview" />)
    expect(screen.getByText('Career Command Center')).toBeInTheDocument()
  })
})
