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

  const filterKey = useMemo(
    () => ({
      query,
      sort,
      order,
      industry: filterIndustry || undefined,
    }),
    [query, sort, order, filterIndustry]
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
  } = useInfiniteQuery<InfiniteCompanySearchResult>({
    queryKey: [COMPANIES_KEY, filterKey],
    queryFn: ({ pageParam }) =>
      companyApi.listInfinite({
        page_size: PAGE_SIZE,
        cursor: pageParam as string | undefined,
        query: filterKey.query || undefined,
        industry: filterKey.industry,
        sort: filterKey.sort,
        order: filterKey.order as 'asc' | 'desc',
      }),
    initialPageParam: undefined,
    getNextPageParam: (lastPage) => (lastPage.has_more ? lastPage.next_cursor : undefined),
  })

  const items = useMemo(() => data?.pages.flatMap((p) => p.items) ?? [], [data])
  const total = data?.pages[0]?.total_items ?? 0
  const loadedCount = items.length

  const activeFilterCount = [query, filterIndustry].filter(Boolean).length

  const clearFilters = useCallback(() => {
    setQuery('')
    setFilterIndustry('')
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

  return {
    items,
    total,
    loadedCount,
    isLoading,
    isFetchingNextPage,
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
    activeFilterCount,
    clearFilters,
    deleteMutation,
    updateMutation,
    reprocessMutation,
    setMainMutation,
  }
}

export function useCompanyQuery(id: number | string | null) {
  return useQuery<CompanyDetail>({
    queryKey: [COMPANY_DETAIL_KEY, id],
    queryFn: () => companyApi.get(id as string),
    enabled: !!id,
  })
}
