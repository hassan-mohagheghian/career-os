import { useState, useEffect } from 'react'
import { Brain, ArrowsClockwise, Clock, Warning } from '@phosphor-icons/react'
import { cn } from '@/shared/lib/utils'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { toast } from 'sonner'
import GenerationProgressCard from '@/shared/components/GenerationProgressCard'
import SkillsIntelSection from '@/features/insights/components/SkillsIntelSection'
import { useSkills } from '../hooks/useSkills'

const SKILLS_STEPS = [
  { key: 'collect', label: 'Collecting data' },
  { key: 'analyze', label: 'AI analysis' },
  { key: 'scoring', label: 'Scoring skills' },
  { key: 'roadmap', label: 'Building roadmap' },
  { key: 'done', label: 'Complete' },
]

function formatTimeAgo(ts: string | null): string | null {
  if (!ts) return null
  const diffMs = Date.now() - new Date(ts).getTime()
  const mins = Math.floor(diffMs / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}d ago`
  return new Date(ts).toLocaleDateString()
}

export default function SkillsTab() {
  const {
    data, status, progress, refreshing, error,
    skillRoadmapProgress, skillGenJobs,
    refresh, cancelRun,
  } = useSkills()

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

  useEffect(() => {
    if (error) toast.error(error)
  }, [error])

  const skillsStatus = status?.skills_intel
  const lastTimestamp = skillsStatus?.lastRun || null

  // Unwrap data: API returns { id, data: {...} } or just {...}
  const unwrappedData: Record<string, any> = {}
  if (data) {
    for (const [key, val] of Object.entries(data)) {
      if (val && typeof val === 'object' && 'data' in val && val.data) {
        unwrappedData[key] = val.data
      } else {
        unwrappedData[key] = val
      }
    }
  }
  const hasData = unwrappedData && Object.keys(unwrappedData).length > 0

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-xl font-extrabold">Skills Intelligence</h2>
          {lastTimestamp && (
            <span className="text-2xs text-muted-foreground flex items-center gap-1">
              <Clock className="w-3 h-3" /> {formatTimeAgo(lastTimestamp)}
            </span>
          )}
        </div>
        <Button
          onClick={refresh}
          disabled={refreshing || progress.running}
          variant={refreshing || progress.running ? "secondary" : "outline"}
          size="sm"
          className="gap-1.5"
        >
          <ArrowsClockwise className={cn("w-3.5 h-3.5", (refreshing || progress.running) && "animate-spin")} />
          {refreshing || progress.running ? 'Generating...' : 'Generate Insights'}
        </Button>
      </div>

      {/* Progress Card */}
      {(refreshing || progress.running) && (
        <GenerationProgressCard
          title="Generating Skills Intelligence"
          type="Skills Analysis"
          progress={{ ...progress, elapsed_seconds: elapsed || progress.elapsed_seconds }}
          steps={SKILLS_STEPS}
          onCancel={cancelRun}
        />
      )}

      {/* Error Banner */}
      {!progress.running && !refreshing && error && !hasData && (
        <Card className="p-4 border-red-500/30 bg-red-500/5">
          <div className="flex items-start gap-2">
            <Warning className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
            <div className="flex-1">
              <div className="text-xs font-bold text-red-500">Analysis Failed</div>
              <div className="text-2xs text-muted-foreground mt-0.5">{error}</div>
            </div>
            <Button onClick={refresh} size="sm" variant="outline" className="gap-1 h-6 text-2xs shrink-0">
              <ArrowsClockwise className="w-3 h-3" /> Retry
            </Button>
          </div>
        </Card>
      )}

      {/* Empty State */}
      {!hasData && !progress.running && !refreshing && (
        <Card className="p-8 text-center border-dashed">
          <Brain className="w-10 h-10 mx-auto mb-3 text-muted-foreground/40" />
          <p className="text-sm font-semibold mb-1">No skills intelligence yet</p>
          <p className="text-xs text-muted-foreground mb-4">Click "Generate Insights" to analyze your skills against the job market and get personalized recommendations.</p>
          <Button onClick={refresh} size="sm" className="gap-1.5">
            <ArrowsClockwise className="w-3.5 h-3.5" /> Generate Insights
          </Button>
        </Card>
      )}

      {/* Skills Content — hide individual genJob cards when main generation is running */}
      {hasData && (
        <SkillsIntelSection
          data={unwrappedData}
          refreshing={{ skills_intel: refreshing }}
          onRefresh={refresh}
          roadmapProgress={skillRoadmapProgress}
          onRefreshProgress={() => {}}
          genJobs={(refreshing || progress.running) ? [] : skillGenJobs}
          status={status}
        />
      )}
    </div>
  )
}
