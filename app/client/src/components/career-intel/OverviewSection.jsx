import {
  Briefcase, Target, Rocket, IdentificationCard, Buildings, Brain, Lightning,
  TrendUp, ArrowsClockwise, CheckCircle, Warning, Circle
} from '@phosphor-icons/react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'

function HealthGauge({ score, label }) {
  const color = score >= 70 ? 'text-green-500' : score >= 50 ? 'text-yellow-500' : 'text-red-500'
  const bgColor = score >= 70 ? 'bg-green-500' : score >= 50 ? 'bg-yellow-500' : 'bg-red-500'
  return (
    <div className="flex flex-col items-center">
      <div className="relative w-24 h-24">
        <svg className="w-24 h-24 -rotate-90" viewBox="0 0 100 100">
          <circle cx="50" cy="50" r="40" fill="none" stroke="currentColor" strokeWidth="8" className="text-muted/30" />
          <circle cx="50" cy="50" r="40" fill="none" strokeWidth="8" strokeLinecap="round"
            strokeDasharray={`${(score / 100) * 251} 251`} className={bgColor} />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className={cn("text-2xl font-extrabold", color)}>{score}</span>
        </div>
      </div>
      <span className="text-[0.6rem] text-muted-foreground mt-1">{label}</span>
    </div>
  )
}

function BreakdownBar({ label, value, color }) {
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-[0.6rem]">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-bold">{value}/100</span>
      </div>
      <Progress value={value} className="h-1.5" />
    </div>
  )
}

function ActionCard({ action }) {
  const impactColors = {
    high: 'border-l-red-500 bg-red-500/5',
    medium: 'border-l-yellow-500 bg-yellow-500/5',
    low: 'border-l-blue-500 bg-blue-500/5'
  }
  const impactBadge = {
    high: 'bg-red-500/15 text-red-500',
    medium: 'bg-yellow-500/15 text-yellow-500',
    low: 'bg-blue-500/15 text-blue-500'
  }
  return (
    <div className={cn("flex items-start gap-3 p-3 rounded-lg border-l-3 transition hover:bg-muted", impactColors[action.impact])}>
      <div className="shrink-0 mt-0.5">
        <span className="flex items-center justify-center w-5 h-5 rounded-full bg-primary/10 text-primary text-[0.6rem] font-bold">
          {action.priority}
        </span>
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-xs font-bold">{action.action}</div>
        <div className="text-[0.6rem] text-muted-foreground mt-0.5">{action.reason}</div>
      </div>
      <Badge variant="secondary" className={cn("text-[0.45rem] h-3.5 shrink-0", impactBadge[action.impact])}>
        {action.impact}
      </Badge>
    </div>
  )
}

export default function OverviewSection({ data, refreshing, onRefresh }) {
  const overview = data?.overview || {}
  const position = overview.position || {}
  const health = overview.careerHealthScore || {}
  const breakdown = health.breakdown || {}
  const actions = overview.nextActions || []

  const statCards = [
    { n: position.totalJobs || 0, l: 'Total Jobs', c: 'text-primary', icon: <Briefcase className="w-5 h-5" /> },
    { n: position.highMatchJobs || 0, l: 'High Match', c: 'text-green-500', icon: <Target className="w-5 h-5" /> },
    { n: position.applyNowJobs || 0, l: 'Apply Now', c: 'text-yellow-500', icon: <Rocket className="w-5 h-5" /> },
    { n: position.visaFriendlyCompanies || 0, l: 'Visa Friendly', c: 'text-purple-500', icon: <IdentificationCard className="w-5 h-5" /> },
    { n: position.targetCompanies || 0, l: 'Target Companies', c: 'text-cyan-500', icon: <Buildings className="w-5 h-5" /> },
    { n: `${position.skillMatchPercentage || 0}%`, l: 'Skill Match', c: 'text-orange-500', icon: <Brain className="w-5 h-5" /> },
  ]

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h3 className="font-extrabold text-sm">Career Command Center</h3>
        <Button variant="ghost" size="sm" onClick={onRefresh} disabled={refreshing.overview} className="gap-1 h-6 text-[0.55rem]">
          <ArrowsClockwise className={cn("w-3 h-3", refreshing.overview && "animate-spin")} /> Refresh
        </Button>
      </div>

      {/* Position Cards */}
      <div className="grid grid-cols-6 gap-3">
        {statCards.map((s, i) => (
          <Card key={i} className="p-3 text-center transition hover:border-primary">
            <div className={cn("mb-1", s.c)}>{s.icon}</div>
            <div className={cn("text-xl font-extrabold", s.c)}>{s.n}</div>
            <div className="text-[0.6rem] uppercase tracking-wider text-muted-foreground">{s.l}</div>
          </Card>
        ))}
      </div>

      {/* Biggest Skill Gaps */}
      {position.biggestSkillGaps?.length > 0 && (
        <Card className="p-4">
          <div className="flex items-center gap-2 mb-2">
            <Warning className="w-4 h-4 text-yellow-500" />
            <h4 className="font-extrabold text-xs">Biggest Skill Gaps</h4>
          </div>
          <div className="flex flex-wrap gap-2">
            {position.biggestSkillGaps.map((gap, i) => (
              <Badge key={i} variant="secondary" className="text-[0.6rem] bg-yellow-500/15 text-yellow-500">{gap}</Badge>
            ))}
          </div>
        </Card>
      )}

      <div className="grid grid-cols-[320px_1fr] gap-4">
        {/* Career Health Score */}
        <div className="space-y-4">
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-4">
              <TrendUp className="w-5 h-5 text-primary" />
              <h4 className="font-extrabold text-sm">Career Health Score</h4>
            </div>
            <div className="flex justify-center mb-4">
              <HealthGauge score={health.overall || 0} label="Career Readiness" />
            </div>
            <div className="space-y-3">
              <BreakdownBar label="Job Market Fit" value={breakdown.jobMarketFit || 0} />
              <BreakdownBar label="Company Fit" value={breakdown.companyFit || 0} />
              <BreakdownBar label="Visa Probability" value={breakdown.visaProbability || 0} />
              <BreakdownBar label="Skill Alignment" value={breakdown.skillAlignment || 0} />
              <BreakdownBar label="Networking Status" value={breakdown.networkingStatus || 0} />
            </div>
          </Card>
        </div>

        {/* Recommended Next Actions */}
        <Card className="p-4">
          <div className="flex items-center gap-2 mb-3">
            <Lightning className="w-5 h-5 text-yellow-500" />
            <h4 className="font-extrabold text-sm">Recommended Next Actions</h4>
          </div>
          <div className="space-y-2">
            {actions.length > 0 ? actions.map((action, i) => (
              <ActionCard key={i} action={action} />
            )) : (
              <div className="text-xs text-muted-foreground text-center py-4">
                Generate intelligence to see recommended actions
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  )
}
