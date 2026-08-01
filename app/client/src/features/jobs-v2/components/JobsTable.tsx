import { useRef, useCallback, useEffect } from 'react'
import { useVirtualizer } from '@tanstack/react-virtual'
import type { JobListItem } from '@/entities/job/types'
import { JobRow } from './JobRow'

const ESTIMATED_ROW_HEIGHT = 40

interface JobsTableProps {
  items: JobListItem[]
  total: number
  loadedCount?: number
  isLoading: boolean
  isFetchingNextPage?: boolean
  hasNextPage?: boolean
  onFetchNextPage?: () => void
  onProcessV2: (id: string) => void
  onLegacyProcess: (id: string) => void
  onViewDetails: (id: string) => void
  onRetry?: (id: string) => void
  onCancel?: (id: string) => void
}

const TABLE_HEADERS = ['Title', 'Company', 'Location', 'Scores', 'Status', 'Updated', 'Actions']

export function JobsTable({
  items, total, loadedCount = 0, isLoading, isFetchingNextPage = false, hasNextPage = false, onFetchNextPage = () => {},
  onProcessV2, onLegacyProcess, onViewDetails, onRetry, onCancel,
}: JobsTableProps) {
  const scrollRef = useRef<HTMLDivElement>(null)

  const rowCount = isLoading ? 8 : items.length

  const virtualizer = useVirtualizer({
    count: rowCount,
    getScrollElement: () => scrollRef.current,
    estimateSize: () => ESTIMATED_ROW_HEIGHT,
    overscan: 10,
  })

  const sentinelRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const sentinel = sentinelRef.current
    if (!sentinel || !hasNextPage) return

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting && hasNextPage && !isFetchingNextPage) {
          onFetchNextPage()
        }
      },
      { rootMargin: '200px' }
    )

    observer.observe(sentinel)
    return () => observer.disconnect()
  }, [hasNextPage, isFetchingNextPage, onFetchNextPage])

  if (isLoading) {
    return (
      <div className="flex-1 overflow-y-auto" ref={scrollRef}>
        <div className="w-full">
          <div className="sticky top-0 z-10 bg-card flex border-b border-border/40">
            {TABLE_HEADERS.map(h => (
              <div key={h} className="flex-1 py-2 px-3 text-2xs font-medium text-muted-foreground uppercase tracking-wider">{h}</div>
            ))}
          </div>
          <div style={{ height: virtualizer.getTotalSize(), position: 'relative' }}>
            {virtualizer.getVirtualItems().map(virtualItem => (
              <div
                key={virtualItem.key}
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: virtualItem.size,
                  transform: `translateY(${virtualItem.start}px)`,
                }}
                className="flex border-b border-border/40"
              >
                {TABLE_HEADERS.map((_, j) => (
                  <div key={j} className="flex-1 py-3 px-3">
                    <div className="h-3 bg-muted rounded animate-pulse" style={{ width: `${50 + Math.random() * 40}%` }} />
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (!isLoading && items.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <p className="text-sm text-muted-foreground">No jobs have been imported yet.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto" ref={scrollRef}>
      <div className="w-full">
        <div className="sticky top-0 z-10 bg-card flex border-b border-border/40">
          {TABLE_HEADERS.map(h => (
            <div key={h} className="flex-1 py-2 px-3 text-2xs font-medium text-muted-foreground uppercase tracking-wider">{h}</div>
          ))}
        </div>
        <div style={{ height: virtualizer.getTotalSize(), position: 'relative' }}>
          {virtualizer.getVirtualItems().map(virtualItem => {
            const job = items[virtualItem.index]
            if (!job) return null
            return (
              <div
                key={virtualItem.key}
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: virtualItem.size,
                  transform: `translateY(${virtualItem.start}px)`,
                }}
              >
                <JobRow
                  job={job}
                  onProcessV2={onProcessV2}
                  onLegacyProcess={onLegacyProcess}
                  onViewDetails={onViewDetails}
                  onRetry={onRetry}
                  onCancel={onCancel}
                />
              </div>
            )
          })}
        </div>
        <div ref={sentinelRef} className="h-4" />
        <div className="px-3 py-3 text-center">
          {isFetchingNextPage && (
            <p className="text-xs text-muted-foreground animate-pulse">Loading more jobs...</p>
          )}
          {!hasNextPage && !isFetchingNextPage && items.length > 0 && (
            <div className="text-xs text-muted-foreground">
              <p>You've reached the end</p>
              <p>{total} jobs loaded</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
