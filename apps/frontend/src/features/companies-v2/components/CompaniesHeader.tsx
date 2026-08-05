'use client'

import { Button } from '@/shared/ui/button'
import { Badge } from '@/shared/ui/badge'
import { Buildings, Plus, Queue as QueueIcon } from '@phosphor-icons/react'

interface CompaniesHeaderProps {
  total: number
  loadedCount: number
  pendingTotal: number
  onOpenQueue: () => void
  onAddCompany: () => void
}

export function CompaniesHeader({ total, loadedCount, pendingTotal, onOpenQueue, onAddCompany }: CompaniesHeaderProps) {
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
        <Button variant="outline" size="sm" className="h-7 text-xs gap-1.5 relative" onClick={onOpenQueue}>
          <QueueIcon className="w-3.5 h-3.5" />
          Queue
          {pendingTotal > 0 && (
            <Badge variant="default" className="text-2xs h-4 px-1 absolute -top-1.5 -right-1.5">
              {pendingTotal}
            </Badge>
          )}
        </Button>
        <Button size="sm" className="h-7 text-xs gap-1.5" onClick={onAddCompany}>
          <Plus className="w-3.5 h-3.5" />
          Add Company
        </Button>
      </div>
    </div>
  )
}
