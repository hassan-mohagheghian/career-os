'use client'

import { useMemo } from 'react'
import { DebouncedInput } from '@/shared/ui/debounced-input'
import { Button } from '@/shared/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger } from '@/shared/ui/select'
import type { CompanyListItem } from '@/entities/company/types'
import { MagnifyingGlass, Buildings } from '@phosphor-icons/react'

interface CompaniesToolbarProps {
  query: string
  onQueryChange: (value: string) => void
  filterIndustry: string
  onFilterIndustryChange: (value: string) => void
  items: CompanyListItem[]
  activeFilterCount: number
  onClearFilters: () => void
}

export function CompaniesToolbar({
  query, onQueryChange,
  filterIndustry, onFilterIndustryChange,
  items, activeFilterCount, onClearFilters,
}: CompaniesToolbarProps) {
  const industries = useMemo(() => {
    const set = new Set<string>()
    items.forEach(c => {
      if (c.industry) set.add(c.industry)
    })
    return [...set].sort()
  }, [items])

  return (
    <div className="px-3 py-2 border-b border-border/40">
      <div className="flex items-center gap-2">
        <div className="relative flex-1 max-w-sm">
          <DebouncedInput
            value={query}
            onValueChange={onQueryChange}
            placeholder="Search by name, industry, or location..."
            icon={<MagnifyingGlass className="w-3.5 h-3.5 text-muted-foreground" />}
            clearable
            clearLabel="Clear search"
            activeClassName="border-emerald-500/30"
            wrapperClassName="w-full"
            inputClassName="pl-8 h-7 text-xs"
            aria-label="Search companies"
          />
        </div>
        <div className="flex items-center gap-1.5">
          <Select value={filterIndustry} onValueChange={onFilterIndustryChange}>
            <SelectTrigger className="h-7 w-auto text-2xs gap-1">
              <Buildings className="w-3 h-3" />
              <span>{filterIndustry || 'Industry'}</span>
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">All</SelectItem>
              {industries.map(ind => (
                <SelectItem key={ind} value={ind}>{ind}</SelectItem>
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
