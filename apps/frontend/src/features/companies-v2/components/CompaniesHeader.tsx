'use client'

import { Button } from '@/shared/ui/button'
import { Buildings, Plus, Queue as QueueIcon, ArrowsClockwise } from '@phosphor-icons/react'
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '@/shared/ui/tooltip'
import { cn } from '@/shared/lib/utils'

interface CompaniesHeaderProps {
  total: number
  loadedCount: number
  onOpenQueue: () => void
  onAddCompany: () => void
  onRefresh?: () => void
  isRefreshing?: boolean
}

export function CompaniesHeader({ total, loadedCount, onOpenQueue, onAddCompany, onRefresh, isRefreshing }: CompaniesHeaderProps) {
  return (
    <div className="flex items-center justify-between px-3 py-2 border-b border-border/40">
      <div className="flex items-center gap-3">
        <h1 className="text-sm font-semibold text-foreground flex items-center gap-1.5">
          <Buildings className="w-3.5 h-3.5" /> Companies ({total})
        </h1>
        <span className="text-2xs text-muted-foreground">
          Loaded {loadedCount} of {total} companies
        </span>
      </div>
      <div className="flex items-center gap-2">
        <TooltipProvider delayDuration={200}>
          <Button variant="outline" size="sm" className="h-7 text-xs gap-1.5 relative" onClick={onOpenQueue}>
            <QueueIcon className="w-3.5 h-3.5" />
            Queue
          </Button>
          <Button size="sm" className="h-7 text-xs gap-1.5" onClick={onAddCompany}>
            <Plus className="w-3.5 h-3.5" />
            Add Company
          </Button>
          {onRefresh && (
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="outline"
                  size="icon"
                  className="h-7 w-7"
                  onClick={onRefresh}
                  disabled={isRefreshing}
                  aria-label="Refresh companies"
                >
                  <ArrowsClockwise className={cn("w-3.5 h-3.5", isRefreshing && "animate-spin")} />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom" className="text-xs">Refresh companies</TooltipContent>
            </Tooltip>
          )}
        </TooltipProvider>
      </div>
    </div>
  )
}
