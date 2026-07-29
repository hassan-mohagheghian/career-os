import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import ProcessingCardFrame from './ProcessingCardFrame'

describe('ProcessingCardFrame', () => {
  it('renders children', () => {
    render(<ProcessingCardFrame status="created"><span>Hello</span></ProcessingCardFrame>)
    expect(screen.getByText('Hello')).toBeInTheDocument()
  })

  it('applies border for failed status', () => {
    const { container } = render(<ProcessingCardFrame status="failed"><span /></ProcessingCardFrame>)
    expect(container.firstChild).toHaveClass('border-red-500/30')
  })

  it('applies border for done status', () => {
    const { container } = render(<ProcessingCardFrame status="processed"><span /></ProcessingCardFrame>)
    expect(container.firstChild).toHaveClass('border-green-500/30')
  })

  it('no special border for neutral status', () => {
    const { container } = render(<ProcessingCardFrame status="queued"><span /></ProcessingCardFrame>)
    expect(container.firstChild).not.toHaveClass('border-red-500/30')
    expect(container.firstChild).not.toHaveClass('border-green-500/30')
  })

  it('supports drag handle', () => {
    const { container } = render(<ProcessingCardFrame status="created" onDragStart={() => {}}><span /></ProcessingCardFrame>)
    expect(container.firstChild).toHaveAttribute('draggable', 'true')
  })
})
