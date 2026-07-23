import {
  TrendUp, Brain, BookOpen, ChartLineUp, Wrench, ArrowsClockwise
} from '@phosphor-icons/react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'

function SkillRow({ skill, type }) {
  const levelColors = {
    expert: 'bg-green-500/15 text-green-500',
    advanced: 'bg-blue-500/15 text-blue-500',
    intermediate: 'bg-yellow-500/15 text-yellow-500',
    beginner: 'bg-orange-500/15 text-orange-500',
    none: 'bg-red-500/15 text-red-500',
  }
  return (
    <div className="flex items-center gap-2 p-2 rounded hover:bg-muted transition text-xs">
      <span className="font-semibold w-24 truncate">{skill.skill}</span>
      <div className="flex-1 h-[3px] rounded-full bg-muted">
        <div className="h-full rounded-full bg-primary" style={{ width: `${skill.demandPercentage || 0}%` }} />
      </div>
      <span className="w-10 text-right text-[0.55rem] text-muted-foreground">{skill.demandPercentage || 0}%</span>
      <Badge variant="secondary" className={cn("text-[0.45rem] h-3 shrink-0", levelColors[skill.candidateLevel || skill.currentLevel] || 'bg-gray-500/15 text-gray-400')}>
        {skill.candidateLevel || skill.currentLevel}
      </Badge>
    </div>
  )
}

export default function SkillsIntelSection({ data, refreshing, onRefresh }) {
  const skills = data?.skills || {}
  const strengths = skills.strengths || []
  const gaps = skills.gaps || []
  const recommendations = skills.learningRecommendations || []

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h3 className="font-extrabold text-sm">Skills Intelligence</h3>
        <Button variant="ghost" size="sm" onClick={onRefresh} disabled={refreshing.skills} className="gap-1 h-6 text-[0.55rem]">
          <ArrowsClockwise className={cn("w-3 h-3", refreshing.skills && "animate-spin")} /> Refresh
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { n: strengths.length, l: 'Strengths', c: 'text-green-500', icon: <TrendUp className="w-5 h-5" /> },
          { n: gaps.length, l: 'Skill Gaps', c: 'text-red-500', icon: <BookOpen className="w-5 h-5" /> },
          { n: recommendations.length, l: 'Recommendations', c: 'text-blue-500', icon: <Brain className="w-5 h-5" /> },
          { n: recommendations.filter(r => r.roi >= 8).length, l: 'High ROI', c: 'text-yellow-500', icon: <ChartLineUp className="w-5 h-5" /> },
        ].map((s, i) => (
          <Card key={i} className="p-3 text-center transition hover:border-primary">
            <div className={cn("mb-1", s.c)}>{s.icon}</div>
            <div className={cn("text-xl font-extrabold", s.c)}>{s.n}</div>
            <div className="text-[0.6rem] uppercase tracking-wider text-muted-foreground">{s.l}</div>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-[1fr_320px] gap-4">
        <div className="space-y-4">
          {/* Strengths */}
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <TrendUp className="w-5 h-5 text-green-500" />
              <h4 className="font-extrabold text-sm">Strengths</h4>
              <Badge variant="secondary" className="text-[0.5rem] bg-green-500/15 text-green-500">{strengths.length}</Badge>
            </div>
            <div className="space-y-1">
              {strengths.length > 0 ? strengths.map((s, i) => (
                <SkillRow key={i} skill={s} type="strength" />
              )) : (
                <div className="text-xs text-muted-foreground">No strengths identified yet</div>
              )}
            </div>
          </Card>

          {/* Gaps */}
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <BookOpen className="w-5 h-5 text-red-500" />
              <h4 className="font-extrabold text-sm">Skill Gaps</h4>
              <Badge variant="secondary" className="text-[0.5rem] bg-red-500/15 text-red-500">{gaps.length}</Badge>
            </div>
            <div className="space-y-1">
              {gaps.length > 0 ? gaps.map((g, i) => (
                <SkillRow key={i} skill={g} type="gap" />
              )) : (
                <div className="text-xs text-muted-foreground">No major gaps identified</div>
              )}
            </div>
          </Card>
        </div>

        <div className="space-y-4">
          {/* Learning Recommendations */}
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <Brain className="w-5 h-5 text-primary" />
              <h4 className="font-extrabold text-sm">Learning Recommendations</h4>
            </div>
            <div className="space-y-2">
              {recommendations.length > 0 ? recommendations.map((r, i) => (
                <div key={i} className="p-2 rounded-lg border border-primary/20 bg-primary/5 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-xs">{r.skill}</span>
                    <Badge variant="secondary" className={cn("text-[0.45rem] h-3.5",
                      r.roi >= 8 ? "bg-green-500/15 text-green-500" :
                      r.roi >= 6 ? "bg-yellow-500/15 text-yellow-500" : "bg-gray-500/15 text-gray-400"
                    )}>ROI: {r.roi}/10</Badge>
                  </div>
                  <div className="text-[0.55rem] text-muted-foreground">
                    {r.reason}
                  </div>
                  <div className="flex items-center gap-2 text-[0.5rem] text-muted-foreground">
                    <span>Demand: {r.demandPercentage}%</span>
                    <span>·</span>
                    <span>Effort: {r.learningEffort}</span>
                  </div>
                </div>
              )) : (
                <div className="text-xs text-muted-foreground text-center py-4">No recommendations yet</div>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
