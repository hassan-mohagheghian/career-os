import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import NetworkingIntelSection from './NetworkingIntelSection'

describe('NetworkingIntelSection', () => {
  const defaultProps = {
    data: null,
    refreshing: {},
    onRefresh: vi.fn(),
    status: {},
    localHistory: [],
    singleRunning: null,
    onCancel: vi.fn(),
  }

  it('renders Networking Intelligence header', () => {
    render(<NetworkingIntelSection {...defaultProps} />)
    expect(screen.getByText('Networking Intelligence')).toBeInTheDocument()
  })

  it('renders Refresh button', () => {
    render(<NetworkingIntelSection {...defaultProps} />)
    expect(screen.getByText('Refresh')).toBeInTheDocument()
  })

  it('renders Networking Targets card', () => {
    render(<NetworkingIntelSection {...defaultProps} />)
    expect(screen.getByText('Networking Targets')).toBeInTheDocument()
  })

  it('renders "No networking targets identified yet" when empty', () => {
    render(<NetworkingIntelSection {...defaultProps} />)
    expect(screen.getByText('No networking targets identified yet')).toBeInTheDocument()
  })

  it('renders targets when data provided', () => {
    const data = {
      networking: {
        targets: [
          { company: 'TechCorp', priority: 1, contactTypes: ['HR', 'Engineer'], reason: 'Good fit', strategy: 'Reach out on LinkedIn' },
        ],
      },
    }
    render(<NetworkingIntelSection {...defaultProps} data={data} />)
    expect(screen.getByText('TechCorp')).toBeInTheDocument()
    expect(screen.getByText('HR')).toBeInTheDocument()
    expect(screen.getByText('Engineer')).toBeInTheDocument()
    expect(screen.getByText('Good fit')).toBeInTheDocument()
  })

  it('renders connection strategy', () => {
    const data = {
      networking: {
        connectionStrategy: {
          whoToContactFirst: 'Engineering Managers',
          why: 'They make hiring decisions',
          suggestedSearchQueries: ['query1'],
          outreachTemplate: 'Hi, I am interested...',
        },
      },
    }
    render(<NetworkingIntelSection {...defaultProps} data={data} />)
    expect(screen.getByText('Connection Strategy')).toBeInTheDocument()
    expect(screen.getByText('Engineering Managers')).toBeInTheDocument()
  })

  it('renders LinkedIn search queries', () => {
    const data = {
      networking: {
        targets: [
          { company: 'Co', priority: 1, contactTypes: [], reason: '', linkedinSearchQueries: ['https://linkedin.com/search'] },
        ],
      },
    }
    render(<NetworkingIntelSection {...defaultProps} data={data} />)
    expect(screen.getByText('LinkedIn Search 1')).toBeInTheDocument()
  })

  it('renders generation history', () => {
    const history = [{ id: 'h1', source: 'networking', status: 'completed', created_at: '2026-07-20T10:00:00Z' }]
    render(<NetworkingIntelSection {...defaultProps} localHistory={history} />)
    expect(screen.getByText('Generation History')).toBeInTheDocument()
  })

  it('renders single running generation', () => {
    const singleRunning = { title: 'Analyzing networking...', source: 'networking', status: 'running' }
    render(<NetworkingIntelSection {...defaultProps} singleRunning={singleRunning} />)
    expect(screen.getByText('Analyzing networking...')).toBeInTheDocument()
  })
})
