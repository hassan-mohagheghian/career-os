import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useApplicationGeneration } from './useApplicationGeneration'
import { subscribeProcessingEvents } from '@/shared/api/processingEvents'
import type { SSEEventEnvelope } from '@/entities/processing/types'

vi.mock('@/shared/api/processingEvents', () => ({
  subscribeProcessingEvents: vi.fn(),
}))

const subscribeMock = vi.mocked(subscribeProcessingEvents)
let listener: ((type: string, data: SSEEventEnvelope) => void) | null = null

beforeEach(() => {
  listener = null
  subscribeMock.mockImplementation((fn: (type: any, data: any) => void) => {
    listener = fn
    return () => {
      if (listener === fn) listener = null
    }
  })
})

afterEach(() => {
  vi.clearAllMocks()
})

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

function emit(type: string, data: Partial<SSEEventEnvelope>) {
  act(() => {
    listener?.(type, data as SSEEventEnvelope)
  })
}

describe('useApplicationGeneration', () => {
  it('tracks running state on execution.started for the matching application', () => {
    const { result } = renderHook(() => useApplicationGeneration('app-1'), { wrapper })

    emit('execution.started', {
      execution_id: 'exec-1',
      target_type: 'application',
      target_id: 'app-1',
      payload: { status: 'RUNNING', updated_at: 'now' },
    })

    expect(result.current.generation).toEqual({
      executionId: 'exec-1',
      status: 'running',
      progress: 0,
      currentStep: null,
      error: null,
    })
  })

  it('updates progress on workflow.step.progress', () => {
    const { result } = renderHook(() => useApplicationGeneration('app-1'), { wrapper })

    emit('execution.started', {
      execution_id: 'exec-1',
      target_type: 'application',
      target_id: 'app-1',
      payload: { status: 'RUNNING' },
    })
    emit('workflow.step.progress', {
      execution_id: 'exec-1',
      target_type: 'application',
      target_id: 'app-1',
      payload: {
        status: 'RUNNING',
        step: {
          id: 'step-1',
          node_id: 'generate',
          title: 'Generating',
          status: 'processing',
          progress: 55,
          displayable: true,
          children: [],
          error: null,
          started_at: null,
          completed_at: null,
        },
      },
    })

    expect(result.current.generation?.status).toBe('running')
    expect(result.current.generation?.progress).toBe(55)
    expect(result.current.generation?.currentStep).toBe('Generating')
  })

  it('marks failed and keeps the error message', () => {
    const { result } = renderHook(() => useApplicationGeneration('app-1'), { wrapper })

    emit('execution.failed', {
      execution_id: 'exec-1',
      target_type: 'application',
      target_id: 'app-1',
      payload: { status: 'FAILED', message: 'boom' },
    })

    expect(result.current.generation?.status).toBe('failed')
    expect(result.current.generation?.error).toBe('boom')
  })

  it('marks completed on execution.completed', () => {
    const { result } = renderHook(() => useApplicationGeneration('app-1'), { wrapper })

    emit('execution.completed', {
      execution_id: 'exec-1',
      target_type: 'application',
      target_id: 'app-1',
      payload: { status: 'COMPLETED' },
    })

    expect(result.current.generation?.status).toBe('completed')
    expect(result.current.generation?.progress).toBe(100)
  })

  it('ignores events for other applications', () => {
    const { result } = renderHook(() => useApplicationGeneration('app-1'), { wrapper })

    emit('execution.started', {
      execution_id: 'exec-other',
      target_type: 'application',
      target_id: 'app-2',
      payload: { status: 'RUNNING' },
    })

    expect(result.current.generation).toBeNull()
  })

  it('clearGeneration resets the state', () => {
    const { result } = renderHook(() => useApplicationGeneration('app-1'), { wrapper })

    emit('execution.completed', {
      execution_id: 'exec-1',
      target_type: 'application',
      target_id: 'app-1',
      payload: { status: 'COMPLETED' },
    })
    expect(result.current.generation?.status).toBe('completed')

    act(() => result.current.clearGeneration())
    expect(result.current.generation).toBeNull()
  })
})
