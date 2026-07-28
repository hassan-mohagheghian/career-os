import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import GenerationProgressCard from './GenerationProgressCard'

describe('GenerationProgressCard', () => {
  it('renders nothing when not running and not failed/cancelled', () => {
    const { container } = render(<GenerationProgressCard title="Processing" progress={{ running: false }} />)
    expect(container.innerHTML).toBe('')
  })

  it('renders title when running', () => {
    render(<GenerationProgressCard title="Generating..." progress={{ running: true }} />)
    expect(screen.getAllByText('Generating...').length).toBeGreaterThanOrEqual(1)
  })

  it('renders LIVE badge when running', () => {
    render(<GenerationProgressCard title="Running" progress={{ running: true }} />)
    expect(screen.getByText('LIVE')).toBeInTheDocument()
  })

  it('renders failed state', () => {
    render(<GenerationProgressCard title="Failed" progress={{ running: false, status: 'failed', error: 'Oops' }} />)
    expect(screen.getByText('Failed')).toBeInTheDocument()
  })

  it('renders cancelled state', () => {
    render(<GenerationProgressCard title="Cancelled" progress={{ running: false, status: 'cancelled' }} />)
    expect(screen.getByText('Cancelled')).toBeInTheDocument()
  })

  it('renders Terminate button when running with onCancel', () => {
    const onCancel = vi.fn()
    render(<GenerationProgressCard title="Running" progress={{ running: true }} onCancel={onCancel} />)
    expect(screen.getByText('Terminate')).toBeInTheDocument()
  })

  it('renders with steps when running', () => {
    const steps = [{ key: 'step_fetch', label: 'Fetching' }, { key: 'step_analyze', label: 'Analyzing' }]
    render(<GenerationProgressCard title="Running" progress={{ running: true, step: 1 }} steps={steps} />)
    expect(screen.getAllByText((_, el) => el?.textContent?.includes('Fetching') ?? false).length).toBeGreaterThanOrEqual(1)
  })

  it('renders compact mode', () => {
    render(<GenerationProgressCard title="Processing" progress={{ running: true }} compact />)
    expect(screen.getByText('Processing')).toBeInTheDocument()
  })

  it('renders elapsed seconds', () => {
    render(<GenerationProgressCard title="Running" progress={{ running: true, elapsed_seconds: 45 }} />)
    expect(screen.getByText('45s')).toBeInTheDocument()
  })

  it('renders elapsed minutes', () => {
    render(<GenerationProgressCard title="Running" progress={{ running: true, elapsed_seconds: 125 }} />)
    expect(screen.getByText('2m 5s')).toBeInTheDocument()
  })

  it('renders type when provided', () => {
    render(<GenerationProgressCard title="Running" progress={{ running: true }} type="job-processing" />)
    expect(screen.getByText('job-processing')).toBeInTheDocument()
  })
})
