import {
  Target, Rocket, Lightbulb, Lightning, ArrowsClockwise
} from '@phosphor-icons/react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'

export default function OpportunitySection({ analysis, jobs, refreshing, onRefresh, onOpenDrawer }) {
  const opportunity = analysis.opportunity || {}
  const matrix = opportunity.matrix || {}
  const topOpps = opportunity.topOpportunities || []
  const insights = opportunity.insights || []

  const quadrants = [
    { key: 'highFitHighSuccess', label: 'Apply Now', color: 'bg-green-500', textColor: 'text-green-500', borderColor: 'border-green-500/30', icon: <Rocket className="w-4 h-4" /> },
    { key: 'highFitMediumSuccess', label: 'Customize', color: 'bg-blue-500', textColor: 'text-blue-500', borderColor: 'border-blue-500/30', icon: <Target className="w-4 h-4" /> },
    { key: 'mediumFitHighSuccess', label: 'Consider', color: 'bg-yellow-500', textColor: 'text-yellow-500', borderColor: 'border-yellow-500/30', icon: <Lightbulb className="w-4 h-4" /> },
    { key: 'lowFit', label: 'Skip', color: 'bg-gray-500', textColor: 'text-gray-500', borderColor: 'border-gray-500/30', icon: <Lightning className="w-4 h-4" /> },
  ]

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h3 className="font-extrabold text-sm">Opportunity Radar</h3>
        <Button variant="ghost" size="sm" onClick={onRefresh} disabled={refreshing.opportunity} className="gap-1 h-6 text-[0.55rem]">
          <ArrowsClockwise className={cn("w-3 h-3", refreshing.opportunity && "animate-spin")} /> Refresh
        </Button>
      </div>

      {/* Opportunity Matrix */}
      <div className="grid grid-cols-2 gap-3">
        {quadrants.map((q) => {
          const data = matrix[q.key] || { count: 0, jobs: [] }
          return (
            <Card key={q.key} className={cn("p-4 border", q.borderColor)}>
              <div className="flex items-center gap-2 mb-2">
                <div className={q.textColor}>{q.icon}</div>
                <h4 className="font-bold text-sm">{q.label}</h4>
                <Badge variant="secondary" className={cn("text-[0.5rem]", q.textColor)}>{data.count} jobs</Badge>
              </div>
              {data.jobs && data.jobs.length > 0 ? (
                <div className="space-y-1.5">
                  {data.jobs.slice(0, 4).map((job, i) => (
                    <div key={i} className="flex items-center justify-between text-[0.6rem] p-1.5 rounded hover:bg-muted transition">
                      <div className="flex items-center gap-2 min-w-0">
                        <span className="font-semibold truncate">{job.company}</span>
                        <span className="text-muted-foreground truncate">{job.role}</span>
                      </div>
                      <div className="flex items-center gap-1 shrink-0">
                        <Badge variant="secondary" className="text-[0.45rem] h-3.5">F:{job.fitScore}</Badge>
                        <Badge variant="secondary" className="text-[0.45rem] h-3.5">S:{job.successScore}</Badge>
                      </div>
                    </div>
                  ))}
                  {data.jobs.length > 4 && <div className="text-[0.5rem] text-muted-foreground">+{data.jobs.length - 4} more</div>}
                </div>
              ) : (
                <div className="text-xs text-muted-foreground">No jobs in this category</div>
              )}
            </Card>
          )
        })}
      </div>

      <div className="grid grid-cols-[1fr_320px] gap-4">
        <div className="space-y-4">
          {/* Top Opportunities Table */}
          {topOpps.length > 0 && (
            <Card className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <Target className="w-5 h-5 text-green-500" />
                <h3 className="font-extrabold text-sm">Top Opportunities</h3>
                <Badge variant="secondary" className="text-[0.5rem]">{topOpps.length} ranked</Badge>
              </div>
              <div className="space-y-1.5">
                {topOpps.map((opp, i) => (
                  <div key={i} className="flex items-center gap-3 text-[0.6rem] p-2 rounded hover:bg-muted transition border-l-2 border-primary">
                    <div className="w-6 text-center font-bold text-primary">#{i + 1}</div>
                    <div className="flex-1 min-w-0">
                      <div className="font-bold">{opp.company}</div>
                      <div className="text-muted-foreground truncate">{opp.role} · {opp.location}</div>
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      <Badge variant="secondary" className="text-[0.45rem] h-3.5 bg-green-500/15 text-green-500">F:{opp.fitScore}</Badge>
                      <Badge variant="secondary" className="text-[0.45rem] h-3.5 bg-blue-500/15 text-blue-500">S:{opp.successScore}</Badge>
                      <Badge variant="secondary" className="text-[0.45rem] h-3.5 bg-purple-500/15 text-purple-500">O:{opp.overallScore}</Badge>
                    </div>
                    <Badge variant="secondary" className={cn("text-[0.45rem] h-3.5 shrink-0",
                      opp.action === 'Apply Now' ? "bg-green-500/15 text-green-500" :
                      opp.action === 'Customize' ? "bg-blue-500/15 text-blue-500" :
                      opp.action === 'Consider' ? "bg-yellow-500/15 text-yellow-500" :
                      "bg-gray-500/15 text-gray-500"
                    )}>{opp.action}</Badge>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>

        <div className="space-y-4">
          {/* Insights */}
          {insights.length > 0 && (
            <Card className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <Lightbulb className="w-5 h-5 text-yellow-500" />
                <h3 className="font-extrabold text-sm">Opportunity Insights</h3>
              </div>
              <div className="space-y-3">
                {insights.map((insight, i) => (
                  <div key={i} className="p-2 rounded-lg border border-yellow-500/20 bg-yellow-500/5 space-y-1">
                    <div className="text-[0.6rem] font-bold text-yellow-500">Observation</div>
                    <div className="text-[0.6rem] text-muted-foreground">{insight.observation}</div>
                    {insight.evidence && <div className="text-[0.55rem] text-muted-foreground/70"><strong>Evidence:</strong> {insight.evidence}</div>}
                    {insight.action && <div className="text-[0.55rem] text-primary"><strong>Action:</strong> {insight.action}</div>}
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
