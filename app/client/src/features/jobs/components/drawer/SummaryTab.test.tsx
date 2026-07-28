import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import SummaryTab from './SummaryTab'

describe('SummaryTab', () => {
  it('renders no summary message when null', () => {
    render(<SummaryTab summary={null} />)
    expect(screen.getByText('No summary available')).toBeInTheDocument()
  })

  it('renders summary text', () => {
    render(<SummaryTab summary={{ summary: 'Great opportunity', stack: 'React, Node', resumeFit: 'Strong match', score: 'A', note: 'Apply now' }} />)
    expect(screen.getByText('Great opportunity')).toBeInTheDocument()
  })

  it('renders stack required', () => {
    render(<SummaryTab summary={{ summary: 'x', stack: 'React, Node', resumeFit: 'y', score: 'A', note: 'z' }} />)
    expect(screen.getByText('React, Node')).toBeInTheDocument()
  })

  it('renders resume fit', () => {
    render(<SummaryTab summary={{ summary: 'x', stack: 'y', resumeFit: 'Strong match', score: 'A', note: 'z' }} />)
    expect(screen.getByText('Strong match')).toBeInTheDocument()
  })

  it('renders note', () => {
    render(<SummaryTab summary={{ summary: 'x', stack: 'y', resumeFit: 'z', score: 'A', note: 'Apply now' }} />)
    expect(screen.getByText('Apply now')).toBeInTheDocument()
  })

  it('renders section headers', () => {
    render(<SummaryTab summary={{ summary: 'x', stack: 'y', resumeFit: 'z', score: 'A', note: 'w' }} />)
    expect(screen.getByText('Summary')).toBeInTheDocument()
    expect(screen.getByText('Stack Required')).toBeInTheDocument()
    expect(screen.getByText('Resume Fit')).toBeInTheDocument()
    expect(screen.getByText('Note')).toBeInTheDocument()
  })
})
