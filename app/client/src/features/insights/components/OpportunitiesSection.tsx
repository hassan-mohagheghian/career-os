import {
  Rocket, Target, Eye, Warning, Lightning, ArrowsClockwise, Buildings, TrendUp, Clock
} from '@phosphor-icons/react'
import { cn } from '@/shared/lib/utils'
import { Button } from '@/shared/ui/button'
import { Badge } from '@/shared/ui/badge'
import { Card } from '@/shared/ui/card'

function formatTimeAgo(ts) {
  if (!ts) return ''
  const diffMs = Date.now() - new Date(ts).getTime()
  const mins = Math.floor(diffMs / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return days < 7 ? `${days}d ago` : new Date(ts).toLocaleDateString()
}

function JobCard({ job, onClick }) {
  const scoreColor = job.overallScore >= 80 ? 'text-green-500' :
                     job.overallScore >= 65 ? 'text-blue-500' :
                     job.overallScore >= 50 ? 'text-yellow-500' : 'text-red-500'
  return (
    <div onClick={onClick} className="flex items-center gap-2 p-2 rounded hover:bg-muted transition cursor-pointer text-xs">
      <span className={cn("font-bold w-8 text-right", scoreColor)}>{job.overallScore}</span>
      <div className="flex-1 min-w-0">
        <div className="font-semibold truncate">{job.company}</div>
        <div className="text-2xs text-muted-foreground truncate">{job.role} · {job.location}</div>
      </div>
      <Badge variant="secondary" className={cn("text-2xs h-3.5 shrink-0",
        job.visaProbability === 'BEST' ? 'bg-green-500/15 text-green-500' :
        job.visaProbability === 'Strong' ? 'bg-green-400/15 text-green-400' : 'bg-gray-500/15 text-gray-400'
      )}>{job.visaProbability}</Badge>
    </div>
  )
}

function FunnelColumn({ title, icon, jobs, color, onClickJob }) {
  return (
    <Card className="p-3">
      <div className="flex items-center gap-2 mb-2">
        <div className={cn("w-6 h-6 rounded flex items-center justify-center", color)}>{icon}</div>
        <h4 className="font-extrabold text-xs">{title}</h4>
        <Badge variant="secondary" className="text-2xs ml-auto">{jobs.length}</Badge>
      </div>
      <div className="space-y-1 max-h-[300px] overflow-y-auto">
        {jobs.length > 0 ? jobs.map((job, i) => (
          <JobCard key={i} job={job} onClick={() => onClickJob?.(job.num)} />
        )) : (
          <div className="text-2xs text-muted-foreground text-center py-2">No jobs</div>
        )}
      </div>
    </Card>
  )
}

export default function OpportunitiesSection({ data, refreshing, onRefresh, onOpenDrawer, status }) {
  const opp = data?.opportunities || {}
  const funnel = opp.funnel || {}
  const insights = opp.insights || []
  const bestJobs = opp.bestJobsThisWeek || []
  const multiRole = opp.multiRoleCompanies || []

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <h3 className="font-extrabold text-sm">Opportunities Intelligence</h3>
          {status?.opportunities?.lastRun && (
            <span className="text-2xs text-muted-foreground/60 flex items-center gap-0.5">
              <Clock className="w-2.5 h-2.5" />{formatTimeAgo(status.opportunities.lastRun)}
            </span>
          )}
        </div>
        <Button variant="ghost" size="sm" onClick={onRefresh} disabled={refreshing.opportunities} className="gap-1 h-6 text-2xs">
          <ArrowsClockwise className={cn("w-3 h-3", refreshing.opportunities && "animate-spin")} /> Refresh
        </Button>
      </div>

      {/* Opportunity Funnel */}
      <div className="grid grid-cols-4 gap-3">
        <FunnelColumn title="Apply Now" icon={<Rocket className="w-3.5 h-3.5" />} jobs={funnel.applyNow || []} color="bg-green-500/20 text-green-500" onClickJob={onOpenDrawer} />
        <FunnelColumn title="High Potential" icon={<Target className="w-3.5 h-3.5" />} jobs={funnel.highPotential || []} color="bg-blue-500/20 text-blue-500" onClickJob={onOpenDrawer} />
        <FunnelColumn title="Consider" icon={<Eye className="w-3.5 h-3.5" />} jobs={funnel.consider || []} color="bg-yellow-500/20 text-yellow-500" onClickJob={onOpenDrawer} />
        <FunnelColumn title="Low Priority" icon={<Warning className="w-3.5 h-3.5" />} jobs={funnel.lowPriority || []} color="bg-gray-500/20 text-gray-400" onClickJob={onOpenDrawer} />
      </div>

      <div className="grid grid-cols-[1fr_320px] gap-4">
        <div className="space-y-4">
          {/* Insights */}
          {insights.length > 0 && (
            <Card className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <Lightning className="w-5 h-5 text-yellow-500" />
                <h4 className="font-extrabold text-sm">Insights</h4>
              </div>
              <div className="space-y-2">
                {insights.map((insight, i) => (
                  <div key={i} className="p-2 rounded-lg border border-yellow-500/20 bg-yellow-500/5 space-y-1">
                    <div className="text-2xs font-bold text-yellow-500">Observation</div>
                    <div className="text-2xs text-muted-foreground">{insight.observation}</div>
                    {insight.evidence && <div className="text-2xs text-muted-foreground/70"><strong>Evidence:</strong> {insight.evidence}</div>}
                    {insight.action && <div className="text-2xs text-primary"><strong>Action:</strong> {insight.action}</div>}
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Best Jobs This Week */}
          {bestJobs.length > 0 && (
            <Card className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <TrendUp className="w-5 h-5 text-green-500" />
                <h4 className="font-extrabold text-sm">Best Jobs This Week</h4>
              </div>
              <div className="space-y-1">
                {bestJobs.map((job, i) => (
                  <JobCard key={i} job={job} onClick={() => onOpenDrawer?.(job.num)} />
                ))}
              </div>
            </Card>
          )}
        </div>

        <div className="space-y-4">
          {/* Multi-Role Companies */}
          {multiRole.length > 0 && (
            <Card className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <Buildings className="w-5 h-5 text-cyan-500" />
                <h4 className="font-extrabold text-sm">Multi-Role Companies</h4>
              </div>
              <div className="space-y-2">
                {multiRole.map((co, i) => (
                  <div key={i} className="p-2 rounded-lg border border-cyan-500/20 bg-cyan-500/5">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-xs">{co.company}</span>
                      <Badge variant="secondary" className="text-2xs h-3.5 bg-cyan-500/15 text-cyan-500">{co.count} roles</Badge>
                    </div>
                    <div className="text-2xs text-muted-foreground mt-1">
                      {co.roles?.join(', ')}
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Missed Opportunities */}
          {opp.missedOpportunities?.length > 0 && (
            <Card className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <Warning className="w-5 h-5 text-orange-500" />
                <h4 className="font-extrabold text-sm">Missed Opportunities</h4>
              </div>
              <div className="space-y-1">
                {opp.missedOpportunities.map((job, i) => (
                  <JobCard key={i} job={job} onClick={() => onOpenDrawer?.(job.num)} />
                ))}
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
