'use client'

import { useState, useMemo, useCallback } from 'react'
import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { companyApi } from './api'
import type {
  CompanyDetail,
  CompanyEditInput,
  InfiniteCompanySearchResult,
} from './types'

const PAGE_SIZE = 25
const COMPANIES_KEY = 'companies-v2-infinite'
const COMPANY_DETAIL_KEY = 'company-detail'

export function useCompaniesInfiniteQuery() {
  const queryClient = useQueryClient()
  const [query, setQuery] = useState('')
  const [sortState, setSortState] = useState<{ sort: string; order: 'asc' | 'desc' }>({
    sort: 'created_at',
    order: 'desc',
  })
  const { sort, order } = sortState
  const [filterIndustry, setFilterIndustry] = useState('')
  const [filterPinned, setFilterPinned] = useState(false)

  const filterKey = useMemo(
    () => ({
      query,
      sort,
      order,
      industry: filterIndustry || undefined,
      pinned: filterPinned || undefined,
    }),
    [query, sort, order, filterIndustry, filterPinned]
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
  } = useInfiniteQuery<InfiniteCompanySearchResult>({
    queryKey: [COMPANIES_KEY, filterKey],
    queryFn: ({ pageParam }) =>
      companyApi.listInfinite({
        page_size: PAGE_SIZE,
        cursor: pageParam as string | undefined,
        query: filterKey.query || undefined,
        industry: filterKey.industry,
        pinned: filterKey.pinned,
        sort: filterKey.sort,
        order: filterKey.order as 'asc' | 'desc',
      }),
    initialPageParam: undefined,
    getNextPageParam: (lastPage) => (lastPage.has_more ? lastPage.next_cursor : undefined),
  })

  const items = useMemo(() => data?.pages.flatMap((p) => p.items) ?? [], [data])
  const total = data?.pages[0]?.total_items ?? 0
  const loadedCount = items.length

  const activeFilterCount = [query, filterIndustry, filterPinned].filter(Boolean).length

  const clearFilters = useCallback(() => {
    setQuery('')
    setFilterIndustry('')
    setFilterPinned(false)
  }, [])

  const handleHeaderSort = useCallback((field: string) => {
    setSortState((prev) => {
      if (prev.sort === field) {
        return { sort: field, order: prev.order === 'desc' ? 'asc' : 'desc' }
      }
      return { sort: field, order: 'desc' }
    })
  }, [])

  const deleteMutation = useMutation({
    mutationFn: (id: string) => companyApi.delete(id),
    onSettled: () => queryClient.invalidateQueries({ queryKey: [COMPANIES_KEY] }),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: CompanyEditInput }) => companyApi.update(id, data),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: [COMPANIES_KEY] })
      queryClient.invalidateQueries({ queryKey: [COMPANY_DETAIL_KEY] })
    },
  })

  const reprocessMutation = useMutation({
    mutationFn: (id: string) => companyApi.reprocess(id),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: [COMPANIES_KEY] })
      queryClient.invalidateQueries({ queryKey: [COMPANY_DETAIL_KEY] })
    },
  })

  const setMainMutation = useMutation({
    mutationFn: ({ id, mainCompanyId }: { id: string; mainCompanyId: string | null }) =>
      companyApi.setMain(id, mainCompanyId),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: [COMPANIES_KEY] })
      queryClient.invalidateQueries({ queryKey: [COMPANY_DETAIL_KEY] })
    },
  })

  const pinnedMutation = useMutation({
    mutationFn: ({ id, pinned }: { id: string; pinned: boolean }) => companyApi.setPinned(id, pinned),
    onMutate: async ({ id, pinned }) => {
      await queryClient.cancelQueries({ queryKey: [COMPANIES_KEY] })
      const previousData = queryClient.getQueriesData<{ pages: { items: CompanyDetail[] }[] }>({ queryKey: [COMPANIES_KEY] })
      queryClient.setQueriesData<{ pages: { items: CompanyDetail[] }[] }>(
        { queryKey: [COMPANIES_KEY] },
        (old) => {
          if (!old) return old
          return {
            ...old,
            pages: old.pages.map((page) => ({
              ...page,
              items: page.items.map((item) =>
                item.id === id ? { ...item, pinned } : item
              ),
            })),
          }
        }
      )
      return previousData
    },
    onError: (_err, _vars, context) => {
      if (context) queryClient.setQueriesData({ queryKey: [COMPANIES_KEY] }, context)
    },
  })

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
    filterIndustry,
    setFilterIndustry: useCallback((v: string) => setFilterIndustry(v), []),
    filterPinned,
    setFilterPinned: useCallback((v: boolean) => setFilterPinned(v), []),
    activeFilterCount,
    clearFilters,
    deleteMutation,
    updateMutation,
    reprocessMutation,
    setMainMutation,
    pinnedMutation,
  }
}

export function useCompanyQuery(id: number | string | null) {
  return useQuery<CompanyDetail>({
    queryKey: [COMPANY_DETAIL_KEY, id],
    queryFn: () => companyApi.get(id as string),
    enabled: !!id,
  })
}
