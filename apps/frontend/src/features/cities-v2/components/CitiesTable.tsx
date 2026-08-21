'use client'

import { useEffect, useRef } from 'react'
import type { CityListItem } from '@/entities/city/types'
import { SortableHeader } from '@/features/jobs-v2/components/SortableHeader'
import { CityRow } from './CityRow'

interface CitiesTableProps {
  items: CityListItem[]
  total: number
  loadedCount: number
  isLoading: boolean
  isFetchingNextPage: boolean
  hasNextPage: boolean
  onFetchNextPage: () => void
  sort: string
  order: 'asc' | 'desc'
  onSortChange: (field: string) => void
  onOpenEdit: (city: CityListItem) => void
  onMerge: (city: CityListItem) => void
}

export function CitiesTable({
  items, total, loadedCount, isLoading, isFetchingNextPage, hasNextPage,
  onFetchNextPage, sort, order, onSortChange, onOpenEdit, onMerge,
}: CitiesTableProps) {
  const sentinelRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const el = sentinelRef.current
    if (!el) return
    const observer = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting && hasNextPage && !isFetchingNextPage) {
        onFetchNextPage()
      }
    })
    observer.observe(el)
    return () => observer.disconnect()
  }, [hasNextPage, isFetchingNextPage, onFetchNextPage])

  if (isLoading && items.length === 0) {
    return <div className="flex-1 flex items-center justify-center text-2xs text-muted-foreground p-6">Loading cities…</div>
  }

  if (items.length === 0) {
    return <div className="flex-1 flex items-center justify-center text-2xs text-muted-foreground p-6">No cities yet</div>
  }

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="flex items-center px-3 py-2 border-b border-border/40">
        <div className="flex-1 flex items-center gap-2">
          <SortableHeader label="City" field="city" sort={sort} order={order} onSortChange={onSortChange} />
          <SortableHeader label="Country" field="country" sort={sort} order={order} onSortChange={onSortChange} />
        </div>
        <div className="w-32 shrink-0 text-right">
          <SortableHeader label="Jobs" field="jobs" sort={sort} order={order} onSortChange={onSortChange} />
        </div>
        <div className="w-40 shrink-0 hidden lg:block text-right">
          <span className="text-2xs font-medium uppercase tracking-wider text-muted-foreground">Original</span>
        </div>
      </div>
      {items.map((city) => (
        <CityRow key={city.id} city={city} onOpenEdit={onOpenEdit} onMerge={onMerge} />
      ))}
      {hasNextPage && (
        <div ref={sentinelRef} className="flex items-center justify-center py-3 text-2xs text-muted-foreground">
          {isFetchingNextPage ? 'Loading more…' : 'Scroll to load more'}
        </div>
      )}
    </div>
  )
}