'use client'

import { useState } from 'react'
import type { CityListItem } from '@/entities/city/types'
import { Button } from '@/shared/ui/button'
import { CitiesHeader } from './CitiesHeader'
import { CitiesToolbar } from './CitiesToolbar'
import { CitiesTable } from './CitiesTable'
import { CityEditDrawer } from './CityEditDrawer'
import { MergeCityDialog } from './MergeCityDialog'
import { useMergeCities } from '@/entities/city/hooks'
import { formatCityLocation } from '@/shared/lib/formatLocation'

interface CitiesPageProps {
  items: CityListItem[]
  total: number
  loadedCount: number
  isLoading: boolean
  isFetchingNextPage: boolean
  hasNextPage: boolean
  onFetchNextPage: () => void
  isError: boolean
  error: Error | null
  onRefetch: () => void
  isRefreshing?: boolean
  query: string
  onQueryChange: (value: string) => void
  sort: string
  order: 'asc' | 'desc'
  onSortChange: (field: string) => void
}

export function CitiesPage({
  items, total, loadedCount, isLoading, isFetchingNextPage, hasNextPage, onFetchNextPage,
  isError, error, onRefetch, isRefreshing,
  query, onQueryChange, sort, order, onSortChange,
}: CitiesPageProps) {
  const [editCity, setEditCity] = useState<CityListItem | null>(null)
  const [mergeSource, setMergeSource] = useState<CityListItem | null>(null)
  const mergeMutation = useMergeCities()

  const handleRowMerge = (targetId: string) => {
    if (!mergeSource) return
    mergeMutation.mutateAsync({ targetId, sourceIds: [mergeSource.id] })
    setMergeSource(null)
  }

  if (isError) {
    return (
      <div className="flex flex-col h-full rounded-lg border overflow-hidden bg-card">
        <CitiesHeader total={total} loadedCount={loadedCount} onRefresh={onRefetch} isRefreshing={isRefreshing} />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center space-y-2">
            <p className="text-sm text-red-500">Unable to load cities</p>
            <p className="text-xs text-muted-foreground">{error?.message || 'An unexpected error occurred'}</p>
            <Button variant="outline" size="sm" className="h-7 text-xs" onClick={onRefetch}>
              Retry
            </Button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full rounded-lg border overflow-hidden bg-card">
      <CitiesHeader total={total} loadedCount={loadedCount} onRefresh={onRefetch} isRefreshing={isRefreshing} />
      <CitiesToolbar query={query} onQueryChange={onQueryChange} />
      <CitiesTable
        items={items}
        total={total}
        loadedCount={loadedCount}
        isLoading={isLoading}
        isFetchingNextPage={isFetchingNextPage}
        hasNextPage={hasNextPage}
        onFetchNextPage={onFetchNextPage}
        sort={sort}
        order={order}
        onSortChange={onSortChange}
        onOpenEdit={setEditCity}
        onMerge={setMergeSource}
      />
      <CityEditDrawer city={editCity} onOpenChange={setEditCity} />
      <MergeCityDialog
        sources={mergeSource ? [{ id: mergeSource.id, name: formatCityLocation(mergeSource.city, mergeSource.country) }] : []}
        open={mergeSource != null}
        onOpenChange={(open) => { if (!open) setMergeSource(null) }}
        onMerge={handleRowMerge}
        pending={mergeMutation.isPending}
      />
    </div>
  )
}