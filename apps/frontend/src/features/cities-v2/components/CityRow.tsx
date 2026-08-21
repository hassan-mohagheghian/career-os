'use client'

import type { CityListItem } from '@/entities/city/types'
import { formatCityLocation } from '@/shared/lib/formatLocation'
import { Badge } from '@/shared/ui/badge'
import { GitMerge, PencilSimple } from '@phosphor-icons/react'
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '@/shared/ui/tooltip'

interface CityRowProps {
  city: CityListItem
  onOpenEdit: (city: CityListItem) => void
  onMerge: (city: CityListItem) => void
}

export function CityRow({ city, onOpenEdit, onMerge }: CityRowProps) {
  const originalText = city.original_text?.trim()
  const address = city.address?.trim()
  const hasDetail = originalText || address

  return (
    <div className="group flex items-center px-3 py-2 border-b border-border/40 last:border-b-0 hover:bg-muted/40 transition-colors">
      <div className="flex-1 min-w-0 flex items-center gap-2">
        <span className="text-xs text-foreground truncate">
          {formatCityLocation(city.city, city.country) || 'Unknown'}
        </span>
        {city.country && (
          <span className="text-2xs text-muted-foreground shrink-0">{city.country}</span>
        )}
        {city.aliases.length > 0 && (
          <Badge variant="secondary" className="text-2xs shrink-0">
            {city.aliases.length} alias{city.aliases.length !== 1 ? 'es' : ''}
          </Badge>
        )}
      </div>
      <div className="w-32 min-w-0 shrink-0 text-right">
        <span className="text-xs font-semibold tabular-nums text-primary">{city.job_count}</span>
        <span className="text-2xs text-muted-foreground ml-1">jobs</span>
      </div>
      {hasDetail && (
        <div className="w-40 min-w-0 hidden lg:block pl-3 text-right">
          <span className="text-2xs text-muted-foreground truncate block max-w-full">
            {originalText || address}
          </span>
        </div>
      )}
      <div className="w-12 shrink-0 flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
        <TooltipProvider delayDuration={200}>
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                type="button"
                onClick={() => onMerge(city)}
                className="rounded p-1 text-muted-foreground hover:text-foreground hover:bg-muted/60"
                aria-label={`Merge ${formatCityLocation(city.city, city.country)}`}
              >
                <GitMerge className="w-3.5 h-3.5" />
              </button>
            </TooltipTrigger>
            <TooltipContent side="top" className="text-xs">Merge</TooltipContent>
          </Tooltip>
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                type="button"
                onClick={() => onOpenEdit(city)}
                className="rounded p-1 text-muted-foreground hover:text-foreground hover:bg-muted/60"
                aria-label={`Edit ${formatCityLocation(city.city, city.country)}`}
              >
                <PencilSimple className="w-3.5 h-3.5" />
              </button>
            </TooltipTrigger>
            <TooltipContent side="top" className="text-xs">Edit aliases</TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>
    </div>
  )
}