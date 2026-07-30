import {
  Pause, Repeat, Trash, ArrowBendUpLeft,
  Copy, Rocket, FileText, X, ArrowUUpLeft
} from '@phosphor-icons/react'
import { cn } from '@/shared/lib/utils'
import { Button } from '@/shared/ui/button'

interface CardActionsProps {
  status: string
  size?: 'sm' | 'md'
  disabled?: boolean
  error?: string | null
  hasWorkflowLogs?: boolean
  onDelete?: () => void
  onProcess?: () => void
  onCancel?: () => void
  onMoveToCreated?: () => void
  onViewWorkflow?: () => void
  className?: string
}

function setToast(msg: string) {
  window.dispatchEvent(new CustomEvent('toast', { detail: msg }))
}

const ACTIVE = new Set(['processing'])
const PRE_PROCESS = new Set(['created', 'pending', 'queued'])
const FAILED = new Set(['failed', 'error'])
const COMPLETED = new Set(['processed', 'cancelled', 'imported'])

export default function CardActions({
  status, size = 'sm', disabled = false, error, hasWorkflowLogs,
  onDelete, onProcess, onCancel, onMoveToCreated, onViewWorkflow, className,
}: CardActionsProps) {
  const isActive = ACTIVE.has(status)
  const isPreProcess = PRE_PROCESS.has(status)
  const isFailed = FAILED.has(status)
  const isCompleted = COMPLETED.has(status)

  const showProcess = onProcess && (isPreProcess || isFailed || isCompleted) && !isActive
  const showCancel = onCancel && isActive
  const showMoveToCreated = onMoveToCreated && status === 'queued'
  const showWorkflow = onViewWorkflow && hasWorkflowLogs
  const showDelete = !!onDelete && !isActive
  const showCopyError = isFailed && error

  const iconSize = size === 'sm' ? 'w-1.5 h-1.5' : 'w-2 h-2'
  const iconBtnSize = size === 'sm' ? 'h-3 w-3' : 'h-3.5 w-3.5'

  if (!showProcess && !showCancel && !showMoveToCreated && !showWorkflow && !showDelete && !showCopyError) {
    return null
  }

  return (
    <div className={cn('flex items-center gap-0 shrink-0', className)}>
      {showCopyError && (
        <Button
          variant="ghost" size="icon"
          className={cn(iconBtnSize, 'shrink-0 text-red-400 hover:bg-red-500/10')}
          onClick={(e) => { e.stopPropagation(); navigator.clipboard.writeText(error!); setToast('Error copied!') }}
          title="Copy error"
        >
          <Copy className={iconSize} />
        </Button>
      )}
      {showProcess && isPreProcess && size === 'sm' && (
        <Button
          size="sm"
          onClick={(e) => { e.stopPropagation(); onProcess?.() }}
          disabled={disabled}
          className="h-3.5 px-1 text-3xs gap-0.5 shrink-0"
        >
          <Rocket className="w-1.5 h-1.5" /> Start
        </Button>
      )}
      {showProcess && (isFailed || isCompleted || (isPreProcess && size === 'md')) && (
        <Button
          variant="ghost" size="icon"
          className={cn(iconBtnSize, 'shrink-0',
            isFailed ? 'text-green-500 hover:bg-green-500/10' : 'text-blue-500 hover:bg-blue-500/10'
          )}
          onClick={(e) => { e.stopPropagation(); onProcess?.() }}
          disabled={disabled}
          title={isFailed ? 'Retry' : 'Process'}
        >
          <Repeat className={cn(iconSize, disabled && 'animate-spin')} />
        </Button>
      )}
      {showCancel && (
        <Button
          variant="ghost" size="icon"
          className={cn(iconBtnSize, 'shrink-0 text-yellow-500 hover:bg-yellow-500/10')}
          onClick={(e) => { e.stopPropagation(); onCancel?.() }}
          disabled={disabled}
          title="Cancel"
        >
          <X className={iconSize} />
        </Button>
      )}
      {showMoveToCreated && (
        <Button
          variant="ghost" size="icon"
          className={cn(iconBtnSize, 'shrink-0 text-orange-500 hover:bg-orange-500/10')}
          onClick={(e) => { e.stopPropagation(); onMoveToCreated?.() }}
          disabled={disabled}
          title="Move to Created"
        >
          <ArrowUUpLeft className={iconSize} />
        </Button>
      )}
      {showWorkflow && (
        <Button
          variant="ghost" size="icon"
          className={cn(iconBtnSize, 'shrink-0')}
          onClick={(e) => { e.stopPropagation(); onViewWorkflow?.() }}
          title="Workflow"
        >
          <FileText className={iconSize} />
        </Button>
      )}
      {showDelete && (
        <Button
          variant="ghost" size="icon"
          className={cn(iconBtnSize, 'shrink-0 text-destructive hover:bg-destructive/10')}
          onClick={(e) => { e.stopPropagation(); onDelete?.() }}
          disabled={disabled}
          title="Delete"
        >
          <Trash className={iconSize} />
        </Button>
      )}
    </div>
  )
}
