'use client'

import { Input } from '@/shared/ui/input'
import { Button } from '@/shared/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger } from '@/shared/ui/select'
import type { ProcessingStatus } from '@/entities/job/types'
import { cn } from '@/shared/lib/utils'
import { MagnifyingGlass, Funnel } from '@phosphor-icons/react'

interface JobsToolbarProps {
  query: string
  onQueryChange: (value: string) => void
  filterProcessingStatus: ProcessingStatus | ''
  onFilterProcessingStatusChange: (value: ProcessingStatus | '') => void
  filterRemote: boolean | ''
  onFilterRemoteChange: (value: boolean | '') => void
  filterVisa: boolean | ''
  onFilterVisaChange: (value: boolean | '') => void
  activeFilterCount: number
  onClearFilters: () => void
}

export function JobsToolbar({
  query, onQueryChange,
  filterProcessingStatus, onFilterProcessingStatusChange,
  filterRemote, onFilterRemoteChange,
  filterVisa, onFilterVisaChange,
  activeFilterCount, onClearFilters,
}: JobsToolbarProps) {
  return (
    <div className="px-3 py-2 border-b border-border/40">
      <div className="flex items-center gap-2">
        <div className="relative flex-1 max-w-sm">
          <MagnifyingGlass className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
          <Input
            value={query}
            onChange={e => onQueryChange(e.target.value)}
            placeholder="Search by title, company, or keyword..."
            className={cn('pl-8 h-7 text-xs', query && 'border-emerald-500/30')}
          />
          {query && (
            <button
              onClick={() => onQueryChange('')}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-2xs text-muted-foreground hover:text-foreground"
            >
              ✕
            </button>
          )}
        </div>
        <div className="flex items-center gap-1.5">
          <Select value={filterProcessingStatus} onValueChange={(v) => onFilterProcessingStatusChange(v as ProcessingStatus | '')}>
            <SelectTrigger className="h-7 w-auto text-2xs gap-1">
              <Funnel className="w-3 h-3" />
              <span>{filterProcessingStatus || 'Status'}</span>
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">All</SelectItem>
              <SelectItem value="created">Created</SelectItem>
              <SelectItem value="queued">Queued</SelectItem>
              <SelectItem value="running">Running</SelectItem>
              <SelectItem value="completed">Completed</SelectItem>
              <SelectItem value="failed">Failed</SelectItem>
            </SelectContent>
          </Select>
          <Select value={filterRemote !== '' ? String(filterRemote) : ''} onValueChange={(v) => onFilterRemoteChange(v === '' ? '' : v === 'true')}>
            <SelectTrigger className="h-7 w-auto text-2xs gap-1">
              <span>{filterRemote !== '' ? (filterRemote ? 'Remote' : 'On-site') : 'Remote'}</span>
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">All</SelectItem>
              <SelectItem value="true">Remote</SelectItem>
              <SelectItem value="false">On-site</SelectItem>
            </SelectContent>
          </Select>
          <Select value={filterVisa !== '' ? String(filterVisa) : ''} onValueChange={(v) => onFilterVisaChange(v === '' ? '' : v === 'true')}>
            <SelectTrigger className="h-7 w-auto text-2xs gap-1">
              <span>{filterVisa !== '' ? (filterVisa ? 'Visa' : 'No Visa') : 'Visa'}</span>
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">All</SelectItem>
              <SelectItem value="true">Visa</SelectItem>
              <SelectItem value="false">No Visa</SelectItem>
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
