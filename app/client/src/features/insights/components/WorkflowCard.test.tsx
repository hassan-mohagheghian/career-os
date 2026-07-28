import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import WorkflowCard from './WorkflowCard'

describe('WorkflowCard', () => {
  it('renders section name', () => {
    render(<WorkflowCard section="overview" status={{}} />)
    expect(screen.getByText('overview')).toBeInTheDocument()
  })

  it('renders steps', () => {
    render(<WorkflowCard section="overview" status={{}} />)
    expect(screen.getByText('Collecting data')).toBeInTheDocument()
    expect(screen.getByText('AI analysis')).toBeInTheDocument()
    expect(screen.getByText('Calculating metrics')).toBeInTheDocument()
    expect(screen.getByText('Saving results')).toBeInTheDocument()
  })

  it('renders Unknown status when empty status', () => {
    render(<WorkflowCard section="overview" status={{}} />)
    expect(screen.getByText('Unknown')).toBeInTheDocument()
  })

  it('renders Generating status when processing', () => {
    render(<WorkflowCard section="overview" status={{ status: 'processing' }} />)
    expect(screen.getByText('Generating...')).toBeInTheDocument()
  })

  it('renders Complete status', () => {
    render(<WorkflowCard section="overview" status={{ status: 'completed' }} />)
    expect(screen.getByText('Complete')).toBeInTheDocument()
  })

  it('renders Failed status', () => {
    render(<WorkflowCard section="overview" status={{ status: 'failed' }} />)
    expect(screen.getByText('Failed')).toBeInTheDocument()
  })

  it('renders error message when failed', () => {
    render(<WorkflowCard section="overview" status={{ status: 'failed', error: 'API error' }} />)
    expect(screen.getByText('API error')).toBeInTheDocument()
  })

  it('renders Queued status for pending', () => {
    render(<WorkflowCard section="overview" status={{ status: 'pending' }} />)
    expect(screen.getByText('Queued')).toBeInTheDocument()
  })

  it('handles undefined status', () => {
    render(<WorkflowCard section="overview" />)
    expect(screen.getByText('Unknown')).toBeInTheDocument()
  })
})
