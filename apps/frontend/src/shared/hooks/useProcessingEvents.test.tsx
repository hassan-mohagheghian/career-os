import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { useProcessingEvents } from './useProcessingEvents'
import { subscribeProcessingEvents } from '@/shared/api/processingEvents'
import type { SSEEventType, SSEEventEnvelope } from '@/entities/processing/types'
import type { JobListItem } from '@/entities/job/types'

vi.mock('@/shared/api/processingEvents', () => ({
  subscribeProcessingEvents: vi.fn(),
}))

let emittedListener: ((type: SSEEventType, data: SSEEventEnvelope) => void) | null = null

function wrapper(qc: QueryClient) {
  return function QueryClientWrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  }
}

function makeJob(id: string): JobListItem {
  return {
    id,
    title: `Job ${id}`,
    company_name: 'Acme',
    location: 'Berlin',
    remote: false,
    visa_sponsorship: true,
    job_status: 'queued',
    latest_processing_execution: { id: 'exec-1', status: 'queued', started_at: null, finished_at: null },
    scores: { overall: null, fit: null, success: null },
    recommendation: null,
    pinned: false,
    dismissed: false,
    tags: [],
    rank: null,
    tracking_status: null,
    easy_apply: null,
    updated_at: null,
    created_at: '2026-08-01T00:00:00Z',
  }
}

function envelope(type: SSEEventType, overrides: Partial<SSEEventEnvelope> = {}): SSEEventEnvelope {
  return {
    id: 'evt-1',
    type,
    timestamp: '2026-08-01T00:00:00Z',
    job_id: 'job-1',
    execution_id: 'exec-1',
    payload: { status: 'COMPLETED', updated_at: '2026-08-01T00:01:00Z' },
    ...overrides,
  }
}

describe('useProcessingEvents', () => {
  let qc: QueryClient

  beforeEach(() => {
    vi.clearAllMocks()
    qc = new QueryClient({
      defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
    })
    vi.mocked(subscribeProcessingEvents).mockImplementation((listener) => {
      emittedListener = listener
      return () => { emittedListener = null }
    })
  })

  afterEach(() => {
    emittedListener = null
  })

  it('invalidates the jobs list cache when an execution completes', () => {
    qc.setQueryData(
      ['jobs-v2-infinite', { page: 1, page_size: 25 }],
      { pages: [{ items: [makeJob('job-1')], total_items: 1, has_more: false, next_cursor: null }], pageParams: [undefined] }
    )
    qc.setQueryData(['job-detail', 'job-1'], makeJob('job-1'))

    renderHook(() => useProcessingEvents(), { wrapper: wrapper(qc) })

    emittedListener?.('execution.completed', envelope('execution.completed'))

    expect(qc.getQueryState(['jobs-v2-infinite', { page: 1, page_size: 25 }])?.isInvalidated).toBe(true)
    expect(qc.getQueryState(['job-detail', 'job-1'])?.isInvalidated).toBe(true)
  })

  it('invalidates the jobs list cache when an execution fails', () => {
    qc.setQueryData(
      ['jobs-v2-infinite', { page: 1, page_size: 25 }],
      { pages: [{ items: [makeJob('job-1')], total_items: 1, has_more: false, next_cursor: null }], pageParams: [undefined] }
    )

    renderHook(() => useProcessingEvents(), { wrapper: wrapper(qc) })

    emittedListener?.('execution.failed', envelope('execution.failed', { payload: { status: 'FAILED', updated_at: null } }))

    expect(qc.getQueryState(['jobs-v2-infinite', { page: 1, page_size: 25 }])?.isInvalidated).toBe(true)
  })

  it('invalidates the jobs list cache when an execution is cancelled', () => {
    qc.setQueryData(
      ['jobs-v2-infinite', { page: 1, page_size: 25 }],
      { pages: [{ items: [makeJob('job-1')], total_items: 1, has_more: false, next_cursor: null }], pageParams: [undefined] }
    )

    renderHook(() => useProcessingEvents(), { wrapper: wrapper(qc) })

    emittedListener?.('execution.cancelled', envelope('execution.cancelled', { payload: { status: 'CANCELLED', updated_at: null } }))

    expect(qc.getQueryState(['jobs-v2-infinite', { page: 1, page_size: 25 }])?.isInvalidated).toBe(true)
  })

  it('does not invalidate the jobs list for non-terminal events', () => {
    qc.setQueryData(
      ['jobs-v2-infinite', { page: 1, page_size: 25 }],
      { pages: [{ items: [makeJob('job-1')], total_items: 1, has_more: false, next_cursor: null }], pageParams: [undefined] }
    )

    renderHook(() => useProcessingEvents(), { wrapper: wrapper(qc) })

    emittedListener?.('workflow.step.started', envelope('workflow.step.started', { payload: { status: 'RUNNING', updated_at: null } }))

    expect(qc.getQueryState(['jobs-v2-infinite', { page: 1, page_size: 25 }])?.isInvalidated).toBe(false)
  })
})
