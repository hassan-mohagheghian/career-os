'use client'

import { DebouncedInput } from '@/shared/ui/debounced-input'
import { Button } from '@/shared/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger } from '@/shared/ui/select'
import { SKILL_CATEGORIES } from '@/entities/skill/types'
import { MagnifyingGlass, FunnelSimple, PushPin } from '@phosphor-icons/react'
import { ColumnsDropdown } from '@/shared/components/ColumnsDropdown'
import { cn } from '@/shared/lib/utils'

interface SkillsToolbarProps {
  query: string
  onQueryChange: (value: string) => void
  filterCategory: string
  onFilterCategoryChange: (value: string) => void
  filterPinned?: boolean
  onFilterPinnedChange?: (value: boolean) => void
  activeFilterCount: number
  onClearFilters: () => void
  showPinnedColumn?: boolean
  onTogglePinnedColumn?: (value: boolean) => void
}

export function SkillsToolbar({
  query,
  onQueryChange,
  filterCategory,
  onFilterCategoryChange,
  filterPinned = false,
  onFilterPinnedChange,
  activeFilterCount,
  onClearFilters,
  showPinnedColumn = true,
  onTogglePinnedColumn,
}: SkillsToolbarProps) {
  return (
    <div className="px-3 py-2 border-b border-border/40">
      <div className="flex items-center gap-2">
        <div className="relative flex-1 max-w-sm">
          <DebouncedInput
            value={query}
            onValueChange={onQueryChange}
            placeholder="Search by name, role, path, or alias..."
            icon={<MagnifyingGlass className="w-3.5 h-3.5 text-muted-foreground" />}
            clearable
            clearLabel="Clear search"
            activeClassName="border-emerald-500/30"
            wrapperClassName="w-full"
            inputClassName="pl-8 h-7 text-xs"
            aria-label="Search skills"
          />
        </div>
        <div className="flex items-center gap-1.5">
          <Select value={filterCategory} onValueChange={onFilterCategoryChange}>
            <SelectTrigger className="h-7 w-auto text-2xs gap-1 text-primary">
              <FunnelSimple className="w-3 h-3" />
              <span>{filterCategory || 'Category'}</span>
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">All</SelectItem>
              {SKILL_CATEGORIES.map((cat) => (
                <SelectItem key={cat} value={cat}>{cat}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          {onFilterPinnedChange && (
            <Button
              variant="ghost"
              size="sm"
              className={cn('h-7 w-auto gap-1 text-2xs', filterPinned && 'text-primary')}
              onClick={() => onFilterPinnedChange(!filterPinned)}
              aria-label="Show pinned skills only"
              aria-pressed={filterPinned}
              title={filterPinned ? 'Showing pinned skills only' : 'Show pinned skills only'}
            >
              <PushPin className="w-3 h-3" weight={filterPinned ? 'fill' : 'regular'} />
              Pinned
            </Button>
          )}
          {onTogglePinnedColumn && (
            <ColumnsDropdown
              options={[{ key: 'pinned', label: 'Pinned', checked: showPinnedColumn }]}
              onToggle={(key, checked) => onTogglePinnedColumn(checked)}
            />
          )}
          {activeFilterCount > 0 && (
            <Button variant="ghost" size="sm" className="h-7 text-2xs text-emerald-500" onClick={onClearFilters}>
              Clear
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}
