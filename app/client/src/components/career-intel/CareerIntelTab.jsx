import { useState, useEffect, useCallback } from 'react'
import {
  ChartBar, Target, Brain, Buildings, Users, Lightbulb, ArrowsClockwise,
  Check, Spinner, Warning, Globe, MagnifyingGlass, Clipboard, CheckCircle, Clock, X, List
} from '@phosphor-icons/react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { toast } from 'sonner'

import OverviewSection from './OverviewSection'
import OpportunitiesSection from './OpportunitiesSection'
import CompaniesSection from './CompaniesSection'
import SkillsIntelSection from './SkillsIntelSection'
import MarketIntelSection from './MarketIntelSection'
import NetworkingIntelSection from './NetworkingIntelSection'

const INTEL_STEPS = [
  { key: 'collect', icon: <Globe className="w-3 h-3" />, label: 'Collecting data' },
  { key: 'analyze', icon: <Brain className="w-3 h-3" />, label: 'AI analysis' },
  { key: 'metrics', icon: <MagnifyingGlass className="w-3 h-3" />, label: 'Calculating metrics' },
  { key: 'save', icon: <Clipboard className="w-3 h-3" />, label: 'Saving results' },
  { key: 'done', icon: <CheckCircle className="w-3 h-3" />, label: 'Complete' },
]

function formatElapsed(seconds) {
  if (!seconds && seconds !== 0) return ''
  if (seconds < 60) return `${seconds}s`
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}m ${s}s`
}

function IntelProgressCard({ progress, elapsed, onCancel }) {
  if (!progress.running) return null
  const elapsedSec = elapsed || progress.elapsed_seconds || 0

  // Simulate step progression based on elapsed time
  const getStepIndex = (secs) => {
    if (secs < 10) return 0
    if (secs < 30) return 1
    if (secs < 60) return 2
    if (secs < 90) return 3
    return 4
  }
  const currentStep = getStepIndex(elapsedSec)

  return (
    <Card className="p-4 border-primary/30 bg-primary/5">
      <div className="flex items-center gap-2 mb-3">
        <Spinner className="w-4 h-4 text-primary animate-spin" />
        <span className="text-sm font-bold">Generating Career Intelligence</span>
        <Badge variant="default" className="text-[0.5rem] animate-pulse">LIVE</Badge>
        <div className="ml-auto flex items-center gap-2">
          <span className="text-[0.55rem] text-muted-foreground">{progress.type === 'all' ? 'All sections' : progress.type}</span>
          {onCancel && (
            <Button variant="destructive" size="sm" onClick={onCancel} className="h-6 gap-1 text-[0.55rem]">
              <X className="w-3 h-3" /> Terminate
            </Button>
          )}
        </div>
      </div>

      {/* Step progress bar */}
      <div className="flex gap-1 mb-3">
        {INTEL_STEPS.map((step, i) => {
          const isDone = i < currentStep
          const isActive = i === currentStep
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
              {i < INTEL_STEPS.length - 1 && <div className={cn("h-[1px] flex-1 rounded-full", isDone ? "bg-green-500" : "bg-border")} />}
            </div>
          )
        })}
      </div>

      {/* Step labels */}
      <div className="flex gap-1 mb-2">
        {INTEL_STEPS.map((step, i) => (
          <div key={step.key} className="flex-1 text-center">
            <span className={cn("text-[0.5rem]",
              i < currentStep ? "text-green-500 font-semibold" :
              i === currentStep ? "text-primary font-semibold" : "text-muted-foreground"
            )}>
              {i < currentStep ? '✓ ' : i === currentStep ? '● ' : ''}{step.label}
            </span>
          </div>
        ))}
      </div>

      {/* Progress + elapsed */}
      <div className="flex items-center gap-2">
        <Progress value={(currentStep / (INTEL_STEPS.length - 1)) * 100} className="h-1 flex-1" />
        <span className="text-[0.55rem] text-muted-foreground shrink-0">{formatElapsed(elapsedSec)}</span>
      </div>
    </Card>
  )
}

function HistoryList({ runs }) {
  const [expanded, setExpanded] = useState(false)
  if (!runs || runs.length === 0) return null
  return (
    <Card className="p-3">
      <button onClick={() => setExpanded(!expanded)} className="flex items-center gap-2 w-full text-left">
        <List className="w-4 h-4 text-muted-foreground" />
        <span className="text-xs font-bold">Analysis History</span>
        <Badge variant="secondary" className="text-[0.5rem] ml-auto">{runs.length}</Badge>
        <span className="text-[0.5rem] text-muted-foreground">{expanded ? '▲' : '▼'}</span>
      </button>
      {expanded && (
        <div className="mt-2 space-y-1 max-h-[200px] overflow-y-auto">
          {runs.map((run, i) => (
            <div key={run.id || i} className="flex items-center gap-2 text-[0.6rem] p-1.5 rounded hover:bg-muted transition">
              <div className={cn("w-2 h-2 rounded-full shrink-0",
                run.status === 'completed' ? "bg-green-500" :
                run.status === 'failed' ? "bg-red-500" :
                run.status === 'cancelled' ? "bg-yellow-500" :
                run.status === 'processing' ? "bg-blue-500 animate-pulse" : "bg-gray-400"
              )} />
              <span className="font-semibold capitalize w-16">{run.insight_type}</span>
              <span className="text-muted-foreground">v{run.version}</span>
              <span className={cn("font-semibold",
                run.status === 'completed' ? "text-green-500" :
                run.status === 'failed' ? "text-red-500" :
                run.status === 'cancelled' ? "text-yellow-500" : "text-muted-foreground"
              )}>{run.status}</span>
              {run.session_id && (
                <span className="text-muted-foreground text-[0.5rem] truncate max-w-[120px]" title={run.session_id}>{run.session_id}</span>
              )}
              <span className="text-muted-foreground ml-auto">{formatTimestamp(run.started_at)}</span>
              {run.error_message && <Warning className="w-3 h-3 text-red-500 shrink-0" title={run.error_message} />}
            </div>
          ))}
        </div>
      )}
    </Card>
  )
}

function formatTimestamp(ts) {
  if (!ts) return null
  const date = new Date(ts)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)
  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return date.toLocaleDateString()
}

export default function CareerIntelTab({ data, status, progress, activeTab, setActiveTab, refreshing, error, onRefreshAll, onRefreshSection, onOpenDrawer, onCancel }) {
  // Unwrap data: API returns { overview: { id, data: {...} }, ... } → sections expect { overview: {...}, ... }
  const unwrappedData = {}
  if (data) {
    for (const [key, val] of Object.entries(data)) {
      if (val && typeof val === 'object' && val.data) {
        unwrappedData[key] = val.data
      } else {
        unwrappedData[key] = val
      }
    }
  }
  const hasData = unwrappedData && Object.keys(unwrappedData).length > 0
  const isRunning = progress?.running || refreshing.all
  const [runs, setRuns] = useState([])

  const fetchRuns = useCallback(() => {
    fetch('/api/career-intelligence/runs?limit=20')
      .then(r => r.ok ? r.json() : [])
      .then(d => setRuns(d))
      .catch(() => setRuns([]))
  }, [])

  useEffect(() => { fetchRuns() }, [fetchRuns])
  // Refresh runs when analysis completes
  useEffect(() => { if (!isRunning) fetchRuns() }, [isRunning, fetchRuns])
  const [elapsed, setElapsed] = useState(0)

  // Elapsed timer when running
  useEffect(() => {
    if (!progress.running) { setElapsed(0); return }
    const start = progress.started_at ? new Date(progress.started_at).getTime() : Date.now()
    const timer = setInterval(() => {
      setElapsed(Math.floor((Date.now() - start) / 1000))
    }, 1000)
    return () => clearInterval(timer)
  }, [progress.running, progress.started_at])

  // Show error toast
  useEffect(() => {
    if (error) toast.error(error)
  }, [error])

  const overallTimestamp = status?._currentRun?.started_at || null
  // Find the most recent error from any section
  const lastError = Object.values(status).find(s => s?.status === 'failed' && s?.error)

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h2 className="text-xl font-extrabold">Career Intelligence</h2>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="bg-muted">
              <TabsTrigger value="overview"><Lightbulb className="w-4 h-4 mr-1.5" />Overview</TabsTrigger>
              <TabsTrigger value="opportunities"><Target className="w-4 h-4 mr-1.5" />Opportunities</TabsTrigger>
              <TabsTrigger value="companies"><Buildings className="w-4 h-4 mr-1.5" />Companies</TabsTrigger>
              <TabsTrigger value="skills"><Brain className="w-4 h-4 mr-1.5" />Skills</TabsTrigger>
              <TabsTrigger value="market"><ChartBar className="w-4 h-4 mr-1.5" />Market</TabsTrigger>
              <TabsTrigger value="networking"><Users className="w-4 h-4 mr-1.5" />Networking</TabsTrigger>
            </TabsList>
          </Tabs>
        </div>
        <div className="flex items-center gap-2">
          {overallTimestamp && (
            <span className="text-[0.55rem] text-muted-foreground flex items-center gap-1">
              <Clock className="w-3 h-3" /> {formatTimestamp(overallTimestamp)}
            </span>
          )}
          <Button onClick={onRefreshAll} disabled={isRunning} variant={isRunning ? "secondary" : "outline"} size="sm" className="gap-1.5">
            <ArrowsClockwise className={cn("w-3.5 h-3.5", isRunning && "animate-spin")} />
            {isRunning ? 'Generating...' : 'Generate All'}
          </Button>
        </div>
      </div>

      {/* Progress Card — shown when analysis is running */}
      <IntelProgressCard progress={progress} elapsed={elapsed} onCancel={onCancel} />

      {/* Error Banner — shown when last run failed */}
      {!isRunning && lastError && !hasData && (
        <Card className="p-4 border-red-500/30 bg-red-500/5">
          <div className="flex items-start gap-2">
            <Warning className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
            <div className="flex-1">
              <div className="text-xs font-bold text-red-500">Analysis Failed</div>
              <div className="text-[0.6rem] text-muted-foreground mt-0.5">{lastError.error}</div>
              <div className="text-[0.55rem] text-muted-foreground mt-1">Last attempted: {formatTimestamp(lastError.lastRun)}</div>
            </div>
            <Button onClick={onRefreshAll} size="sm" variant="outline" className="gap-1 h-6 text-[0.55rem] shrink-0">
              <ArrowsClockwise className="w-3 h-3" /> Retry
            </Button>
          </div>
        </Card>
      )}

      {/* Workflow Status Cards — shown when data exists and not running */}
      {hasData && !isRunning && (
        <div className="grid grid-cols-6 gap-2">
          {['overview', 'opportunities', 'companies', 'skills', 'market', 'networking'].map(s => (
            <div key={s} className={cn(
              "p-2 rounded-lg border text-center transition cursor-pointer hover:border-primary",
              status[s]?.status === 'completed' ? "border-green-500/30 bg-green-500/5" :
              status[s]?.status === 'failed' ? "border-red-500/30 bg-red-500/5" :
              "border-border"
            )} onClick={() => setActiveTab(s)}>
              <div className={cn("text-[0.55rem] font-bold capitalize mb-0.5", s)}>{s}</div>
              <div className={cn("text-[0.5rem]",
                status[s]?.status === 'completed' ? "text-green-500" :
                status[s]?.status === 'failed' ? "text-red-500" :
                status[s]?.status === 'processing' ? "text-primary" :
                "text-muted-foreground"
              )}>
                {status[s]?.status === 'completed' ? '✓ Done' :
                 status[s]?.status === 'failed' ? '✗ Failed' :
                 status[s]?.status === 'processing' ? '● Running' :
                 status[s]?.status === 'never' ? 'Never run' :
                 status[s]?.status || 'Unknown'}
              </div>
              {status[s]?.error && (
                <div className="text-[0.45rem] text-red-500 mt-0.5 truncate" title={status[s].error}>{status[s].error.slice(0, 30)}</div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* History List */}
      {!isRunning && <HistoryList runs={runs} />}

      {/* Empty State */}
      {!hasData && !isRunning && (
        <Card className="p-8 text-center border-dashed">
          <Lightbulb className="w-10 h-10 mx-auto mb-3 text-muted-foreground/40" />
          <p className="text-sm font-semibold mb-1">No career intelligence yet</p>
          <p className="text-xs text-muted-foreground mb-4">Click "Generate All" to create actionable insights from your processed jobs, companies, and skills data.</p>
          <Button onClick={onRefreshAll} size="sm" className="gap-1.5">
            <ArrowsClockwise className="w-3.5 h-3.5" /> Generate Intelligence
          </Button>
        </Card>
      )}

      {/* Sections — shown when data exists and not running */}
      {hasData && activeTab === 'overview' && (
        <OverviewSection data={unwrappedData} refreshing={refreshing} onRefresh={() => onRefreshSection('overview')} />
      )}
      {hasData && activeTab === 'opportunities' && (
        <OpportunitiesSection data={unwrappedData} refreshing={refreshing} onRefresh={() => onRefreshSection('opportunities')} onOpenDrawer={onOpenDrawer} />
      )}
      {hasData && activeTab === 'companies' && (
        <CompaniesSection data={unwrappedData} refreshing={refreshing} onRefresh={() => onRefreshSection('companies')} />
      )}
      {hasData && activeTab === 'skills' && (
        <SkillsIntelSection data={unwrappedData} refreshing={refreshing} onRefresh={() => onRefreshSection('skills')} />
      )}
      {hasData && activeTab === 'market' && (
        <MarketIntelSection data={unwrappedData} refreshing={refreshing} onRefresh={() => onRefreshSection('market')} />
      )}
      {hasData && activeTab === 'networking' && (
        <NetworkingIntelSection data={unwrappedData} refreshing={refreshing} onRefresh={() => onRefreshSection('networking')} />
      )}
    </div>
  )
}
