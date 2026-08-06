import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom'
import Header from './index'

const pushMock = vi.fn()

vi.mock('next/navigation', () => ({
  usePathname: () => '/jobs',
  useRouter: () => ({ push: pushMock }),
}))

vi.mock('next-themes', () => ({
  useTheme: () => ({ theme: 'light', setTheme: vi.fn() }),
}))

vi.mock('next/dynamic', () => ({
  __esModule: true,
  default: () => () => null,
}))

describe('Header', () => {
  beforeEach(() => {
    pushMock.mockClear()
  })

  it('renders all main nav items', () => {
    render(<Header />)
    expect(screen.getByRole('navigation', { name: 'Main navigation' })).toBeInTheDocument()
    for (const label of ['Jobs', 'Companies', 'Skills', 'Resume', 'Rules', 'AI']) {
      expect(screen.getByRole('button', { name: new RegExp(label, 'i') })).toBeInTheDocument()
    }
  })

  it('marks the active tab', () => {
    render(<Header />)
    expect(screen.getByRole('button', { name: /jobs/i })).toHaveClass('text-primary')
  })

  it('navigates on non-active item click', async () => {
    const user = userEvent.setup()
    render(<Header />)
    await user.click(screen.getByRole('button', { name: /companies/i }))
    expect(pushMock).toHaveBeenCalledWith('/companies')
  })

  it('does not hide the menu when the active item is clicked', async () => {
    const user = userEvent.setup()
    render(<Header />)
    const jobs = screen.getByRole('button', { name: /jobs/i })
    await user.click(jobs)
    expect(pushMock).toHaveBeenCalledWith('/jobs')
    expect(screen.getByRole('button', { name: /jobs/i })).toBeInTheDocument()
    expect(screen.getByRole('navigation', { name: 'Main navigation' })).toBeInTheDocument()
  })

  it('opens the AI submenu with LLM Configurations and navigates', async () => {
    const user = userEvent.setup()
    render(<Header />)
    await user.click(screen.getByRole('button', { name: /ai/i }))
    const submenu = await waitFor(() => screen.getByRole('menuitem', { name: /llm configurations/i }))
    await user.click(submenu)
    expect(pushMock).toHaveBeenCalledWith('/ai/llm-configurations')
  })
})
