import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import ScoreBar from './ScoreBar'

describe('ScoreBar', () => {
  it('renders label and value', () => {
    render(<ScoreBar label="Fit Score" value={75} />)
    expect(screen.getByText('Fit Score')).toBeInTheDocument()
    expect(screen.getByText('75')).toBeInTheDocument()
  })

  it('renders ? for null value', () => {
    render(<ScoreBar label="Score" value={null} />)
    expect(screen.getByText('?')).toBeInTheDocument()
  })

  it('applies green bar for high value', () => {
    render(<ScoreBar label="Score" value={85} />)
    expect(screen.getByText('85')).toBeInTheDocument()
  })

  it('applies blue bar for medium-high value', () => {
    render(<ScoreBar label="Score" value={65} />)
    expect(screen.getByText('65')).toBeInTheDocument()
  })

  it('applies yellow bar for medium value', () => {
    render(<ScoreBar label="Score" value={45} />)
    expect(screen.getByText('45')).toBeInTheDocument()
  })

  it('applies red bar for low value', () => {
    render(<ScoreBar label="Score" value={20} />)
    expect(screen.getByText('20')).toBeInTheDocument()
  })

  it('handles custom max', () => {
    render(<ScoreBar label="Score" value={50} max={200} />)
    expect(screen.getByText('50')).toBeInTheDocument()
  })
})
