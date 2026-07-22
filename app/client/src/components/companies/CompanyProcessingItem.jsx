import { useState } from 'react'
import {
  Rocket, Pause, Repeat, Trash, ArrowBendUpLeft,
  Check, Globe, CheckCircle, Brain, Warning, LinkSimple, Copy
} from '@phosphor-icons/react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip'

function setToast(msg) {
  window.dispatchEvent(new CustomEvent('toast', { detail: msg }))
}

const STEPS = [
  { key: 'fetch', icon: <Globe className="w-3 h-3" />, abbr: 'Fetch', label: 'Fetch content' },
  { key: 'extract', icon: <Brain className="w-3 h-3" />, abbr: 'Extract', label: 'Extract info' },
  { key: 'analyze', icon: <Brain className="w-3 h-3" />, abbr: 'Analyze', label: 'Analyze company' },
  { key: 'save', icon: <CheckCircle className="w-3 h-3" />, abbr: 'Save', label: 'Save to DB' },
  { key: 'done', icon: <CheckCircle className="w-3 h-3" />, abbr: 'Done', label: 'Complete' },
]

const STEP_KEYS = ['step_fetch', 'step_extract', 'step_analyze', 'step_save', 'step_done']

function getStatus(item) {
  if (item.status === 'done') return 'done'
  if (item.status === 'failed') return 'failed'
  if (item.status === 'processing') {
    const vals = STEP_KEYS.map(k => item[k])
    const done = vals.filter(s => s === 1).length
    const labels = ['Fetching', 'Extracting', 'Analyzing', 'Saving', 'Done']
    return labels[Math.min(done, labels.length - 1)] || 'Processing'
  }
  if (item.status === 'queued') return 'Queued'
  return 'Pending'
}

export default function CompanyProcessingItem({ item, onDelete, onProcess, onReset, onPause, onReprocess }) {
  const [processing, setProcessing] = useState(false)
  const statusKey = getStatus(item)
  const isDone = item.status === 'done'
  const isFailed = item.status === 'failed'
  const isPaused = item.status === 'paused'
  const isQueued = statusKey === 'Queued'
  const isPending = item.status === 'pending'
  const isProcessing = !isDone && !isFailed && !isPaused && !isQueued && !isPending

  const vals = STEP_KEYS.map(k => item[k])
  const done = vals.filter(s => s === 1).length
  const nextStep = isProcessing ? vals.findIndex(s => s !== 1) : -1
  const progress = (done / STEPS.length) * 100

  const handleReprocess = async () => {
    if (!onReprocess || processing) return
    setProcessing(true)
    try { await onReprocess() } finally { setProcessing(false) }
  }

  const handleProcess = async () => {
    if (!onProcess || processing) return
    setProcessing(true)
    try { await onProcess() } finally { setProcessing(false) }
  }

  return (
    <div className={cn(
      "group/card rounded-lg border bg-card p-1.5 min-w-0 overflow-hidden transition hover:shadow",
      isFailed && "border-red-500/30",
      isDone && "border-green-500/30"
    )}>
      {/* Row 1: Status dot + Company name */}
      <div className="flex items-center gap-1 mb-1 min-w-0">
        <div className={cn(
          "w-2 h-2 rounded-full shrink-0",
          isDone ? "bg-green-500" : isFailed ? "bg-red-500" : isPaused ? "bg-yellow-500" : isProcessing ? "bg-blue-500 animate-pulse" : isQueued ? "bg-yellow-400" : "bg-muted-foreground"
        )} />
        {item.source === 'reprocess' && <span className="text-[0.4rem] px-0.5 rounded bg-secondary text-secondary-foreground shrink-0">R</span>}
        <span className="text-[0.55rem] font-bold truncate min-w-0">{item.company_name || 'Processing...'}</span>
      </div>

      {/* Row 2: Step icons */}
      <div className="flex gap-1 mb-1 min-w-0">
        {STEPS.map((step, i) => {
          const d = vals[i] === 1
          const isActive = i === nextStep && !d
          return (
            <div key={i} className="flex-1 min-w-0 flex justify-center">
              <Tooltip>
                <TooltipTrigger asChild>
                  <div className={cn(
                    "w-4 h-4 rounded-full border shrink-0 flex items-center justify-center",
                    d ? "bg-green-500 border-green-500 text-white" :
                    isActive ? "bg-primary border-primary text-primary-foreground animate-pulse" :
                    "bg-background border-border text-muted-foreground"
                  )}>
                    {d ? <Check className="w-2 h-2" /> : step.icon}
                  </div>
                </TooltipTrigger>
                <TooltipContent side="top" className="text-[0.6rem] px-2 py-1">
                  {d ? `${step.label} — done` : isActive ? `${step.label} — in progress...` : step.label}
                </TooltipContent>
              </Tooltip>
            </div>
          )
        })}
      </div>

      {/* Row 3: Progress */}
      <div className="flex items-center gap-1 mb-1 min-w-0">
        <span className="text-[0.45rem] font-semibold text-muted-foreground shrink-0">{done}/{STEPS.length}</span>
        <Progress value={progress} className="h-0.5 flex-1 min-w-0" />
      </div>

      {/* Row 4: Status + actions */}
      <div className="flex items-center gap-1 min-w-0">
        {item.input_text && item.input_type === 'url' && (
          <Button variant="ghost" size="icon" className="h-3 w-3 shrink-0" onClick={(e) => { e.stopPropagation(); window.open(item.input_text, '_blank') }} title="Open URL">
            <LinkSimple className="w-1.5 h-1.5 text-primary" />
          </Button>
        )}
        <span className="text-[0.45rem] truncate flex-1 min-w-0 text-muted-foreground">
          {isProcessing && <span className="text-blue-500">{statusKey}...</span>}
          {isPending && <span className="text-gray-400">pending</span>}
          {isPaused && <span className="text-yellow-500">paused</span>}
          {isFailed && <span className="text-red-500" title={item.error || 'Failed'}><Warning className="w-1.5 h-1.5 inline mr-0.5" />{item.error ? item.error.slice(0, 50) : 'Failed'}</span>}
          {isQueued && <span className="text-yellow-500">queued</span>}
          {isDone && <span className="text-green-500">done</span>}
        </span>
        <div className="flex items-center gap-0 shrink-0">
          {isFailed && item.error && (
            <Button variant="ghost" size="icon" className="h-3 w-3 shrink-0 text-red-400 hover:bg-red-500/10" onClick={(e) => { e.stopPropagation(); navigator.clipboard.writeText(item.error); setToast('Error copied!') }} title="Copy error message">
              <Copy className="w-1.5 h-1.5" />
            </Button>
          )}
          {(isQueued || isPending) && onProcess && (
            <Button size="sm" onClick={handleProcess} disabled={processing} className="h-3.5 px-1 text-[0.4rem] gap-0.5 shrink-0">
              <Rocket className="w-1.5 h-1.5" /> Start
            </Button>
          )}
          {isProcessing && onPause && (
            <Button variant="ghost" size="icon" className="h-3 w-3 shrink-0 text-yellow-500 hover:bg-yellow-500/10" onClick={onPause} title="Pause">
              <Pause className="w-1.5 h-1.5" />
            </Button>
          )}
          {isProcessing && onReprocess && (
            <Button variant="ghost" size="icon" className="h-3 w-3 shrink-0 text-orange-500 hover:bg-orange-500/10" onClick={handleReprocess} title="Restart from scratch">
              <Repeat className={cn("w-1.5 h-1.5", processing && "animate-spin")} />
            </Button>
          )}
          {isFailed && onProcess && (
            <Button variant="ghost" size="icon" className="h-3 w-3 shrink-0 text-green-500 hover:bg-green-500/10" onClick={handleProcess} title="Retry">
              <Repeat className={cn("w-1.5 h-1.5", processing && "animate-spin")} />
            </Button>
          )}
          {onReset && (isQueued || isProcessing || isPaused || isFailed) && (
            <Button variant="ghost" size="icon" className="h-3 w-3 shrink-0 text-orange-500 hover:bg-orange-500/10" onClick={onReset} title="Reset">
              <ArrowBendUpLeft className="w-1.5 h-1.5" />
            </Button>
          )}
          {onDelete && (
            <Button variant="ghost" size="icon" className="h-3 w-3 shrink-0 text-destructive hover:bg-destructive/10" onClick={onDelete} title="Remove">
              <Trash className="w-1.5 h-1.5" />
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}
