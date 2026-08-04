import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { useJobsInfiniteQuery } from './useJobsInfiniteQuery'
import { jobApi } from '@/entities/job/api'
import type { JobListItem, InfiniteJobSearchResult } from '@/entities/job/types'

vi.mock('@/entities/job/api', () => ({
  jobApi: {
    searchInfinite: vi.fn(),
    deleteJob: vi.fn(),
  },
}))

function makeJob(id: string): JobListItem {
  return {
    id,
    title: `Job ${id}`,
    company_name: 'Acme',
    location: 'Berlin',
    remote: false,
    visa_sponsorship: true,
    job_status: 'imported',
    latest_processing_execution: null,
    scores: { overall: null, fit: null, success: null },
    updated_at: null,
    created_at: '2026-08-01T00:00:00Z',
  }
}

function page(items: JobListItem[], total_items: number, has_more = false, next_cursor: string | null = null): InfiniteJobSearchResult {
  return { items, total_items, has_more, next_cursor }
}

function wrapper(qc: QueryClient) {
  return function QueryClientWrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  }
}

describe('useJobsInfiniteQuery.deleteMutation', () => {
  let qc: QueryClient
  let firstPage: JobListItem[]
  let secondPage: JobListItem[]

  beforeEach(() => {
    vi.clearAllMocks()
    qc = new QueryClient({
      defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
    })
    firstPage = [makeJob('job-1'), makeJob('job-2')]
    secondPage = [makeJob('job-3')]
    vi.mocked(jobApi.searchInfinite).mockImplementation((_q) =>
      Promise.resolve(_q?.cursor ? page(secondPage, 3, false) : page(firstPage, 3, true, 'cursor-2'))
    )
  })

  it('optimistically removes the job and decrements the total before the request resolves', async () => {
    let resolveDelete!: () => void
    vi.mocked(jobApi.deleteJob).mockImplementation(() => new Promise<void>((resolve) => { resolveDelete = resolve }))

    const { result } = renderHook(() => useJobsInfiniteQuery(), { wrapper: wrapper(qc) })

    await waitFor(() => {
      expect(result.current.items).toHaveLength(2)
    })

    act(() => {
      result.current.deleteMutation.mutate('job-1')
    })

    await waitFor(() => {
      const cached = qc.getQueriesData<{ pages: { items: JobListItem[]; total_items: number }[] }>({ queryKey: ['jobs-v2-infinite'] })
      const pages = cached[0]?.[1]?.pages ?? []
      expect(pages[0].items.map(i => i.id)).not.toContain('job-1')
      expect(pages[0].total_items).toBe(2)
    })

    act(() => { resolveDelete() })
    await waitFor(() => {
      expect(result.current.deleteMutation.isSuccess).toBe(true)
    })
  })

  it('restores the removed job when the delete request fails', async () => {
    vi.mocked(jobApi.deleteJob).mockRejectedValue(new Error('boom'))

    const { result } = renderHook(() => useJobsInfiniteQuery(), { wrapper: wrapper(qc) })

    await waitFor(() => {
      expect(result.current.items).toHaveLength(2)
    })

    await act(async () => {
      result.current.deleteMutation.mutate('job-1')
    })

    await waitFor(() => {
      expect(result.current.deleteMutation.isError).toBe(true)
    })

    const cached = qc.getQueriesData<{ pages: { items: JobListItem[]; total_items: number }[] }>({ queryKey: ['jobs-v2-infinite'] })
    const pages = cached[0]?.[1]?.pages ?? []
    expect(pages[0].items.map(i => i.id)).toContain('job-1')
    expect(pages[0].total_items).toBe(3)
  })
})
