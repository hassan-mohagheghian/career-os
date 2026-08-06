'use client'

import { DebouncedInput } from '@/shared/ui/debounced-input'
import { Button } from '@/shared/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger } from '@/shared/ui/select'
import { SKILL_CATEGORIES } from '@/entities/skill/types'
import { MagnifyingGlass, FunnelSimple } from '@phosphor-icons/react'

interface SkillsToolbarProps {
  query: string
  onQueryChange: (value: string) => void
  filterCategory: string
  onFilterCategoryChange: (value: string) => void
  activeFilterCount: number
  onClearFilters: () => void
}

export function SkillsToolbar({
  query,
  onQueryChange,
  filterCategory,
  onFilterCategoryChange,
  activeFilterCount,
  onClearFilters,
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
            <SelectTrigger className="h-7 w-auto text-2xs gap-1">
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
