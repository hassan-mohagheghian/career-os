import {
  Brain, Target, Warning, Lightning, ArrowsClockwise, ArrowRight,
} from '@phosphor-icons/react'
import { cn } from '@/shared/lib/utils'
import SkillsIntelSection from '@/features/insights/components/SkillsIntelSection'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { useSkills } from '../hooks/useSkills'

function MiniStat({ label, value, color }: { label: string; value: number | string; color?: string }) {
  return (
    <div className="flex items-center gap-1.5">
      <span className={cn("text-lg font-extrabold", color)}>{value}</span>
      <span className="text-2xs text-muted-foreground">{label}</span>
    </div>
  )
}

export default function SkillsTab({ deepLinkSkill, onClearDeepLink }: { deepLinkSkill?: string | null; onClearDeepLink?: () => void } = {}) {
  const {
    skillRoadmapProgress, skillGenJobs,
    refreshSkillRoadmapProgress, dashboardData,
    refresh, refreshing,
  } = useSkills()

  const activeJobs = skillGenJobs.filter((j: any) => j.status === 'running' || j.status === 'queued')
  const summary = dashboardData?.summary || {}
  const isRunning = refreshing || activeJobs.length > 0

  return (
    <div className="space-y-5">
      {/* Intelligence Summary Header */}
      {summary.total_skills > 0 && (
        <Card className="p-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-1.5">
                <Brain className="w-4 h-4 text-primary" />
                <span className="text-xs font-extrabold">Skills Overview</span>
              </div>
              <MiniStat label="skills" value={summary.total_skills} color="text-blue-500" />
              <MiniStat label="strengths" value={summary.strengths_count} color="text-green-500" />
              <MiniStat label="gaps" value={summary.gaps_count} color="text-orange-500" />
              <MiniStat label="roadmaps" value={summary.roadmap_skills} color="text-purple-500" />
              {summary.career_readiness_score > 0 && (
                <div className="flex items-center gap-1">
                  <span className={cn("text-lg font-extrabold",
                    summary.career_readiness_score >= 70 ? "text-green-500" :
                    summary.career_readiness_score >= 40 ? "text-yellow-500" : "text-red-500"
                  )}>{summary.career_readiness_score}</span>
                  <span className="text-2xs text-muted-foreground">readiness</span>
                </div>
              )}
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="ghost" size="sm"
                onClick={() => window.location.hash = 'insights/skills'}
                className="gap-1 h-6 text-2xs"
              >
                Full Intelligence <ArrowRight className="w-3 h-3" />
              </Button>
              <Button
                variant="outline" size="sm"
                onClick={refresh}
                disabled={isRunning}
                className="gap-1 h-6 text-2xs"
              >
                <ArrowsClockwise className={cn("w-3 h-3", isRunning && "animate-spin")} />
                {isRunning ? 'Analyzing...' : 'Refresh'}
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Full Skills Management — with intelligence data */}
      <SkillsIntelSection
        data={dashboardData?.intel_report ? { skills_intel: dashboardData.intel_report.data } : {}}
        refreshing={{}}
        onRefresh={refresh}
        roadmapProgress={skillRoadmapProgress}
        onRefreshProgress={refreshSkillRoadmapProgress}
        genJobs={activeJobs}
        status={{}}
        deepLinkSkill={deepLinkSkill}
        onClearDeepLink={onClearDeepLink}
      />
    </div>
  )
}
