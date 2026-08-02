import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import { TechCard, StackCard } from './TechCards'

describe('TechCard', () => {
  const tech = {
    name: 'React',
    pc: 'p1',
    pl: 'Primary',
    usage: 80,
    uc: '#22c55e',
    jobs: 50,
    jd: 'jobs use it',
    reason: 'Industry standard',
    sc: 'green',
    dc: 'bg-green-500',
    action: 'Learn',
  }

  it('renders name', () => {
    render(<TechCard tech={tech} />)
    expect(screen.getByText('React')).toBeInTheDocument()
  })

  it('renders priority label', () => {
    render(<TechCard tech={tech} />)
    expect(screen.getByText('Primary')).toBeInTheDocument()
  })

  it('renders usage percentage', () => {
    render(<TechCard tech={tech} />)
    expect(screen.getByText('80%')).toBeInTheDocument()
  })

  it('renders job count', () => {
    render(<TechCard tech={tech} />)
    expect(screen.getByText('50')).toBeInTheDocument()
  })

  it('renders reason', () => {
    render(<TechCard tech={tech} />)
    expect(screen.getByText('Industry standard')).toBeInTheDocument()
  })

  it('renders action badge text', () => {
    render(<TechCard tech={tech} />)
    expect(screen.getByText('green — Learn')).toBeInTheDocument()
  })
})

describe('StackCard', () => {
  const tech = {
    name: 'React',
    mc: 'p1',
    ml: 'Major',
    level: 4,
    roles: '5 roles',
    path: 'Frontend path',
  }

  it('renders name', () => {
    render(<StackCard tech={tech} />)
    expect(screen.getByText('React')).toBeInTheDocument()
  })

  it('renders level bars', () => {
    render(<StackCard tech={tech} />)
    expect(screen.getByText('Major')).toBeInTheDocument()
  })

  it('renders roles', () => {
    render(<StackCard tech={tech} />)
    expect(screen.getByText('5 roles')).toBeInTheDocument()
  })

  it('renders path', () => {
    render(<StackCard tech={tech} />)
    expect(screen.getByText('Frontend path')).toBeInTheDocument()
  })
})
