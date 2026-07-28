import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import { Section, TabHeader, Field, TagList, ScoreBadge, DRAWER_WIDTH } from './DrawerComponents'

describe('Section', () => {
  it('renders title and children', () => {
    render(<Section title="My Section"><div>Child content</div></Section>)
    expect(screen.getByText('My Section')).toBeInTheDocument()
    expect(screen.getByText('Child content')).toBeInTheDocument()
  })

  it('renders with icon', () => {
    render(<Section title="With Icon" icon={<span data-testid="icon">★</span>}><span>Content</span></Section>)
    expect(screen.getByTestId('icon')).toBeInTheDocument()
    expect(screen.getByText('With Icon')).toBeInTheDocument()
  })
})

describe('TabHeader', () => {
  it('renders title', () => {
    render(<TabHeader title="Header Title" />)
    expect(screen.getByText('Header Title')).toBeInTheDocument()
  })

  it('renders with icon', () => {
    render(<TabHeader title="Header" icon={<span data-testid="icon">★</span>} />)
    expect(screen.getByTestId('icon')).toBeInTheDocument()
  })

  it('applies custom className', () => {
    render(<TabHeader title="Header" className="custom-class" />)
    expect(screen.getByText('Header').className).toContain('custom-class')
  })
})

describe('Field', () => {
  it('renders label and value', () => {
    render(<Field label="Name" value="John" />)
    expect(screen.getByText('Name:')).toBeInTheDocument()
    expect(screen.getByText('John')).toBeInTheDocument()
  })

  it('returns null when value is falsy', () => {
    const { container } = render(<Field label="Name" value={null} />)
    expect(container.innerHTML).toBe('')
  })

  it('returns null when value is empty string', () => {
    const { container } = render(<Field label="Name" value="" />)
    expect(container.innerHTML).toBe('')
  })
})

describe('TagList', () => {
  it('renders list of tags', () => {
    render(<TagList items={['React', 'TypeScript', 'Node']} />)
    expect(screen.getByText('React')).toBeInTheDocument()
    expect(screen.getByText('TypeScript')).toBeInTheDocument()
    expect(screen.getByText('Node')).toBeInTheDocument()
  })

  it('returns null for empty array', () => {
    const { container } = render(<TagList items={[]} />)
    expect(container.innerHTML).toBe('')
  })

  it('returns null for null items', () => {
    const { container } = render(<TagList items={null} />)
    expect(container.innerHTML).toBe('')
  })
})

describe('ScoreBadge', () => {
  it('renders value and label', () => {
    render(<ScoreBadge value={85} label="Fit" />)
    expect(screen.getByText('85')).toBeInTheDocument()
    expect(screen.getByText('Fit')).toBeInTheDocument()
  })

  it('shows ? when value is null', () => {
    render(<ScoreBadge value={null} label="Score" />)
    expect(screen.getByText('?')).toBeInTheDocument()
  })

  it('applies lg size by default', () => {
    render(<ScoreBadge value={85} label="Score" />)
    const valueEl = screen.getByText('85')
    expect(valueEl.className).toContain('text-lg')
  })

  it('applies 4xl size', () => {
    render(<ScoreBadge value={85} label="Score" size="4xl" />)
    const valueEl = screen.getByText('85')
    expect(valueEl.className).toContain('text-4xl')
  })

  it('applies blue color', () => {
    render(<ScoreBadge value={85} label="Score" color="blue" />)
    const valueEl = screen.getByText('85')
    expect(valueEl.className).toContain('text-blue-400')
  })
})

describe('DRAWER_WIDTH', () => {
  it('exports a valid width class', () => {
    expect(DRAWER_WIDTH).toBeTruthy()
    expect(typeof DRAWER_WIDTH).toBe('string')
  })
})
