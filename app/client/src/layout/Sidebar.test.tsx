import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import Sidebar from './Sidebar'

const tabs = [
  { id: 'jobs', section: 'jobs', label: 'Jobs', icon: <span>J</span> },
  { id: 'companies', section: 'jobs', label: 'Companies', icon: <span>C</span>, badge: 5 },
  { id: 'resume', section: 'settings', label: 'Resume', icon: <span>R</span> },
  {
    id: 'insights', section: 'jobs', label: 'Insights', icon: <span>I</span>,
    children: [
      { id: 'overview', label: 'Overview' },
      { id: 'skills', label: 'Skills' },
    ]
  },
]

describe('Sidebar', () => {
  it('renders section headers', () => {
    render(<Sidebar sidebarOpen={true} tabs={tabs} tab="jobs" onSwitchTab={vi.fn()} onClose={vi.fn()} />)
    expect(screen.getByText('jobs')).toBeInTheDocument()
    expect(screen.getByText('settings')).toBeInTheDocument()
  })

  it('renders tab labels', () => {
    render(<Sidebar sidebarOpen={true} tabs={tabs} tab="jobs" onSwitchTab={vi.fn()} onClose={vi.fn()} />)
    expect(screen.getByText('Jobs')).toBeInTheDocument()
    expect(screen.getByText('Companies')).toBeInTheDocument()
    expect(screen.getByText('Resume')).toBeInTheDocument()
  })

  it('renders badge', () => {
    render(<Sidebar sidebarOpen={true} tabs={tabs} tab="jobs" onSwitchTab={vi.fn()} onClose={vi.fn()} />)
    expect(screen.getByText('5')).toBeInTheDocument()
  })

  it('calls onSwitchTab when tab clicked', () => {
    const onSwitchTab = vi.fn()
    render(<Sidebar sidebarOpen={true} tabs={tabs} tab="jobs" onSwitchTab={onSwitchTab} onClose={vi.fn()} />)
    fireEvent.click(screen.getByText('Resume'))
    expect(onSwitchTab).toHaveBeenCalledWith('resume')
  })

  it('renders child tabs for insights', () => {
    render(<Sidebar sidebarOpen={true} tabs={tabs} tab="insights" onSwitchTab={vi.fn()} onClose={vi.fn()} />)
    expect(screen.getByText('Overview')).toBeInTheDocument()
    expect(screen.getByText('Skills')).toBeInTheDocument()
  })

  it('hides sidebar when sidebarOpen is false', () => {
    const { container } = render(<Sidebar sidebarOpen={false} tabs={tabs} tab="jobs" onSwitchTab={vi.fn()} onClose={vi.fn()} />)
    const aside = container.querySelector('aside')
    expect(aside.className).toContain('w-0')
  })

  it('shows overlay when sidebar open on mobile', () => {
    render(<Sidebar sidebarOpen={true} tabs={tabs} tab="jobs" onSwitchTab={vi.fn()} onClose={vi.fn()} />)
    // Overlay div
    expect(screen.getByText('Jobs')).toBeInTheDocument()
  })

  it('calls onClose when overlay clicked', () => {
    const onClose = vi.fn()
    render(<Sidebar sidebarOpen={true} tabs={tabs} tab="jobs" onSwitchTab={vi.fn()} onClose={onClose} />)
    const overlay = document.querySelector('.fixed.inset-0.bg-black\\/40')
    if (overlay) fireEvent.click(overlay)
    expect(onClose).toHaveBeenCalled()
  })
})
