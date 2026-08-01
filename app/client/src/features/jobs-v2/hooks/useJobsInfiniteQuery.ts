'use client'

import { useState, useMemo, useCallback } from 'react'
import { useInfiniteQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { jobApi } from '@/entities/job/api'
import type { JobListItem, ProcessingStatus, InfiniteJobSearchResult } from '@/entities/job/types'

const PAGE_SIZE = 30
const JOBS_KEY = 'jobs-v2-infinite'

export function useJobsInfiniteQuery() {
  const queryClient = useQueryClient()
  const [query, setQuery] = useState('')
  const [sort, setSort] = useState('created_at')
  const [order, setOrder] = useState<'asc' | 'desc'>('desc')
  const [filterProcessingStatus, setFilterProcessingStatus] = useState<ProcessingStatus | ''>('')
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
      processing_status: filterKey.processing_status as ProcessingStatus | undefined,
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
    setSort: useCallback((v: string) => { setSort(v) }, []),
    order,
    toggleOrder: useCallback(() => { setOrder(o => o === 'desc' ? 'asc' : 'desc') }, []),
    hasNextPage: !!hasNextPage,
    fetchNextPage,
    filterProcessingStatus,
    setFilterProcessingStatus: useCallback((v: ProcessingStatus | '') => { setFilterProcessingStatus(v) }, []),
    filterLocation,
    setFilterLocation: useCallback((v: string) => { setFilterLocation(v) }, []),
    filterRemote,
    setFilterRemote: useCallback((v: boolean | '') => { setFilterRemote(v) }, []),
    filterVisa,
    setFilterVisa: useCallback((v: boolean | '') => { setFilterVisa(v) }, []),
    activeFilterCount,
    clearFilters,
    processMutation,
  }
}
