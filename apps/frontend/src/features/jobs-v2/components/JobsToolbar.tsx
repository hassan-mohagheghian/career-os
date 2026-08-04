'use client'

import { DebouncedInput } from '@/shared/ui/debounced-input'
import { Button } from '@/shared/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger } from '@/shared/ui/select'
import type { ProcessingStatusFilter, RecommendationFilter } from '@/entities/job/types'
import { MagnifyingGlass, MapPin, Funnel, Star } from '@phosphor-icons/react'
import { cn } from '@/shared/lib/utils'

const STATUS_FILTER_LABELS: Record<string, string> = {
  created: 'Created',
  queued: 'Queued',
  running: 'Running',
  completed: 'Completed',
  failed: 'Failed',
  none: 'Not processed',
}

const RECOMMENDATION_LABELS: Record<string, string> = {
  apply: 'Apply',
  consider: 'Consider',
  skip: 'Skip',
}

interface JobsToolbarProps {
  query: string
  onQueryChange: (value: string) => void
  filterProcessingStatus: ProcessingStatusFilter
  onFilterProcessingStatusChange: (value: ProcessingStatusFilter) => void
  filterLocation: string
  onFilterLocationChange: (value: string) => void
  filterRemote: boolean | ''
  onFilterRemoteChange: (value: boolean | '') => void
  filterVisa: boolean | ''
  onFilterVisaChange: (value: boolean | '') => void
  filterFavorite: boolean
  onFilterFavoriteChange: (value: boolean) => void
  filterRecommendation: RecommendationFilter
  onFilterRecommendationChange: (value: RecommendationFilter) => void
  activeFilterCount: number
  onClearFilters: () => void
}

export function JobsToolbar({
  query, onQueryChange,
  filterProcessingStatus, onFilterProcessingStatusChange,
  filterLocation, onFilterLocationChange,
  filterRemote, onFilterRemoteChange,
  filterVisa, onFilterVisaChange,
  filterFavorite, onFilterFavoriteChange,
  filterRecommendation, onFilterRecommendationChange,
  activeFilterCount, onClearFilters,
}: JobsToolbarProps) {
  return (
    <div className="px-3 py-2 border-b border-border/40">
      <div className="flex items-center gap-2">
        <div className="relative flex-1 max-w-sm">
          <DebouncedInput
            value={query}
            onValueChange={onQueryChange}
            placeholder="Search by title, company, or keyword..."
            icon={<MagnifyingGlass className="w-3.5 h-3.5 text-muted-foreground" />}
            clearable
            clearLabel="Clear search"
            activeClassName="border-emerald-500/30"
            wrapperClassName="w-full"
            inputClassName="pl-8 h-7 text-xs"
            aria-label="Search jobs"
          />
        </div>
        <div className="flex items-center gap-1.5">
          <Select value={filterProcessingStatus} onValueChange={(v) => onFilterProcessingStatusChange(v as ProcessingStatusFilter)}>
            <SelectTrigger className="h-7 w-auto text-2xs gap-1">
              <Funnel className="w-3 h-3" />
              <span>{filterProcessingStatus ? STATUS_FILTER_LABELS[filterProcessingStatus] ?? filterProcessingStatus : 'Status'}</span>
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">All</SelectItem>
              <SelectItem value="created">Created</SelectItem>
              <SelectItem value="queued">Queued</SelectItem>
              <SelectItem value="running">Running</SelectItem>
              <SelectItem value="completed">Completed</SelectItem>
              <SelectItem value="failed">Failed</SelectItem>
              <SelectItem value="none">Not processed</SelectItem>
            </SelectContent>
          </Select>
          <div className="relative w-36">
            <DebouncedInput
              value={filterLocation}
              onValueChange={onFilterLocationChange}
              placeholder="Location..."
              icon={<MapPin className="w-3 h-3 text-muted-foreground" />}
              clearable
              clearLabel="Clear location filter"
              activeClassName="border-emerald-500/30"
              wrapperClassName="w-full"
              inputClassName="pl-6 h-7 text-2xs"
              aria-label="Filter by location"
            />
          </div>
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
          <Select value={filterRecommendation} onValueChange={(v) => onFilterRecommendationChange(v as RecommendationFilter)}>
            <SelectTrigger className="h-7 w-auto text-2xs gap-1">
              <span>{filterRecommendation ? RECOMMENDATION_LABELS[filterRecommendation] ?? filterRecommendation : 'Recommendation'}</span>
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">All</SelectItem>
              <SelectItem value="apply">Apply</SelectItem>
              <SelectItem value="consider">Consider</SelectItem>
              <SelectItem value="skip">Skip</SelectItem>
            </SelectContent>
          </Select>
          <Button
            variant="ghost"
            size="sm"
            className={cn('h-7 w-auto gap-1 text-2xs', filterFavorite && 'text-yellow-500')}
            onClick={() => onFilterFavoriteChange(!filterFavorite)}
            aria-label="Show favorites only"
            aria-pressed={filterFavorite}
            title={filterFavorite ? 'Showing favorites only' : 'Show favorites only'}
          >
            <Star className="w-3 h-3" weight={filterFavorite ? 'fill' : 'regular'} />
            Favorites
          </Button>
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
