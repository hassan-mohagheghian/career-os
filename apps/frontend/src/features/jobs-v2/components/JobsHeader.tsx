'use client'

import { Button } from '@/shared/ui/button'
import { Badge } from '@/shared/ui/badge'
import { List, Plus } from '@phosphor-icons/react'

interface JobsHeaderProps {
  total: number
  loadedCount: number
  processingCount: number
  onOpenQueue: () => void
  onAddJob: () => void
}

export function JobsHeader({ total, loadedCount, processingCount, onOpenQueue, onAddJob }: JobsHeaderProps) {
  return (
    <div className="flex items-center justify-between px-3 py-2 border-b border-border/40">
      <div className="flex items-center gap-3">
        <h1 className="text-sm font-semibold text-foreground">Jobs ({total})</h1>
        <span className="text-2xs text-muted-foreground">
          Loaded {loadedCount} of {total} jobs
        </span>
      </div>
      <div className="flex items-center gap-2">
        <Button variant="outline" size="sm" className="h-7 text-xs gap-1.5 relative" onClick={onOpenQueue}>
          <List className="w-3.5 h-3.5" />
          Queue
          {processingCount > 0 && (
            <Badge variant="default" className="text-2xs h-4 px-1 absolute -top-1.5 -right-1.5">
              {processingCount}
            </Badge>
          )}
        </Button>
        <Button size="sm" className="h-7 text-xs gap-1.5" onClick={onAddJob}>
          <Plus className="w-3.5 h-3.5" />
          Add Job
        </Button>
      </div>
    </div>
  )
}
