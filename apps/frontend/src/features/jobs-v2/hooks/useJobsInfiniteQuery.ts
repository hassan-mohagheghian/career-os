'use client'

import { useState, useMemo, useCallback } from 'react'
import { useInfiniteQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { jobApi } from '@/entities/job/api'
import type { JobListItem, ProcessingStatus, ProcessingStatusFilter, InfiniteJobSearchResult } from '@/entities/job/types'

const PAGE_SIZE = 30
const JOBS_KEY = 'jobs-v2-infinite'

export function useJobsInfiniteQuery() {
  const queryClient = useQueryClient()
  const [query, setQuery] = useState('')
  const [sortState, setSortState] = useState<{ sort: string; order: 'asc' | 'desc' }>({ sort: 'updated_at', order: 'desc' })
  const { sort, order } = sortState
  const [filterProcessingStatus, setFilterProcessingStatus] = useState<ProcessingStatusFilter>('')
  const [filterLocation, setFilterLocation] = useState('')
  const [filterRemote, setFilterRemote] = useState<boolean | ''>('')
  const [filterVisa, setFilterVisa] = useState<boolean | ''>('')

  const filterKey = useMemo(() => ({
    query,
    sort,
    order,
    processing_status: filterProcessingStatus || undefined,
    location: filterLocation || undefined,
    remote: filterRemote === '' ? undefined : filterRemote,
    visa: filterVisa === '' ? undefined : filterVisa,
  }), [query, sort, order, filterProcessingStatus, filterLocation, filterRemote, filterVisa])

  const {
    data,
    isLoading,
    isError,
    error,
    refetch,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery<InfiniteJobSearchResult>({
    queryKey: [JOBS_KEY, filterKey],
    queryFn: ({ pageParam }) => jobApi.searchInfinite({
      page_size: PAGE_SIZE,
      cursor: pageParam as string | undefined,
      query: filterKey.query || undefined,
      sort: filterKey.sort,
      order: filterKey.order as 'asc' | 'desc',
      processing_status: filterKey.processing_status as ProcessingStatus | 'none' | undefined,
      location: filterKey.location as string | undefined,
      remote: filterKey.remote as boolean | undefined,
      visa: filterKey.visa as boolean | undefined,
    }),
    initialPageParam: undefined,
    getNextPageParam: (lastPage) => lastPage.has_more ? lastPage.next_cursor : undefined,
  })

  const items = useMemo(() => {
    return data?.pages.flatMap(p => p.items) ?? []
  }, [data])

  const total = data?.pages[0]?.total_items ?? 0
  const loadedCount = items.length

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
  }, [])

  const handleHeaderSort = useCallback((field: string) => {
    setSortState(prev => {
      if (prev.sort === field) {
        return { sort: field, order: prev.order === 'desc' ? 'asc' : 'desc' }
      }
      return { sort: field, order: 'desc' }
    })
  }, [])
  const processMutation = useMutation({
    mutationFn: (jobId: string) => jobApi.processJob(jobId),
    onMutate: async (jobId) => {
      await queryClient.cancelQueries({ queryKey: [JOBS_KEY] })
      const previousData = queryClient.getQueriesData<{ pages: { items: JobListItem[] }[] }>({ queryKey: [JOBS_KEY] })
      queryClient.setQueriesData<{ pages: { items: JobListItem[] }[] }>(
        { queryKey: [JOBS_KEY] },
        (old) => {
          if (!old) return old
          return {
            ...old,
            pages: old.pages.map(page => ({
              ...page,
              items: page.items.map((item) =>
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
            })),
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

  const deleteMutation = useMutation({
    mutationFn: (jobId: string) => jobApi.deleteJob(jobId),
    onMutate: async (jobId) => {
      await queryClient.cancelQueries({ queryKey: [JOBS_KEY] })
      const previousData = queryClient.getQueriesData<{ pages: { items: JobListItem[]; total_items?: number }[] }>({ queryKey: [JOBS_KEY] })
      queryClient.setQueriesData<{ pages: { items: JobListItem[]; total_items?: number }[] }>(
        { queryKey: [JOBS_KEY] },
        (old) => {
          if (!old) return old
          return {
            ...old,
            pages: old.pages.map(page => ({
              ...page,
              total_items: page.total_items !== undefined ? Math.max(0, page.total_items - 1) : page.total_items,
              items: page.items.filter((item) => item.id !== jobId),
            })),
          }
        }
      )
      return { previousData }
    },
    onError: (_err, _jobId, context) => {
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
    items,
    total,
    loadedCount,
    isLoading,
    isFetchingNextPage,
    isError,
    error,
    refetch,
    query,
    setQuery: useCallback((v: string) => { setQuery(v) }, []),
    sort,
    order,
    handleHeaderSort,
    hasNextPage: !!hasNextPage,
    fetchNextPage,
    filterProcessingStatus,
    setFilterProcessingStatus: useCallback((v: ProcessingStatusFilter) => { setFilterProcessingStatus(v) }, []),
    filterLocation,
    setFilterLocation: useCallback((v: string) => { setFilterLocation(v) }, []),
    filterRemote,
    setFilterRemote: useCallback((v: boolean | '') => { setFilterRemote(v) }, []),
    filterVisa,
    setFilterVisa: useCallback((v: boolean | '') => { setFilterVisa(v) }, []),
    activeFilterCount,
    clearFilters,
    processMutation,
    deleteMutation,
  }
}
