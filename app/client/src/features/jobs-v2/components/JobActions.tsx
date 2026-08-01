import type { ProcessingStatus } from '@/entities/job/types'
import { ProcessingButton } from './ProcessingButton'
import { Button } from '@/shared/ui/button'
import { Play, Eye, ArrowsClockwise, Square } from '@phosphor-icons/react'

interface JobActionsProps {
  processingStatus: ProcessingStatus | null
  onProcessV2: () => void
  onLegacyProcess: () => void
  onViewDetails: () => void
  onRetry?: () => void
  onCancel?: () => void
}

export function JobActions({
  processingStatus, onProcessV2, onLegacyProcess, onViewDetails, onRetry, onCancel,
}: JobActionsProps) {
  return (
    <div className="flex items-center gap-1">
      {(!processingStatus || processingStatus === 'created') && (
        <>
          <ProcessingButton onClick={onProcessV2} />
          <Button variant="ghost" size="sm" className="h-6 w-6 p-0 text-muted-foreground" onClick={onLegacyProcess} title="Legacy Process">
            <Play className="w-3 h-3" />
          </Button>
          <Button variant="ghost" size="sm" className="h-6 w-6 p-0 text-muted-foreground" onClick={onViewDetails} title="Details">
            <Eye className="w-3 h-3" />
          </Button>
        </>
      )}
      {processingStatus === 'running' && (
        <>
          <Button variant="ghost" size="sm" className="h-6 text-2xs gap-1 text-emerald-500" onClick={onViewDetails}>
            <Eye className="w-3 h-3" />
            View Progress
          </Button>
        </>
      )}
      {processingStatus === 'completed' && (
        <>
          <Button variant="ghost" size="sm" className="h-6 text-2xs gap-1 text-green-500" onClick={onViewDetails}>
            <Eye className="w-3 h-3" />
            View Results
          </Button>
          <Button variant="ghost" size="sm" className="h-6 text-2xs gap-1 text-muted-foreground" onClick={onProcessV2}>
            <ArrowsClockwise className="w-3 h-3" />
            Reprocess
          </Button>
        </>
      )}
      {processingStatus === 'failed' && (
        <>
          <Button variant="ghost" size="sm" className="h-6 text-2xs gap-1 text-red-500" onClick={onRetry}>
            <ArrowsClockwise className="w-3 h-3" />
            Retry
          </Button>
          <Button variant="ghost" size="sm" className="h-6 text-2xs gap-1 text-muted-foreground" onClick={onViewDetails}>
            <Eye className="w-3 h-3" />
            Details
          </Button>
        </>
      )}
      {(processingStatus === 'queued' || processingStatus === 'starting') && (
        <Button variant="ghost" size="sm" className="h-6 w-6 p-0 text-muted-foreground" onClick={onCancel} title="Cancel">
          <Square className="w-3 h-3" />
        </Button>
      )}
    </div>
  )
}
