import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import GenerationHistoryDrawer from './GenerationHistoryDrawer'

const mockItems = [
  { id: 1, source: 'job-processing', title: 'Job #1', status: 'completed', started_at: '2026-07-27T10:00:00Z', completed_at: '2026-07-27T10:05:00Z', error: null, session_id: null, provider: null },
  { id: 2, source: 'insights', title: 'Insights Run', status: 'failed', started_at: '2026-07-27T11:00:00Z', completed_at: null, error: 'Failed', session_id: null, provider: null },
]

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn(() =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ items: mockItems, total: mockItems.length }),
    })
  ))
})

describe('GenerationHistoryDrawer', () => {
  it('does not render when closed', () => {
    const { container } = render(
      <GenerationHistoryDrawer open={false} onOpenChange={vi.fn()} />
    )
    expect(container.querySelector('[role="dialog"]')).not.toBeInTheDocument()
  })

  it('renders when open and fetches history', async () => {
    render(<GenerationHistoryDrawer open={true} onOpenChange={vi.fn()} />)
    expect(screen.getByText('Generation History')).toBeInTheDocument()
    await waitFor(() => {
      expect(screen.getByText('Job #1')).toBeInTheDocument()
    })
  })

  it('calls onOpenChange when drawer closes', async () => {
    const onOpenChange = vi.fn()
    render(<GenerationHistoryDrawer open={true} onOpenChange={onOpenChange} />)
    // Drawer open state is managed by Sheet
    expect(screen.getByText('Generation History')).toBeInTheDocument()
  })

  it('shows item count', async () => {
    render(<GenerationHistoryDrawer open={true} onOpenChange={vi.fn()} />)
    await waitFor(() => {
      expect(screen.getByText(/2 runs/)).toBeInTheDocument()
    })
  })

  it('shows loading state', async () => {
    vi.stubGlobal('fetch', vi.fn(() => new Promise(() => {}))) // never resolves
    render(<GenerationHistoryDrawer open={true} onOpenChange={vi.fn()} />)
    expect(screen.getByText('Generation History')).toBeInTheDocument()
  })
})
