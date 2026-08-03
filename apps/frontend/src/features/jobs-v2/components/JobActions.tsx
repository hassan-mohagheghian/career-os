import type { ProcessingStatus } from '@/entities/job/types'
import { ProcessingButton } from './ProcessingButton'
import { Button } from '@/shared/ui/button'
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '@/shared/ui/tooltip'
import { Eye, ArrowsClockwise, Square, PencilSimple, Trash } from '@phosphor-icons/react'

interface JobActionsProps {
  processingStatus: ProcessingStatus | null
  onProcessV2: () => void
  onViewDetails: () => void
  onEdit: () => void
  onDelete: () => void
  onRetry?: () => void
  onCancel?: () => void
}

function IconButton({
  icon,
  label,
  onClick,
  color,
}: {
  icon: React.ReactNode
  label: string
  onClick: () => void
  color?: string
}) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button variant="ghost" size="sm" className="h-6 w-6 p-0 text-muted-foreground" onClick={onClick} aria-label={label}>
          <span className={color}>{icon}</span>
        </Button>
      </TooltipTrigger>
      <TooltipContent side="top" className="text-xs">{label}</TooltipContent>
    </Tooltip>
  )
}

export function JobActions({
  processingStatus, onProcessV2, onViewDetails, onEdit, onDelete, onRetry, onCancel,
}: JobActionsProps) {
  return (
    <TooltipProvider delayDuration={200}>
      <div className="flex items-center gap-1">
        {(!processingStatus || processingStatus === 'created') && (
          <>
            <ProcessingButton onClick={onProcessV2} />
            <IconButton icon={<Eye className="w-3 h-3" />} label="Details" onClick={onViewDetails} />
          </>
        )}
        {processingStatus === 'running' && (
          <IconButton icon={<Eye className="w-3 h-3 text-emerald-500" />} label="View Progress" onClick={onViewDetails} />
        )}
        {processingStatus === 'completed' && (
          <>
            <IconButton icon={<Eye className="w-3 h-3 text-green-500" />} label="View Results" onClick={onViewDetails} />
            <IconButton icon={<ArrowsClockwise className="w-3 h-3" />} label="Reprocess" onClick={onProcessV2} />
          </>
        )}
        {processingStatus === 'failed' && (
          <>
            <IconButton icon={<ArrowsClockwise className="w-3 h-3 text-red-500" />} label="Retry" onClick={onRetry!} />
            <IconButton icon={<Eye className="w-3 h-3" />} label="Details" onClick={onViewDetails} />
          </>
        )}
        {(processingStatus === 'queued' || processingStatus === 'starting') && (
          <IconButton icon={<Square className="w-3 h-3" />} label="Cancel" onClick={onCancel!} />
        )}
        <IconButton icon={<PencilSimple className="w-3 h-3" />} label="Edit" onClick={onEdit} />
        <IconButton icon={<Trash className="w-3 h-3 text-red-500" />} label="Delete" onClick={onDelete} />
      </div>
    </TooltipProvider>
  )
}