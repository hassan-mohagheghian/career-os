'use client'

import { Button } from '@/shared/ui/button'
import { MapPin, ArrowsClockwise } from '@phosphor-icons/react'
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '@/shared/ui/tooltip'
import { cn } from '@/shared/lib/utils'

interface CitiesHeaderProps {
  total: number
  loadedCount: number
  onRefresh?: () => void
  isRefreshing?: boolean
}

export function CitiesHeader({ total, loadedCount, onRefresh, isRefreshing }: CitiesHeaderProps) {
  return (
    <div className="flex items-center justify-between px-3 py-2 border-b border-border/40">
      <div className="flex items-center gap-3">
        <h1 className="text-sm font-semibold text-foreground flex items-center gap-1.5">
          <MapPin className="w-3.5 h-3.5" /> Cities ({total})
        </h1>
        <span className="text-2xs text-muted-foreground">
          Loaded {loadedCount} of {total} cities
        </span>
      </div>
      {onRefresh && (
        <TooltipProvider delayDuration={200}>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="outline"
                size="icon"
                className="h-7 w-7"
                onClick={onRefresh}
                disabled={isRefreshing}
                aria-label="Refresh cities"
              >
                <ArrowsClockwise className={cn("w-3.5 h-3.5", isRefreshing && "animate-spin")} />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="bottom" className="text-xs">Refresh cities</TooltipContent>
          </Tooltip>
        </TooltipProvider>
      )}
    </div>
  )
}