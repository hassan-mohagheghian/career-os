'use client'

import { useState, useMemo, useCallback } from 'react'
import { useInfiniteQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { skillApi } from './api'
import type { InfiniteSkillSearchResult, SkillCreateInput, SkillUpdateInput } from './types'

const PAGE_SIZE = 25
const SKILLS_KEY = 'skills-v2-infinite'

export function useSkillsInfiniteQuery() {
  const queryClient = useQueryClient()
  const [query, setQuery] = useState('')
  const [sortState, setSortState] = useState<{ sort: string; order: 'asc' | 'desc' }>({
    sort: 'created_at',
    order: 'desc',
  })
  const { sort, order } = sortState
  const [filterCategory, setFilterCategory] = useState('')

  const filterKey = useMemo(
    () => ({
      query,
      sort,
      order,
      category: filterCategory || undefined,
    }),
    [query, sort, order, filterCategory]
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
  } = useInfiniteQuery<InfiniteSkillSearchResult>({
    queryKey: [SKILLS_KEY, filterKey],
    queryFn: ({ pageParam }) =>
      skillApi.listInfinite({
        page_size: PAGE_SIZE,
        cursor: pageParam as string | undefined,
        query: filterKey.query || undefined,
        category: filterKey.category,
        sort: filterKey.sort,
        order: filterKey.order as 'asc' | 'desc',
      }),
    initialPageParam: undefined,
    getNextPageParam: (lastPage) => (lastPage.has_more ? lastPage.next_cursor : undefined),
  })

  const items = useMemo(() => data?.pages.flatMap((p) => p.items) ?? [], [data])
  const total = data?.pages[0]?.total_items ?? 0
  const loadedCount = items.length

  const activeFilterCount = [query, filterCategory].filter(Boolean).length

  const clearFilters = useCallback(() => {
    setQuery('')
    setFilterCategory('')
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
    mutationFn: (id: number | string) => skillApi.delete(id),
    onSettled: () => queryClient.invalidateQueries({ queryKey: [SKILLS_KEY] }),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number | string; data: SkillUpdateInput }) => skillApi.update(id, data),
    onSettled: () => queryClient.invalidateQueries({ queryKey: [SKILLS_KEY] }),
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
    filterCategory,
    setFilterCategory: useCallback((v: string) => setFilterCategory(v), []),
    activeFilterCount,
    clearFilters,
    deleteMutation,
    updateMutation,
  }
}

export function useCreateSkill() {
  const queryClient = useQueryClient()
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const mutation = useMutation({
    mutationFn: (data: SkillCreateInput) => skillApi.create(data),
    onError: (e: unknown) => {
      setError((e as { message?: string })?.message || 'Failed to add skill')
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: [SKILLS_KEY] })
    },
  })

  const createSkill = async (data: SkillCreateInput): Promise<boolean> => {
    setSubmitting(true)
    setError(null)
    try {
      await mutation.mutateAsync(data)
      return true
    } catch {
      return false
    } finally {
      setSubmitting(false)
    }
  }

  const clearError = () => setError(null)

  return { createSkill, submitting, error, clearError }
}
