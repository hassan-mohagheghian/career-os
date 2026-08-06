import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import { JobsHeader } from './JobsHeader'

vi.mock('sonner', () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}))

function baseProps(overrides: Partial<Parameters<typeof JobsHeader>[0]> = {}): Parameters<typeof JobsHeader>[0] {
  return {
    total: 10,
    loadedCount: 5,
    processingCount: 0,
    onOpenQueue: vi.fn(),
    onAddJob: vi.fn(),
    ...overrides,
  }
}

describe('JobsHeader', () => {
  it('renders the total count and add job shortcut hint', () => {
    render(<JobsHeader {...baseProps()} />)
    expect(screen.getByText(/Jobs \(10\)/)).toBeInTheDocument()
    expect(screen.getByText('N')).toBeInTheDocument()
  })

  it('triggers onRefresh when the refresh button is clicked', () => {
    const onRefresh = vi.fn()
    render(<JobsHeader {...baseProps({ onRefresh })} />)
    fireEvent.click(screen.getByRole('button', { name: 'Refresh jobs' }))
    expect(onRefresh).toHaveBeenCalledTimes(1)
  })

  it('does not render the refresh button when onRefresh is not provided', () => {
    render(<JobsHeader {...baseProps()} />)
    expect(screen.queryByRole('button', { name: 'Refresh jobs' })).not.toBeInTheDocument()
  })

  it('disables the refresh button while refreshing', () => {
    render(<JobsHeader {...baseProps({ onRefresh: vi.fn(), isRefreshing: true })} />)
    expect(screen.getByRole('button', { name: 'Refresh jobs' })).toBeDisabled()
  })

  it('shows a queue badge when there are processing items', () => {
    render(<JobsHeader {...baseProps({ processingCount: 3 })} />)
    expect(screen.getByText('3')).toBeInTheDocument()
  })
})
