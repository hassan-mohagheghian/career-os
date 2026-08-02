import { StatusBadge } from './StatusBadge'
import type { ProcessingStatus } from '@/entities/job/types'

interface ProcessingStatusProps {
  status: ProcessingStatus | null
  progress?: number | null
}

export function ProcessingStatus({ status, progress }: ProcessingStatusProps) {
  return (
    <div className="flex items-center gap-2">
      <StatusBadge status={status} />
      {status === 'running' && progress !== null && progress !== undefined && (
        <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden">
          <div
            className="h-full bg-emerald-500 rounded-full transition-all duration-500"
            style={{ width: `${Math.min(progress, 100)}%` }}
          />
        </div>
      )}
    </div>
  )
}
