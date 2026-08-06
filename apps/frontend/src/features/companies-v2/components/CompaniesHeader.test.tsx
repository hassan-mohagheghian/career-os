import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import { CompaniesHeader } from './CompaniesHeader'

vi.mock('sonner', () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}))

function baseProps(overrides: Partial<Parameters<typeof CompaniesHeader>[0]> = {}): Parameters<typeof CompaniesHeader>[0] {
  return {
    total: 7,
    loadedCount: 3,
    onOpenQueue: vi.fn(),
    onAddCompany: vi.fn(),
    ...overrides,
  }
}

describe('CompaniesHeader', () => {
  it('renders the total count', () => {
    render(<CompaniesHeader {...baseProps()} />)
    expect(screen.getByText(/Companies \(7\)/)).toBeInTheDocument()
  })

  it('triggers onRefresh when the refresh button is clicked', () => {
    const onRefresh = vi.fn()
    render(<CompaniesHeader {...baseProps({ onRefresh })} />)
    fireEvent.click(screen.getByRole('button', { name: 'Refresh companies' }))
    expect(onRefresh).toHaveBeenCalledTimes(1)
  })

  it('does not render the refresh button when onRefresh is not provided', () => {
    render(<CompaniesHeader {...baseProps()} />)
    expect(screen.queryByRole('button', { name: 'Refresh companies' })).not.toBeInTheDocument()
  })

  it('disables the refresh button while refreshing', () => {
    render(<CompaniesHeader {...baseProps({ onRefresh: vi.fn(), isRefreshing: true })} />)
    expect(screen.getByRole('button', { name: 'Refresh companies' })).toBeDisabled()
  })
})
