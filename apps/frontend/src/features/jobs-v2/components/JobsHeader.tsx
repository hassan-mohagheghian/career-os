'use client'

import { Button } from '@/shared/ui/button'
import { Badge } from '@/shared/ui/badge'
import { List, Plus, ClipboardText, ArrowsClockwise } from '@phosphor-icons/react'
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '@/shared/ui/tooltip'
import { cn } from '@/shared/lib/utils'

interface JobsHeaderProps {
  total: number
  loadedCount: number
  processingCount: number
  onOpenQueue: () => void
  onAddJob: () => void
  onRefresh?: () => void
  isRefreshing?: boolean
}

export function JobsHeader({ total, loadedCount, processingCount, onOpenQueue, onAddJob, onRefresh, isRefreshing }: JobsHeaderProps) {
  return (
    <div className="flex items-center justify-between px-3 py-2 border-b border-border/40">
      <div className="flex items-center gap-3">
        <h1 className="text-sm font-semibold text-foreground">Jobs ({total})</h1>
        <span className="text-2xs text-muted-foreground">
          Loaded {loadedCount} of {total} jobs
        </span>
      </div>
      <div className="flex items-center gap-2">
        <TooltipProvider delayDuration={200}>
          <Button variant="outline" size="sm" className="h-7 text-xs gap-1.5 relative" onClick={onOpenQueue}>
            <List className="w-3.5 h-3.5" />
            Queue
            {processingCount > 0 && (
              <Badge variant="default" className="text-2xs h-4 px-1 absolute -top-1.5 -right-1.5">
                {processingCount}
              </Badge>
            )}
          </Button>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button size="sm" className="h-7 text-xs gap-1.5" onClick={onAddJob}>
                <Plus className="w-3.5 h-3.5" />
                Add Job
                <kbd className="ml-0.5 inline-flex h-4 items-center rounded border border-border bg-background px-1 font-sans text-2xs text-muted-foreground">
                  N
                </kbd>
              </Button>
            </TooltipTrigger>
            <TooltipContent side="bottom" className="text-xs">
              <span className="flex items-center gap-1.5">
                <ClipboardText className="w-3 h-3" />
                Press <kbd className="rounded border border-border bg-background px-1 font-sans">N</kbd> to add a job from a copied link
              </span>
            </TooltipContent>
          </Tooltip>
          {onRefresh && (
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="outline"
                  size="icon"
                  className="h-7 w-7"
                  onClick={onRefresh}
                  disabled={isRefreshing}
                  aria-label="Refresh jobs"
                >
                  <ArrowsClockwise className={cn("w-3.5 h-3.5", isRefreshing && "animate-spin")} />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom" className="text-xs">Refresh jobs</TooltipContent>
            </Tooltip>
          )}
        </TooltipProvider>
      </div>
    </div>
  )
}
