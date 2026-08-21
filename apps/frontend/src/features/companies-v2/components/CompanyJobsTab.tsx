import { useState } from 'react'
import { MapPin, ArrowSquareOut, ArrowRight } from '@phosphor-icons/react'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { GradeBadge } from '@/shared/components/GradeBadge'
import { RankBadge } from '@/shared/components/RankBadge'
import { gradeForScore } from '@/shared/lib/grade'

export default function CompanyJobsTab({ companyId, companyName, jobs = [], onOpenJob, onNavigateToJob }: {
  companyId?: string
  companyName?: string
  jobs?: any[]
  onOpenJob?: (id: string) => void
  onNavigateToJob?: (id: string) => void
}) {
  const [expanded, setExpanded] = useState(false)
  const shownJobs = expanded ? jobs : jobs.slice(0, 5)

  if (jobs.length === 0) {
    return (
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-muted-foreground">0 linked jobs</span>
        </div>
        <div className="text-center py-6 text-xs text-muted-foreground">No jobs linked to this company yet.</div>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-muted-foreground">{jobs.length} linked job{jobs.length !== 1 ? 's' : ''}</span>
      </div>
      {shownJobs.map(j => {
        const overall = j.overall_score ?? j.score ?? null
        const overallNum = overall != null ? Number(overall) : null
        const validOverall = overallNum != null && !Number.isNaN(overallNum) ? overallNum : null
        return (
          <div key={j.id} className="flex items-center gap-1 p-2 rounded border border-border/50 hover:bg-muted/50 transition group">
            <div className="flex-1 min-w-0 cursor-pointer" onClick={() => onOpenJob?.(j.id)}>
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold truncate flex-1">{j.role || 'Untitled Job'}</span>
                {validOverall != null && <GradeBadge grade={gradeForScore(validOverall)} className="shrink-0" />}
                {j.rank != null && <RankBadge rank={j.rank} variant="inline" className="shrink-0" />}
              </div>
              {j.location && <div className="text-2xs text-muted-foreground mt-0.5"><MapPin className="w-2 h-2 inline mr-0.5" />{j.location}</div>}
              {(j.fit_score != null || j.success_score != null) && (
                <div className="flex items-center gap-2 mt-0.5">
                  {overall != null && <Badge variant="secondary" className="text-2xs">Overall {overall}</Badge>}
                  {j.success_score != null && <Badge variant="secondary" className="text-2xs">Success {j.success_score}</Badge>}
                  {j.fit_score != null && <Badge variant="secondary" className="text-2xs">Fit {j.fit_score}</Badge>}
                </div>
              )}
            </div>
            <div className="flex items-center gap-0.5 shrink-0 opacity-0 group-hover:opacity-100 transition">
              <Button variant="ghost" size="icon" className="h-5 w-5" onClick={() => onOpenJob?.(j.id)} title="Open job drawer">
                <ArrowSquareOut className="w-3 h-3" />
              </Button>
              <Button variant="ghost" size="icon" className="h-5 w-5" onClick={() => onNavigateToJob?.(j.id)} title="Go to Jobs page">
                <ArrowRight className="w-3 h-3" />
              </Button>
            </div>
          </div>
        )
      })}
      {jobs.length > 5 && (
        <Button variant="ghost" size="sm" className="w-full h-6 text-2xs" onClick={() => setExpanded(e => !e)}>
          {expanded ? 'Show fewer' : `Show all ${jobs.length} jobs`}
        </Button>
      )}
    </div>
  )
}
