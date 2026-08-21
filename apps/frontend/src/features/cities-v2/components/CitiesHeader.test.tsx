import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import { CitiesHeader } from './CitiesHeader'

vi.mock('sonner', () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}))

function baseProps(overrides: Partial<Parameters<typeof CitiesHeader>[0]> = {}): Parameters<typeof CitiesHeader>[0] {
  return { total: 240, loadedCount: 25, ...overrides }
}

describe('CitiesHeader', () => {
  it('renders the total count', () => {
    render(<CitiesHeader {...baseProps()} />)
    expect(screen.getByText(/Cities \(240\)/)).toBeInTheDocument()
  })

  it('renders the loaded count', () => {
    render(<CitiesHeader {...baseProps()} />)
    expect(screen.getByText(/Loaded 25 of 240 cities/)).toBeInTheDocument()
  })

  it('triggers onRefresh when the refresh button is clicked', () => {
    const onRefresh = vi.fn()
    render(<CitiesHeader {...baseProps({ onRefresh })} />)
    fireEvent.click(screen.getByRole('button', { name: 'Refresh cities' }))
    expect(onRefresh).toHaveBeenCalledTimes(1)
  })

  it('does not render the refresh button when onRefresh is not provided', () => {
    render(<CitiesHeader {...baseProps()} />)
    expect(screen.queryByRole('button', { name: 'Refresh cities' })).not.toBeInTheDocument()
  })

  it('disables the refresh button while refreshing', () => {
    render(<CitiesHeader {...baseProps({ onRefresh: vi.fn(), isRefreshing: true })} />)
    expect(screen.getByRole('button', { name: 'Refresh cities' })).toBeDisabled()
  })
})