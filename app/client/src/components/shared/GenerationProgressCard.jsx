import { Spinner, X, Copy, Check } from '@phosphor-icons/react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { toast } from 'sonner'

const DEFAULT_STEPS = [
  { key: 'prepare', label: 'Preparing' },
  { key: 'prompt', label: 'Prompt' },
  { key: 'ai', label: 'AI' },
  { key: 'save', label: 'Saving' },
]

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
        {progress?.message && <span className="text-[0.6rem] text-muted-foreground">{progress.message}</span>}
        <div className="flex-1">
          <Progress value={totalSteps ? (displayStep / totalSteps) * 100 : 0} className="h-1" />
        </div>
        <span className="text-[0.55rem] text-muted-foreground shrink-0">{displayStep}/{totalSteps}</span>
        {session_id && (
          <button onClick={handleCopySession} className="text-[0.5rem] text-muted-foreground hover:text-foreground font-mono truncate max-w-[80px] shrink-0" title={`Click to copy: ${session_id}`}>
            {session_id.slice(0, 8)}...
          </button>
        )}
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
        {isRunning && <Badge variant="default" className="text-[0.5rem] animate-pulse">LIVE</Badge>}
        <div className="ml-auto flex items-center gap-2">
          {type && <span className="text-[0.55rem] text-muted-foreground">{type}</span>}
          {session_id && (
            <button onClick={handleCopySession} className="text-[0.55rem] text-muted-foreground hover:text-foreground font-mono flex items-center gap-1" title={`Click to copy: ${session_id}`}>
              <Copy className="w-3 h-3" /> {session_id.slice(0, 8)}...
            </button>
          )}
          {isRunning && onCancel && (
            <Button variant="destructive" size="sm" onClick={onCancel} className="h-6 gap-1 text-[0.55rem]">
              <X className="w-3 h-3" /> Terminate
            </Button>
          )}
          {(isFailed || isCancelled) && onRetry && (
            <Button variant="outline" size="sm" onClick={onRetry} className="h-6 gap-1 text-[0.55rem]">
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
                  "w-5 h-5 rounded-full flex items-center justify-center text-[0.45rem] font-bold transition-all border shrink-0",
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
              <span className={cn("text-[0.5rem]",
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
          <div className="text-[0.6rem] text-red-400 max-h-[60px] overflow-y-auto font-mono">{progress.error}</div>
        </div>
      )}

      {/* Progress + elapsed */}
      {isRunning && (
        <div className="flex items-center gap-2">
          <Progress value={totalSteps ? (displayStep / totalSteps) * 100 : 0} className="h-1 flex-1" />
          <span className="text-[0.55rem] text-muted-foreground shrink-0">{formatElapsed(elapsedSec)}</span>
        </div>
      )}
    </Card>
  )
}
