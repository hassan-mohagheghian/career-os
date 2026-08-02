import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import { MultiSelect } from './MultiSelect'

const options = [
  { value: 'Berlin', label: 'Berlin' },
  { value: 'Munich', label: 'Munich' },
  { value: 'Hamburg', label: 'Hamburg' },
]

describe('MultiSelect', () => {
  it('renders with placeholder', () => {
    render(<MultiSelect value={[]} onChange={vi.fn()} options={options} placeholder="City" />)
    expect(screen.getByText('City')).toBeInTheDocument()
  })

  it('shows count when items selected', () => {
    render(<MultiSelect value={['Berlin']} onChange={vi.fn()} options={options} placeholder="City" />)
    expect(screen.getByText('1 sel')).toBeInTheDocument()
  })

  it('shows multiple selection count', () => {
    render(<MultiSelect value={['Berlin', 'Munich']} onChange={vi.fn()} options={options} placeholder="City" />)
    expect(screen.getByText('2 sel')).toBeInTheDocument()
  })

  it('opens popover when clicked', () => {
    render(<MultiSelect value={[]} onChange={vi.fn()} options={options} placeholder="City" />)
    fireEvent.click(screen.getByText('City'))
    expect(screen.getByText('Berlin')).toBeInTheDocument()
    expect(screen.getByText('Munich')).toBeInTheDocument()
  })

  it('calls onChange when option toggled', () => {
    const onChange = vi.fn()
    render(<MultiSelect value={[]} onChange={onChange} options={options} placeholder="City" />)
    fireEvent.click(screen.getByText('City'))
    fireEvent.click(screen.getByText('Berlin'))
    expect(onChange).toHaveBeenCalledWith(['Berlin'])
  })

  it('deselects option when already selected', () => {
    const onChange = vi.fn()
    render(<MultiSelect value={['Berlin']} onChange={onChange} options={options} placeholder="City" />)
    fireEvent.click(screen.getByText('1 sel'))
    fireEvent.click(screen.getByText('Berlin'))
    expect(onChange).toHaveBeenCalledWith([])
  })

  it('renders with icon', () => {
    render(<MultiSelect value={[]} onChange={vi.fn()} options={options} placeholder="City" icon={<span data-testid="icon">★</span>} />)
    expect(screen.getByTestId('icon')).toBeInTheDocument()
  })
})
