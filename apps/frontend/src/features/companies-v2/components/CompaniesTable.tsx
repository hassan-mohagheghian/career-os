import { useRef, useCallback, useEffect } from 'react'
import { useVirtualizer } from '@tanstack/react-virtual'
import type { CompanyListItem } from '@/entities/company/types'
import { CompanyRow } from './CompanyRow'
import { SortableHeader, type ScoreSortOption } from '@/features/jobs-v2/components/SortableHeader'
import { COMPANY_GRID_TEMPLATE } from './companiesColumns'

const ESTIMATED_ROW_HEIGHT = 40

interface CompaniesTableProps {
  items: CompanyListItem[]
  total: number
  loadedCount?: number
  isLoading: boolean
  isFetchingNextPage?: boolean
  hasNextPage?: boolean
  onFetchNextPage?: () => void
  onViewDetails: (id: string) => void
  onReprocess: (id: string) => void
  onEdit: (id: string) => void
  onDelete: (id: string) => void
  sort?: string
  order?: 'asc' | 'desc'
  onSortChange?: (field: string) => void
}

const SCORE_SORT_OPTIONS: ScoreSortOption[] = [
  { field: 'overall_score', label: 'Overall' },
  { field: 'fit_score', label: 'Fit' },
  { field: 'success_score', label: 'Success' },
]

interface ColumnDef {
  label: string
  field?: string
  scoreOptions?: ScoreSortOption[]
}

const COLUMN_DEFS: ColumnDef[] = [
  { label: 'Name', field: 'name' },
  { label: 'Industry' },
  { label: 'Location' },
  { label: 'Size' },
  { label: 'Jobs' },
  { label: 'Scores', scoreOptions: SCORE_SORT_OPTIONS },
  { label: 'Status' },
  { label: 'Updated', field: 'updated_at' },
  { label: 'Created', field: 'created_at' },
  { label: 'Actions' },
]

const gridStyle = { gridTemplateColumns: COMPANY_GRID_TEMPLATE }

export function CompaniesTable({
  items, total, loadedCount = 0, isLoading, isFetchingNextPage = false, hasNextPage = false, onFetchNextPage = () => {},
  onViewDetails, onReprocess, onEdit, onDelete,
  sort = 'created_at', order = 'desc', onSortChange = () => {},
}: CompaniesTableProps) {
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
          <div className="sticky top-0 z-10 bg-card grid border-b border-border/40" style={gridStyle}>
            {COLUMN_DEFS.map((col, i) => (
              <div key={col.label} className={`py-2 px-3 flex items-center ${i === COLUMN_DEFS.length - 1 ? 'justify-end' : ''}`}>
                <SortableHeader
                  label={col.label}
                  field={col.field}
                  scoreOptions={col.scoreOptions}
                  sort={sort}
                  order={order}
                  onSortChange={onSortChange}
                />
              </div>
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
                  gridTemplateColumns: COMPANY_GRID_TEMPLATE,
                }}
                className="grid border-b border-border/40"
              >
                {COLUMN_DEFS.map((_, j) => (
                  <div key={j} className="py-2 px-3">
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
          <p className="text-sm text-muted-foreground">No companies have been processed yet.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto" ref={scrollRef}>
      <div className="w-full">
        <div className="sticky top-0 z-10 bg-card grid border-b border-border/40" style={gridStyle}>
          {COLUMN_DEFS.map((col, i) => (
            <div key={col.label} className={`py-2 px-3 flex items-center ${i === COLUMN_DEFS.length - 1 ? 'justify-end' : ''}`}>
              <SortableHeader
                label={col.label}
                field={col.field}
                scoreOptions={col.scoreOptions}
                sort={sort}
                order={order}
                onSortChange={onSortChange}
              />
            </div>
          ))}
        </div>
        <div style={{ height: virtualizer.getTotalSize(), position: 'relative' }}>
          {virtualizer.getVirtualItems().map(virtualItem => {
            const company = items[virtualItem.index]
            if (!company) return null
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
                <CompanyRow
                  company={company}
                  onViewDetails={onViewDetails}
                  onReprocess={onReprocess}
                  onEdit={onEdit}
                  onDelete={onDelete}
                />
              </div>
            )
          })}
        </div>
        <div ref={sentinelRef} className="h-4" />
        <div className="px-3 py-3 text-center">
          {isFetchingNextPage && (
            <p className="text-xs text-muted-foreground animate-pulse">Loading more companies...</p>
          )}
          {!hasNextPage && !isFetchingNextPage && items.length > 0 && (
            <div className="text-xs text-muted-foreground">
              <p>You've reached the end</p>
              <p>{total} companies loaded</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
