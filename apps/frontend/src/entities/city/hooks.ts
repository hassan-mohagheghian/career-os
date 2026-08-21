'use client'

import { useState, useMemo, useCallback } from 'react'
import { useInfiniteQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { cityApi } from './api'
import type { InfiniteCitySearchResult } from './types'

const PAGE_SIZE = 25
const CITIES_KEY = 'cities-infinite'

export function useCitiesInfiniteQuery() {
  const [query, setQuery] = useState('')
  const [sortState, setSortState] = useState<{ sort: 'jobs' | 'country' | 'city'; order: 'asc' | 'desc' }>({
    sort: 'jobs',
    order: 'desc',
  })
  const { sort, order } = sortState

  const filterKey = useMemo(
    () => ({ query, sort, order }),
    [query, sort, order]
  )

  const {
    data,
    isLoading,
    isError,
    error,
    refetch,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isRefetching,
  } = useInfiniteQuery<InfiniteCitySearchResult>({
    queryKey: [CITIES_KEY, filterKey],
    queryFn: ({ pageParam }) =>
      cityApi.listInfinite({
        page_size: PAGE_SIZE,
        cursor: pageParam as string | undefined,
        query: filterKey.query || undefined,
        sort: filterKey.sort,
        order: filterKey.order,
      }),
    initialPageParam: undefined,
    getNextPageParam: (lastPage) => (lastPage.has_more ? lastPage.next_cursor : undefined),
  })

  const items = useMemo(() => data?.pages.flatMap((p) => p.items) ?? [], [data])
  const total = data?.pages[0]?.total_items ?? 0
  const loadedCount = items.length

  const handleHeaderSort = useCallback((field: string) => {
    if (field !== 'jobs' && field !== 'country' && field !== 'city') return
    setSortState((prev) => {
      if (prev.sort === field) {
        return { sort: field, order: prev.order === 'desc' ? 'asc' : 'desc' }
      }
      return { sort: field, order: 'desc' }
    })
  }, [])

  return {
    items,
    total,
    loadedCount,
    isLoading,
    isFetchingNextPage,
    isRefetching,
    hasNextPage: !!hasNextPage,
    fetchNextPage,
    isError,
    error,
    refetch,
    query,
    setQuery: useCallback((v: string) => setQuery(v), []),
    sort,
    order,
    handleHeaderSort,
  }
}

function useInvalidateCities() {
  const queryClient = useQueryClient()
  return useCallback(() => {
    queryClient.invalidateQueries({ queryKey: [CITIES_KEY] })
  }, [queryClient])
}

export function useMergeCities() {
  const invalidate = useInvalidateCities()
  return useMutation({
    mutationFn: ({ targetId, sourceIds }: { targetId: string; sourceIds: string[] }) =>
      cityApi.merge(targetId, sourceIds),
    onSettled: invalidate,
  })
}

export function useAddCityAlias() {
  const invalidate = useInvalidateCities()
  return useMutation({
    mutationFn: ({ cityId, aliasName }: { cityId: string; aliasName: string }) =>
      cityApi.addAlias(cityId, aliasName),
    onSettled: invalidate,
  })
}

export function useRemoveCityAlias() {
  const invalidate = useInvalidateCities()
  return useMutation({
    mutationFn: ({ cityId, aliasName }: { cityId: string; aliasName: string }) =>
      cityApi.removeAlias(cityId, aliasName),
    onSettled: invalidate,
  })
}

export function usePromoteCityCanonical() {
  const invalidate = useInvalidateCities()
  return useMutation({
    mutationFn: ({ cityId, aliasName }: { cityId: string; aliasName: string }) =>
      cityApi.promoteAliasToCanonical(cityId, aliasName),
    onSettled: invalidate,
  })
}