import { Spinner, X, Copy, Check } from '@phosphor-icons/react'
import { cn } from '@/shared/lib/utils'
import { Button } from '@/shared/ui/button'
import { Badge } from '@/shared/ui/badge'
import { Card } from '@/shared/ui/card'
import { Progress } from '@/shared/ui/progress'
import { toast } from 'sonner'

// Step configurations for each generation source type
export const STEP_CONFIGS: Record<string, { steps: Array<{ key: string; label: string }>; totalSteps: number }> = {
  // Job processing: 8 steps
  'job-processing': {
    totalSteps: 8,
    steps: [
      { key: 'step_fetch', label: 'Fetching' },
      { key: 'step_validate', label: 'Validating' },
      { key: 'step_extract_raw', label: 'Extracting' },
      { key: 'step_extract_struct', label: 'Structuring' },
      { key: 'step_summary', label: 'Summarizing' },
      { key: 'step_analyze', label: 'Analyzing' },
      { key: 'step_db', label: 'Saving' },
      { key: 'step_done', label: 'Done' },
    ],
  },
  // Company processing: 5 steps
  'company-processing': {
    totalSteps: 5,
    steps: [
      { key: 'step_fetch', label: 'Fetching' },
      { key: 'step_extract', label: 'Extracting' },
      { key: 'step_analyze', label: 'Analyzing' },
      { key: 'step_save', label: 'Saving' },
      { key: 'step_done', label: 'Done' },
    ],
  },
  // Resume/Cover letter generation was removed with the legacy generation stack.
}

const DEFAULT_STEPS = STEP_CONFIGS['job-processing'].steps

function formatElapsed(seconds) {
  if (!seconds && seconds !== 0) return ''
  if (seconds < 60) return `${seconds}s`
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}m ${s}s`
}

export default function GenerationProgressCard({
  title = 'Generating...',
  type,
  progress,
  elapsed,
  steps = DEFAULT_STEPS,
  onCancel,
  onRetry,
  compact = false,
  className,
}) {
  if (!progress?.running && progress?.status !== 'failed' && progress?.status !== 'cancelled') return null

  const isFailed = progress?.status === 'failed'
  const isCancelled = progress?.status === 'cancelled'
  const isRunning = progress?.running
  const elapsedSec = elapsed || progress?.elapsed_seconds || 0
  const currentStep = progress?.step || 0
  const totalSteps = progress?.total_steps || steps.length
  const session_id = progress?.session_id

  // Auto-detect step index from elapsed time if step is 0
  const getStepFromElapsed = (secs) => {
    if (secs < 10) return 0
    if (secs < 30) return 1
    if (secs < 60) return 2
    if (secs < 90) return 3
    return 4
  }
  const displayStep = currentStep > 0 ? currentStep : (isRunning ? getStepFromElapsed(elapsedSec) : 0)

  const handleCopySession = () => {
    if (session_id) {
      navigator.clipboard.writeText(session_id)
      toast.success('Session ID copied')
    }
  }

  if (compact) {
    return (
      <div className={cn("flex items-center gap-2 p-2 rounded-lg border border-primary/30 bg-primary/5", className)}>
        <Spinner className="w-3.5 h-3.5 text-primary animate-spin shrink-0" />
        <span className="text-xs font-semibold">{title}</span>
        {progress?.message && <span className="text-2xs text-muted-foreground">{progress.message}</span>}
        <div className="flex-1">
          <Progress value={totalSteps ? (displayStep / totalSteps) * 100 : 0} className="h-1" />
        </div>
        <span className="text-2xs text-muted-foreground shrink-0">{displayStep}/{totalSteps}</span>
      </div>
    )
  }

  return (
    <Card className={cn("p-4 border-primary/30 bg-primary/5", className)}>
      {/* Header */}
      <div className="flex items-center gap-2 mb-3">
        {isRunning ? (
          <Spinner className="w-4 h-4 text-primary animate-spin" />
        ) : isFailed ? (
          <X className="w-4 h-4 text-red-500" />
        ) : (
          <Check className="w-4 h-4 text-green-500" />
        )}
        <span className="text-sm font-bold">{isFailed ? 'Failed' : isCancelled ? 'Cancelled' : title}</span>
        {isRunning && <Badge variant="default" className="text-2xs animate-pulse">LIVE</Badge>}
        <div className="ml-auto flex items-center gap-2">
          {type && <span className="text-2xs text-muted-foreground">{type}</span>}
          {isRunning && onCancel && (
            <Button variant="destructive" size="sm" onClick={onCancel} className="h-6 gap-1 text-2xs">
              <X className="w-3 h-3" /> Terminate
            </Button>
          )}
          {(isFailed || isCancelled) && onRetry && (
            <Button variant="outline" size="sm" onClick={onRetry} className="h-6 gap-1 text-2xs">
              <Spinner className="w-3 h-3" /> Retry
            </Button>
          )}
        </div>
      </div>

      {/* Step progress bar */}
      {isRunning && (
        <div className="flex gap-1 mb-3">
          {steps.map((step, i) => {
            const isDone = i < displayStep
            const isActive = i === displayStep
            return (
              <div key={step.key} className="flex items-center gap-0.5 flex-1">
                <div className={cn(
                  "w-5 h-5 rounded-full flex items-center justify-center text-2xs font-bold transition-all border shrink-0",
                  isDone ? "bg-green-500 text-white border-green-500" :
                  isActive ? "bg-primary text-primary-foreground border-primary animate-pulse" :
                  "bg-background text-muted-foreground border-border"
                )}>
                  {isDone ? <Check className="w-3 h-3" /> : isActive ? <Spinner className="w-3 h-3 animate-spin" /> : i + 1}
                </div>
                {i < steps.length - 1 && <div className={cn("h-[1px] flex-1 rounded-full", isDone ? "bg-green-500" : "bg-border")} />}
              </div>
            )
          })}
        </div>
      )}

      {/* Step labels */}
      {isRunning && (
        <div className="flex gap-1 mb-2">
          {steps.map((step, i) => (
            <div key={step.key} className="flex-1 text-center">
              <span className={cn("text-2xs",
                i < displayStep ? "text-green-500 font-semibold" :
                i === displayStep ? "text-primary font-semibold" : "text-muted-foreground"
              )}>
                {i < displayStep ? '✓ ' : i === displayStep ? '● ' : ''}{step.label}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Error display */}
      {isFailed && progress?.error && (
        <div className="mb-3 p-2 rounded bg-red-500/10 border border-red-500/20">
          <div className="text-2xs text-red-400 max-h-[60px] overflow-y-auto font-mono">{progress.error}</div>
        </div>
      )}

      {/* Progress + elapsed */}
      {isRunning && (
        <div className="flex items-center gap-2">
          <Progress value={totalSteps ? (displayStep / totalSteps) * 100 : 0} className="h-1 flex-1" />
          <span className="text-2xs text-muted-foreground shrink-0">{formatElapsed(elapsedSec)}</span>
        </div>
      )}
    </Card>
  )
}
