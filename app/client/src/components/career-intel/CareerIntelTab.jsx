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
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from '@/components/ui/sheet'
import { toast } from 'sonner'
import GenerationProgressCard from '@/components/shared/GenerationProgressCard'

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

  return (
    <GenerationProgressCard
      title="Generating Career Intelligence"
      type={progress.type === 'all' ? 'All sections' : progress.type}
      progress={{ ...progress, elapsed_seconds: elapsed || progress.elapsed_seconds }}
      steps={INTEL_STEPS.map(s => ({ key: s.key, label: s.label }))}
      onCancel={onCancel}
    />
  )
}

function HistoryDrawer({ runs, roadmapJobs, runsTotal, roadmapTotal, onLoadMoreRuns, onLoadMoreRoadmapJobs, open, onOpenChange }) {
  const allHistory = [
    ...runs.map(r => ({ ...r, source: 'career-intel' })),
    ...roadmapJobs.map(j => ({
      id: j.id || `roadmap-${j.skill_name}`,
      insight_type: `roadmap: ${j.skill_name}`,
      job_type: j.job_type,
      status: j.status,
      version: j.version,
      started_at: j.started_at,
      completed_at: j.completed_at,
      error_message: j.error,
      session_id: j.session_id,
      source: 'roadmap'
    }))
  ].sort((a, b) => {
    const dateA = a.started_at ? new Date(a.started_at) : new Date(0)
    const dateB = b.started_at ? new Date(b.started_at) : new Date(0)
    return dateB - dateA
  })

  const totalAll = runsTotal + roadmapTotal
  const hasMoreRuns = runs.length < runsTotal
  const hasMoreRoadmap = roadmapJobs.length < roadmapTotal

  const scrollRef = useCallback((node) => {
    if (!node) return
    const handleScroll = () => {
      if (node.scrollTop + node.clientHeight >= node.scrollHeight - 50) {
        if (hasMoreRuns) onLoadMoreRuns?.()
        if (hasMoreRoadmap) onLoadMoreRoadmapJobs?.()
      }
    }
    node.addEventListener('scroll', handleScroll)
    return () => node.removeEventListener('scroll', handleScroll)
  }, [hasMoreRuns, hasMoreRoadmap, onLoadMoreRuns, onLoadMoreRoadmapJobs])

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-[400px] sm:w-[500px] p-0">
        <SheetHeader className="p-6 pb-4">
          <SheetTitle className="flex items-center gap-2">
            <List className="w-5 h-5" />
            Generation History
          </SheetTitle>
          <SheetDescription>
            {totalAll} total generation runs
          </SheetDescription>
        </SheetHeader>
        <div ref={scrollRef} className="px-6 pb-6 space-y-1 overflow-y-auto h-[calc(100vh-120px)]">
          {allHistory.map((run, i) => (
            <div key={run.id || i} className="flex items-center gap-2 text-xs p-2 rounded hover:bg-muted transition">
              <div className={cn("w-2.5 h-2.5 rounded-full shrink-0",
                run.status === 'completed' ? "bg-green-500" :
                run.status === 'failed' ? "bg-red-500" :
                run.status === 'cancelled' ? "bg-yellow-500" :
                run.status === 'processing' || run.status === 'running' ? "bg-blue-500 animate-pulse" : "bg-gray-400"
              )} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-semibold capitalize">
                    {run.source === 'roadmap' ? `${run.job_type || 'generate'}: ${run.insight_type.replace('roadmap: ', '')}` : run.insight_type}
                  </span>
                  {run.version && <span className="text-muted-foreground text-[0.6rem]">v{run.version}</span>}
                  <span className={cn("font-semibold text-[0.6rem]",
                    run.status === 'completed' ? "text-green-500" :
                    run.status === 'failed' ? "text-red-500" :
                    run.status === 'cancelled' ? "text-yellow-500" : "text-muted-foreground"
                  )}>{run.status}</span>
                  <Badge variant="secondary" className={cn("text-[0.4rem] h-3",
                    run.source === 'roadmap' ? "bg-purple-500/15 text-purple-500" : "bg-blue-500/15 text-blue-500"
                  )}>
                    {run.source === 'roadmap' ? 'Roadmap' : 'Intel'}
                  </Badge>
                </div>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="text-muted-foreground text-[0.6rem]">{formatTimestamp(run.started_at)}</span>
                  {run.session_id ? (
                    <span className="text-muted-foreground text-[0.5rem] font-mono truncate max-w-[140px]" title={run.session_id}>{run.session_id}</span>
                  ) : (
                    <span className="text-muted-foreground/50 text-[0.5rem]">no_session_id</span>
                  )}
                </div>
                {run.error_message && (
                  <div className="text-red-500 text-[0.6rem] mt-0.5 flex items-center gap-1">
                    <Warning className="w-3 h-3 shrink-0" />
                    <span className="truncate">{run.error_message}</span>
                  </div>
                )}
              </div>
            </div>
          ))}
          {allHistory.length === 0 && (
            <div className="text-center py-8 text-muted-foreground text-sm">
              No generation runs yet
            </div>
          )}
          {(hasMoreRuns || hasMoreRoadmap) && allHistory.length > 0 && (
            <div className="text-center py-2 text-muted-foreground text-[0.6rem]">
              Loading more...
            </div>
          )}
        </div>
      </SheetContent>
    </Sheet>
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

export default function CareerIntelTab({ data, status, progress, activeTab, setActiveTab, refreshing, error, onRefreshAll, onRefreshSection, onOpenDrawer, onOpenCompany, onAddCompany, onCancel, skillRoadmapProgress, onRefreshSkillProgress, skillGenJobs }) {
  // Wrap setActiveTab to also update URL hash
  const switchSubTab = (sub) => {
    setActiveTab(sub)
    window.location.hash = `career-intel/${sub}`
  }
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
  const [runsTotal, setRunsTotal] = useState(0)
  const [roadmapJobs, setRoadmapJobs] = useState([])
  const [roadmapTotal, setRoadmapTotal] = useState(0)
  const [historyOpen, setHistoryOpen] = useState(false)

  const PAGE_SIZE = 20

  const fetchRuns = useCallback((offset = 0, append = false) => {
    fetch(`/api/career-intelligence/runs?limit=${PAGE_SIZE}&offset=${offset}`)
      .then(r => r.ok ? r.json() : { items: [], total: 0 })
      .then(d => {
        const items = d.items || []
        const total = d.total || 0
        setRunsTotal(total)
        setRuns(prev => append ? [...prev, ...items] : items)
      })
      .catch(() => { if (!append) setRuns([]) })
  }, [])

  const fetchRoadmapJobs = useCallback((offset = 0, append = false) => {
    fetch(`/api/skill-roadmap-jobs?limit=${PAGE_SIZE}&offset=${offset}`)
      .then(r => r.ok ? r.json() : { items: [], total: 0 })
      .then(d => {
        const items = d.items || []
        const total = d.total || 0
        setRoadmapTotal(total)
        setRoadmapJobs(prev => append ? [...prev, ...items] : items)
      })
      .catch(() => { if (!append) setRoadmapJobs([]) })
  }, [])

  const loadMoreRuns = useCallback(() => {
    if (runs.length < runsTotal) fetchRuns(runs.length, true)
  }, [runs.length, runsTotal, fetchRuns])

  const loadMoreRoadmapJobs = useCallback(() => {
    if (roadmapJobs.length < roadmapTotal) fetchRoadmapJobs(roadmapJobs.length, true)
  }, [roadmapJobs.length, roadmapTotal, fetchRoadmapJobs])

  useEffect(() => { fetchRuns(); fetchRoadmapJobs() }, [fetchRuns, fetchRoadmapJobs])
  // Refresh runs when analysis completes
  useEffect(() => { if (!isRunning) { fetchRuns(); fetchRoadmapJobs() } }, [isRunning, fetchRuns, fetchRoadmapJobs])
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
          <Tabs value={activeTab} onValueChange={switchSubTab}>
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
          <Button variant="ghost" size="sm" onClick={() => setHistoryOpen(true)} className="gap-1.5 h-8">
            <List className="w-3.5 h-3.5" />
            History
            {runsTotal + roadmapTotal > 0 && <Badge variant="secondary" className="text-[0.5rem] h-4 ml-0.5">{runsTotal + roadmapTotal}</Badge>}
          </Button>
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

      {/* History Drawer */}
      <HistoryDrawer runs={runs} roadmapJobs={roadmapJobs} runsTotal={runsTotal} roadmapTotal={roadmapTotal}
        onLoadMoreRuns={loadMoreRuns} onLoadMoreRoadmapJobs={loadMoreRoadmapJobs}
        open={historyOpen} onOpenChange={setHistoryOpen} />

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
        <CompaniesSection data={unwrappedData} refreshing={refreshing} onRefresh={() => onRefreshSection('companies')} onOpenCompany={onOpenCompany} onAddCompany={onAddCompany} />
      )}
      {hasData && activeTab === 'skills' && (
        <SkillsIntelSection data={unwrappedData} refreshing={refreshing} onRefresh={() => onRefreshSection('skills')} roadmapProgress={skillRoadmapProgress} onRefreshProgress={onRefreshSkillProgress} genJobs={skillGenJobs} />
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
