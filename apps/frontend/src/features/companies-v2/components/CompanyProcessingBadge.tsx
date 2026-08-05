import { cn } from '@/shared/lib/utils'

interface CompanyProcessingBadgeProps {
  status: string | null | undefined
  className?: string
}

const statusConfig: Record<string, { color: string; label: string }> = {
  created: { color: 'bg-gray-500/15 text-gray-500 border-gray-500/20', label: 'Created' },
  pending: { color: 'bg-sky-500/15 text-sky-500 border-sky-500/20', label: 'Pending' },
  queued: { color: 'bg-yellow-500/15 text-yellow-500 border-yellow-500/20', label: 'Queued' },
  processing: { color: 'bg-blue-500/15 text-blue-500 border-blue-500/20', label: 'Processing' },
  running: { color: 'bg-emerald-500/15 text-emerald-500 border-emerald-500/20', label: 'Running' },
  completed: { color: 'bg-green-500/15 text-green-500 border-green-500/20', label: 'Completed' },
  processed: { color: 'bg-green-500/15 text-green-500 border-green-500/20', label: 'Processed' },
  failed: { color: 'bg-red-500/15 text-red-500 border-red-500/20', label: 'Failed' },
  cancelled: { color: 'bg-red-500/15 text-red-500 border-red-500/20', label: 'Cancelled' },
}

export function CompanyProcessingBadge({ status, className }: CompanyProcessingBadgeProps) {
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
      'inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-2xs font-medium border whitespace-nowrap',
      config.color,
      className
    )}>
      {(status === 'processing' || status === 'running') && (
        <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
      )}
      {config.label}
    </span>
  )
}
