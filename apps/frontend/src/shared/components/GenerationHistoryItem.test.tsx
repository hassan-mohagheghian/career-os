import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import GenerationHistoryItem from './GenerationHistoryItem'

const baseItem = {
  id: 1,
  source: 'job-processing',
  title: 'Software Engineer at Acme',
  status: 'processed',
  started_at: '2026-07-27T10:00:00Z',
  completed_at: '2026-07-27T10:05:00Z',
  error: null,
  session_id: 'sess-abc-123',
  provider: 'claude',
}

describe('GenerationHistoryItem', () => {
  it('renders title and status in full mode', () => {
    render(<GenerationHistoryItem item={baseItem} />)
    expect(screen.getByText('Software Engineer at Acme')).toBeInTheDocument()
    expect(screen.getByText('processed')).toBeInTheDocument()
  })

  it('renders in compact mode', () => {
    render(<GenerationHistoryItem item={baseItem} compact />)
    expect(screen.getByText('Software Engineer at Acme')).toBeInTheDocument()
    expect(screen.getByText('processed')).toBeInTheDocument()
  })

  it('renders source badge label', () => {
    render(<GenerationHistoryItem item={baseItem} />)
    expect(screen.getByText('Job')).toBeInTheDocument()
  })

  it('renders error message when present', () => {
    const item = { ...baseItem, error: 'Processing failed', status: 'failed' }
    render(<GenerationHistoryItem item={item} />)
    expect(screen.getByText('Processing failed')).toBeInTheDocument()
  })

  it('renders session button with provider label', () => {
    render(<GenerationHistoryItem item={baseItem} />)
    expect(screen.getByText('Claude')).toBeInTheDocument()
  })

  it('copies session ID on click', () => {
    const writeText = vi.fn()
    Object.assign(navigator, { clipboard: { writeText } })
    render(<GenerationHistoryItem item={baseItem} />)
    fireEvent.click(screen.getByTitle(/Click to copy/))
    expect(writeText).toHaveBeenCalledWith('sess-abc-123')
  })

  it('does not render session button when no provider', () => {
    const item = { ...baseItem, provider: null }
    render(<GenerationHistoryItem item={item} />)
    expect(screen.queryByTitle(/Click to copy/)).not.toBeInTheDocument()
  })

  it('shows time info with started and completed', () => {
    render(<GenerationHistoryItem item={baseItem} />)
    // Should render time strings
    expect(screen.getByText(/→/)).toBeInTheDocument()
  })

  it('uses default source config for unknown source', () => {
    const item = { ...baseItem, source: 'unknown_source' }
    render(<GenerationHistoryItem item={item} />)
    // Should not crash, uses fallback
    expect(screen.getByText('Software Engineer at Acme')).toBeInTheDocument()
  })

  it('renders provider label for mimo provider', () => {
    const item = { ...baseItem, provider: 'mimo', session_id: 'sess-456' }
    render(<GenerationHistoryItem item={item} />)
    expect(screen.getByText('MiMo')).toBeInTheDocument()
  })

  it('renders with showFullDatetime', () => {
    render(<GenerationHistoryItem item={baseItem} showFullDatetime />)
    expect(screen.getByText('Software Engineer at Acme')).toBeInTheDocument()
  })

  it('renders no time when no started_at or completed_at', () => {
    const item = { ...baseItem, started_at: null, completed_at: null }
    render(<GenerationHistoryItem item={item} />)
    expect(screen.getByText('Software Engineer at Acme')).toBeInTheDocument()
  })

  it('renders cancelled status with yellow color', () => {
    const item = { ...baseItem, status: 'cancelled' }
    render(<GenerationHistoryItem item={item} />)
    expect(screen.getByText('cancelled')).toBeInTheDocument()
  })

  it('renders running status', () => {
    const item = { ...baseItem, status: 'running', completed_at: null }
    render(<GenerationHistoryItem item={item} />)
    expect(screen.getByText('running')).toBeInTheDocument()
  })
})
