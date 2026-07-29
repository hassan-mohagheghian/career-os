import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import Header from './Header'

describe('Header', () => {
  const defaultProps = {
    theme: 'dark',
    tab: 'jobs',
    onSwitchTab: vi.fn(),
    onToggleTheme: vi.fn(),
  }

  it('renders brand name', () => {
    render(<Header {...defaultProps} />)
    expect(screen.getByText('Job Search')).toBeInTheDocument()
  })

  it('renders feature tabs', () => {
    render(<Header {...defaultProps} />)
    expect(screen.getByText('Jobs')).toBeInTheDocument()
    expect(screen.getByText('Companies')).toBeInTheDocument()
    expect(screen.getByText('Resume')).toBeInTheDocument()
    expect(screen.getByText('Rules')).toBeInTheDocument()
  })

  it('calls onSwitchTab when feature tab clicked', () => {
    const onSwitchTab = vi.fn()
    render(<Header {...defaultProps} onSwitchTab={onSwitchTab} />)
    fireEvent.click(screen.getByText('Companies'))
    expect(onSwitchTab).toHaveBeenCalledWith('companies')
  })

  it('calls onToggleTheme when theme button clicked', () => {
    const onToggleTheme = vi.fn()
    render(<Header {...defaultProps} onToggleTheme={onToggleTheme} />)
    const allButtons = screen.getAllByRole('button')
    const themeBtn = allButtons[allButtons.length - 2]
    fireEvent.click(themeBtn)
    expect(onToggleTheme).toHaveBeenCalled()
  })

  it('calls onSwitchTab with jobs when brand clicked', () => {
    const onSwitchTab = vi.fn()
    render(<Header {...defaultProps} onSwitchTab={onSwitchTab} />)
    fireEvent.click(screen.getByText('Job Search'))
    expect(onSwitchTab).toHaveBeenCalledWith('jobs')
  })
})
