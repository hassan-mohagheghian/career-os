import { useRef, useCallback, useEffect } from 'react'
import { useVirtualizer } from '@tanstack/react-virtual'
import type { SkillListItem } from '@/entities/skill/types'
import { SkillRow } from './SkillRow'
import { SortableHeader } from '@/features/jobs-v2/components/SortableHeader'
import { SKILL_GRID_TEMPLATE, SKILL_GRID_TEMPLATE_WITH_PIN } from './skillsColumns'

const ESTIMATED_ROW_HEIGHT = 40

interface ColumnDef {
  label: string
  field?: string
}

const PIN_COLUMN: ColumnDef = { label: 'Pin' }

const COLUMN_DEFS: ColumnDef[] = [
  { label: 'Name', field: 'name' },
  { label: 'Category', field: 'category' },
  { label: 'Level', field: 'level' },
  { label: 'Roles' },
  { label: 'Demand', field: 'market_relevance' },
  { label: 'Confidence', field: 'confidence' },
  { label: 'Created', field: 'created_at' },
  { label: 'Mentions', field: 'mention_count' },
  { label: 'Actions' },
]

const gridStyle = { gridTemplateColumns: SKILL_GRID_TEMPLATE }

interface SkillsTableProps {
  items: SkillListItem[]
  total: number
  loadedCount?: number
  isLoading: boolean
  isFetchingNextPage?: boolean
  hasNextPage?: boolean
  onFetchNextPage?: () => void
  onViewDetails: (id: number) => void
  onEdit: (id: number) => void
  onDelete: (id: number) => void
  onTogglePinned?: (id: number, pinned: boolean) => void
  showPinnedColumn?: boolean
  sort?: string
  order?: 'asc' | 'desc'
  onSortChange?: (field: string) => void
}

export function SkillsTable({
  items, total, loadedCount = 0, isLoading, isFetchingNextPage = false, hasNextPage = false, onFetchNextPage = () => {},
  onViewDetails, onEdit, onDelete, onTogglePinned, showPinnedColumn = true,
  sort = 'created_at', order = 'desc', onSortChange = () => {},
}: SkillsTableProps) {
  const scrollRef = useRef<HTMLDivElement>(null)

  const rowCount = isLoading ? 8 : items.length

  const visibleColumnDefs = showPinnedColumn ? [PIN_COLUMN, ...COLUMN_DEFS] : COLUMN_DEFS
  const gridStyle = { gridTemplateColumns: showPinnedColumn ? SKILL_GRID_TEMPLATE_WITH_PIN : SKILL_GRID_TEMPLATE }

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

  const renderHeader = () => (
    <div className="sticky top-0 z-10 bg-card grid border-b border-border/40" style={gridStyle}>
      {visibleColumnDefs.map((col, i) => (
        <div key={col.label} className={`py-2 px-3 flex items-center ${i === visibleColumnDefs.length - 1 ? 'justify-end' : ''}`}>
          <SortableHeader
            label={col.label}
            field={col.field}
            sort={sort}
            order={order}
            onSortChange={onSortChange}
          />
        </div>
      ))}
    </div>
  )

  if (isLoading) {
    return (
      <div className="flex-1 overflow-y-auto" ref={scrollRef}>
        <div className="w-full">
          {renderHeader()}
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
                  gridTemplateColumns: gridStyle.gridTemplateColumns,
                }}
                className="grid border-b border-border/40"
              >
                {visibleColumnDefs.map((_, j) => (
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
          <p className="text-sm text-muted-foreground">No skills yet. Add one or run an AI analysis.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto" ref={scrollRef}>
      <div className="w-full">
        {renderHeader()}
        <div style={{ height: virtualizer.getTotalSize(), position: 'relative' }}>
          {virtualizer.getVirtualItems().map(virtualItem => {
            const skill = items[virtualItem.index]
            if (!skill) return null
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
                <SkillRow
                  skill={skill}
                  onViewDetails={onViewDetails}
                  onEdit={onEdit}
                  onDelete={onDelete}
                  onTogglePinned={onTogglePinned}
                  showPinnedColumn={showPinnedColumn}
                />
              </div>
            )
          })}
        </div>
        <div ref={sentinelRef} className="h-4" />
        <div className="px-3 py-3 text-center">
          {isFetchingNextPage && (
            <p className="text-xs text-muted-foreground animate-pulse">Loading more skills...</p>
          )}
          {!hasNextPage && !isFetchingNextPage && items.length > 0 && (
            <div className="text-xs text-muted-foreground">
              <p>You've reached the end</p>
              <p>{total} skills loaded</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
