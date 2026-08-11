import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import { GenerationProgress } from './GenerationProgress'
import type { ApplicationGenerationState } from '../hooks/useApplicationGeneration'

describe('GenerationProgress', () => {
  it('shows running status with progress and current step', () => {
    const generation: ApplicationGenerationState = {
      executionId: 'exec-1',
      status: 'running',
      progress: 42,
      currentStep: 'Generating resume',
      error: null,
    }
    render(<GenerationProgress generation={generation} />)
    expect(screen.getByText(/in progress/)).toBeInTheDocument()
    expect(screen.getByText('Generating resume')).toBeInTheDocument()
    expect(screen.getByText('42%')).toBeInTheDocument()
  })

  it('shows completed state with a success message', () => {
    const generation: ApplicationGenerationState = {
      executionId: 'exec-1',
      status: 'completed',
      progress: 100,
      currentStep: null,
      error: null,
    }
    render(<GenerationProgress generation={generation} />)
    expect(screen.getByText(/Generated successfully/)).toBeInTheDocument()
  })

  it('shows the error message for a failed generation', () => {
    const generation: ApplicationGenerationState = {
      executionId: 'exec-1',
      status: 'failed',
      progress: null,
      currentStep: null,
      error: 'The AI returned an invalid result',
    }
    render(<GenerationProgress generation={generation} />)
    expect(screen.getByText('The AI returned an invalid result')).toBeInTheDocument()
  })

  it('calls onDismiss when Dismiss is clicked for a completed generation', () => {
    const onDismiss = vi.fn()
    const generation: ApplicationGenerationState = {
      executionId: 'exec-1',
      status: 'completed',
      progress: 100,
      currentStep: null,
      error: null,
    }
    render(<GenerationProgress generation={generation} onDismiss={onDismiss} />)
    fireEvent.click(screen.getByText('Dismiss'))
    expect(onDismiss).toHaveBeenCalled()
  })

  it('does not show Dismiss while running', () => {
    const generation: ApplicationGenerationState = {
      executionId: 'exec-1',
      status: 'running',
      progress: 10,
      currentStep: null,
      error: null,
    }
    render(<GenerationProgress generation={generation} onDismiss={vi.fn()} />)
    expect(screen.queryByText('Dismiss')).not.toBeInTheDocument()
  })
})
