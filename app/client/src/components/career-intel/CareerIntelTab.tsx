import { useState, useEffect } from 'react'
import {
  ChartBar, Target, Brain, Buildings, Users, Lightbulb, ArrowsClockwise,
  Check, Warning, Globe, MagnifyingGlass, Clipboard, CheckCircle, Clock,
} from '@phosphor-icons/react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
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

function formatElapsed(seconds: number): string {
  if (!seconds && seconds !== 0) return ''
  if (seconds < 60) return `${seconds}s`
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}m ${s}s`
}

function IntelProgressCard({ progress, elapsed, onCancel }: { progress: any; elapsed: number; onCancel: () => void }) {
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

function formatTimestamp(ts: string | null): string | null {
  if (!ts) return null
  const date = new Date(ts)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)
  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return date.toLocaleDateString()
}

function SectionTimestamp({ status, sectionKey }: { status: Record<string, any>; sectionKey: string }) {
  const sectionStatus = status?.[sectionKey]
  if (!sectionStatus?.lastRun) return null
  const isError = sectionStatus.status === 'failed'
  return (
    <span className={cn("text-[0.5rem] flex items-center gap-0.5 ml-1.5",
      isError ? "text-red-500" : "text-muted-foreground/60"
    )}>
      <Clock className="w-2.5 h-2.5" />
      {formatTimestamp(sectionStatus.lastRun)}
      {isError && sectionStatus.error && <span title={sectionStatus.error}>!</span>}
    </span>
  )
}

interface CareerIntelTabProps {
  data: Record<string, any> | null
  status: Record<string, any>
  progress: any
  activeTab: string
  setActiveTab: (tab: string) => void
  refreshing: Record<string, boolean>
  error: string | null
  onRefreshAll: () => void
  onRefreshSection: (section: string) => void
  onOpenDrawer: (num: number) => void
  onOpenCompany: (id: number) => void
  onAddCompany: (text: string) => void
  onCancel: () => void
  skillRoadmapProgress: Record<string, any>
  onRefreshSkillProgress: () => void
  skillGenJobs: any[]
}

export default function CareerIntelTab({
  data, status, progress, activeTab, setActiveTab, refreshing, error,
  onRefreshAll, onRefreshSection, onOpenDrawer, onOpenCompany, onAddCompany,
  onCancel, skillRoadmapProgress, onRefreshSkillProgress, skillGenJobs,
}: CareerIntelTabProps) {
  const switchSubTab = (sub: string) => {
    setActiveTab(sub)
    window.location.hash = `career-intel/${sub}`
  }

  const unwrappedData: Record<string, any> = {}
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

  const [elapsed, setElapsed] = useState(0)

  useEffect(() => {
    if (!progress.running) { setElapsed(0); return }
    const start = progress.started_at ? new Date(progress.started_at).getTime() : Date.now()
    const timer = setInterval(() => {
      setElapsed(Math.floor((Date.now() - start) / 1000))
    }, 1000)
    return () => clearInterval(timer)
  }, [progress.running, progress.started_at])

  useEffect(() => {
    if (error) toast.error(error)
  }, [error])

  const overallTimestamp = status?._currentRun?.started_at || null
  const lastError = Object.values(status).find((s: any) => s?.status === 'failed' && s?.error)

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h2 className="text-xl font-extrabold">Career Intelligence</h2>
          <Tabs value={activeTab} onValueChange={switchSubTab}>
            <TabsList className="bg-muted">
              <TabsTrigger value="overview" className="gap-1"><Lightbulb className="w-4 h-4" />Overview<SectionTimestamp status={status} sectionKey="overview" /></TabsTrigger>
              <TabsTrigger value="opportunities" className="gap-1"><Target className="w-4 h-4" />Opportunities<SectionTimestamp status={status} sectionKey="opportunities" /></TabsTrigger>
              <TabsTrigger value="companies" className="gap-1"><Buildings className="w-4 h-4" />Companies<SectionTimestamp status={status} sectionKey="companies" /></TabsTrigger>
              <TabsTrigger value="skills" className="gap-1"><Brain className="w-4 h-4" />Skills<SectionTimestamp status={status} sectionKey="skills_intel" /></TabsTrigger>
              <TabsTrigger value="market" className="gap-1"><ChartBar className="w-4 h-4" />Market<SectionTimestamp status={status} sectionKey="market" /></TabsTrigger>
              <TabsTrigger value="networking" className="gap-1"><Users className="w-4 h-4" />Networking<SectionTimestamp status={status} sectionKey="networking" /></TabsTrigger>
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

      {/* Progress Card */}
      <IntelProgressCard progress={progress} elapsed={elapsed} onCancel={onCancel} />

      {/* Error Banner */}
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

      {/* Sections */}
      {hasData && activeTab === 'overview' && (
        <OverviewSection data={unwrappedData} refreshing={refreshing} onRefresh={() => onRefreshSection('overview')} status={status} />
      )}
      {hasData && activeTab === 'opportunities' && (
        <OpportunitiesSection data={unwrappedData} refreshing={refreshing} onRefresh={() => onRefreshSection('opportunities')} onOpenDrawer={onOpenDrawer} status={status} />
      )}
      {hasData && activeTab === 'companies' && (
        <CompaniesSection data={unwrappedData} refreshing={refreshing} onRefresh={() => onRefreshSection('companies')} onOpenCompany={onOpenCompany} onAddCompany={onAddCompany} status={status} />
      )}
      {hasData && activeTab === 'skills' && (
        <SkillsIntelSection data={unwrappedData} refreshing={refreshing} onRefresh={() => onRefreshSection('skills')} roadmapProgress={skillRoadmapProgress} onRefreshProgress={onRefreshSkillProgress} genJobs={skillGenJobs} status={status} />
      )}
      {hasData && activeTab === 'market' && (
        <MarketIntelSection data={unwrappedData} refreshing={refreshing} onRefresh={() => onRefreshSection('market')} status={status} />
      )}
      {hasData && activeTab === 'networking' && (
        <NetworkingIntelSection data={unwrappedData} refreshing={refreshing} onRefresh={() => onRefreshSection('networking')} status={status} />
      )}
    </div>
  )
}
