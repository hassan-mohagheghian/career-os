'use client'

import { useState, useMemo, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { jobApi } from '@/entities/job/api'
import type { JobListItem, JobSearchQuery, ProcessingStatus } from '@/entities/job/types'

const PAGE_SIZE = 30
const JOBS_KEY = 'jobs-v2'

export function useJobSearch() {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(0)
  const [query, setQuery] = useState('')
  const [sort, setSort] = useState('created_at')
  const [order, setOrder] = useState<'asc' | 'desc'>('desc')
  const [filterProcessingStatus, setFilterProcessingStatus] = useState<ProcessingStatus | ''>('')
  const [filterLocation, setFilterLocation] = useState('')
  const [filterRemote, setFilterRemote] = useState<boolean | ''>('')
  const [filterVisa, setFilterVisa] = useState<boolean | ''>('')

  const searchParams: JobSearchQuery = useMemo(() => ({
    page: page + 1,
    page_size: PAGE_SIZE,
    query: query || undefined,
    processing_status: (filterProcessingStatus as ProcessingStatus) || undefined,
    location: filterLocation || undefined,
    remote: filterRemote === '' ? undefined : (filterRemote as boolean),
    visa: filterVisa === '' ? undefined : (filterVisa as boolean),
    sort: sort || undefined,
    order: order || undefined,
  }), [page, query, sort, order, filterProcessingStatus, filterLocation, filterRemote, filterVisa])

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: [JOBS_KEY, searchParams],
    queryFn: () => jobApi.search(searchParams),
  })

  const total = data?.pagination?.total_items ?? 0
  const items = data?.items ?? []

  const hasNextPage = (page + 1) * PAGE_SIZE < total

  const loadNextPage = useCallback(() => {
    if (hasNextPage) setPage(p => p + 1)
  }, [hasNextPage])

  const resetPage = useCallback(() => setPage(0), [])

  const toggleOrder = useCallback(() => {
    setOrder(o => o === 'desc' ? 'asc' : 'desc')
    resetPage()
  }, [resetPage])

  const setSortAndReset = useCallback((newSort: string) => {
    setSort(newSort)
    resetPage()
  }, [resetPage])

  const activeFilterCount = [
    filterProcessingStatus,
    filterLocation,
    filterRemote !== '',
    filterVisa !== '',
  ].filter(Boolean).length

  const clearFilters = useCallback(() => {
    setFilterProcessingStatus('')
    setFilterLocation('')
    setFilterRemote('')
    setFilterVisa('')
    resetPage()
  }, [resetPage])

  const processMutation = useMutation({
    mutationFn: (jobId: string) => jobApi.processJob(jobId),
    onMutate: async (jobId) => {
      await queryClient.cancelQueries({ queryKey: [JOBS_KEY] })
      const previousData = queryClient.getQueriesData<{ items: JobListItem[] }>({ queryKey: [JOBS_KEY] })
      queryClient.setQueriesData<{ items: JobListItem[] }>(
        { queryKey: [JOBS_KEY] },
        (old) => {
          if (!old) return old
          return {
            ...old,
            items: old.items.map((item) =>
              item.id === jobId
                ? {
                    ...item,
                    latest_processing_execution: {
                      id: 'optimistic',
                      status: 'queued' as ProcessingStatus,
                      started_at: new Date().toISOString(),
                      finished_at: null,
                    },
                  }
                : item
            ),
          }
        }
      )
      return { previousData }
    },
    onError: (_err, jobId, context) => {
      if (context?.previousData) {
        for (const [key, data] of context.previousData) {
          queryClient.setQueryData(key, data)
        }
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: [JOBS_KEY] })
    },
  })

  return {
    items, total, isLoading, isError, error, refetch,
    page, setPage: resetPage,
    query, setQuery: (v: string) => { setQuery(v); resetPage() },
    sort, setSort: setSortAndReset,
    order, toggleOrder, hasNextPage, loadNextPage,
    filterProcessingStatus, setFilterProcessingStatus: (v: ProcessingStatus | '') => { setFilterProcessingStatus(v); resetPage() },
    filterLocation, setFilterLocation: (v: string) => { setFilterLocation(v); resetPage() },
    filterRemote, setFilterRemote: (v: boolean | '') => { setFilterRemote(v); resetPage() },
    filterVisa, setFilterVisa: (v: boolean | '') => { setFilterVisa(v); resetPage() },
    activeFilterCount, clearFilters,
    processMutation,
  }
}
