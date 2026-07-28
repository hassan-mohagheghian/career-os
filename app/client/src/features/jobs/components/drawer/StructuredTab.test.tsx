import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import StructuredTab from './StructuredTab'

describe('StructuredTab', () => {
  it('renders no data message when no structured_description', () => {
    render(<StructuredTab job={{}} />)
    expect(screen.getByText('No structured data available')).toBeInTheDocument()
  })

  it('renders requirements when structured_description present', () => {
    const job = { structured_description: JSON.stringify({ requirements: ['React', 'Node.js'], responsibilities: ['Build APIs'] }) }
    render(<StructuredTab job={job} />)
    expect(screen.getByText('React')).toBeInTheDocument()
    expect(screen.getByText('Node.js')).toBeInTheDocument()
    expect(screen.getByText('Build APIs')).toBeInTheDocument()
  })

  it('renders nice_to_have', () => {
    const job = { structured_description: JSON.stringify({ nice_to_have: ['TypeScript'] }) }
    render(<StructuredTab job={job} />)
    expect(screen.getByText('TypeScript')).toBeInTheDocument()
  })

  it('handles invalid JSON gracefully', () => {
    render(<StructuredTab job={{ structured_description: '{bad' }} />)
    expect(screen.getByText('No structured data available')).toBeInTheDocument()
  })

  it('renders content when arrays have items', () => {
    const job = { structured_description: JSON.stringify({ requirements: ['React'], nice_to_have: ['TypeScript'] }) }
    render(<StructuredTab job={job} />)
    expect(screen.getByText('React')).toBeInTheDocument()
  })
})
