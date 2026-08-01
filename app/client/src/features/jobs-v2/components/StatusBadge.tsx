import { cn } from '@/shared/lib/utils'
import type { ProcessingStatus } from '@/entities/job/types'

interface StatusBadgeProps {
  status: ProcessingStatus | null
  className?: string
}

const statusConfig: Record<string, { color: string; label: string }> = {
  created: { color: 'bg-gray-500/15 text-gray-500 border-gray-500/20', label: 'Created' },
  queued: { color: 'bg-blue-500/15 text-blue-500 border-blue-500/20', label: 'Queued' },
  starting: { color: 'bg-amber-500/15 text-amber-500 border-amber-500/20', label: 'Starting' },
  running: { color: 'bg-emerald-500/15 text-emerald-500 border-emerald-500/20', label: 'Running' },
  completed: { color: 'bg-green-500/15 text-green-500 border-green-500/20', label: 'Completed' },
  failed: { color: 'bg-red-500/15 text-red-500 border-red-500/20', label: 'Failed' },
  cancelled: { color: 'bg-gray-500/15 text-gray-500 border-gray-500/20', label: 'Cancelled' },
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  if (!status) {
    return (
      <span className={cn('inline-flex items-center text-xs text-muted-foreground', className)}>
        —
      </span>
    )
  }

  const config = statusConfig[status] || { color: 'bg-gray-500/15 text-gray-500 border-gray-500/20', label: status }

  return (
    <span className={cn(
      'inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-2xs font-medium border',
      config.color,
      className
    )}>
      {status === 'running' && (
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
      )}
      {config.label}
    </span>
  )
}
