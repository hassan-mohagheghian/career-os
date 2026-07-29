import { Target, ChartBar, TrendUp, Scales, Stack } from '@phosphor-icons/react'
import { cn } from '@/shared/lib/utils'
import { TabHeader } from '@/shared/components/DrawerComponents'
import { getScoreColor, getMatchClass, numericToGrade } from '@/shared/components/ProcessedCards'

export default function ScoresTab({ job }) {
  const overall = job.overall_score != null ? Math.round(job.overall_score) : null
  const fit = job.fit_score != null ? Math.round(job.fit_score) : null
  const success = job.success_score != null ? Math.round(job.success_score) : null
  const grade = job.score || (overall != null ? numericToGrade(overall) : null)
  const match = job.match

  return (
    <div>
      <div className="grid grid-cols-3 gap-3 mb-4">
        <div className={cn("flex flex-col items-center justify-center p-4 rounded-lg border-2", getScoreColor(overall ?? grade))}>
          <span className={cn("text-5xl font-black", getScoreColor(overall ?? grade))}>
            {overall ?? grade ?? '?'}
          </span>
          <span className="text-2xs uppercase tracking-wider text-muted-foreground font-semibold mt-1">Overall</span>
        </div>
        <div className="flex flex-col items-center justify-center p-4 rounded-lg border bg-muted/30">
          <span className={cn("text-3xl font-bold", getScoreColor(fit != null ? fit : grade))}>
            {fit ?? grade ?? '?'}
          </span>
          <span className="text-2xs uppercase tracking-wider text-muted-foreground font-semibold mt-1">Fit</span>
        </div>
        <div className="flex flex-col items-center justify-center p-4 rounded-lg border bg-muted/30">
          <span className={cn("text-3xl font-bold", getScoreColor(success != null ? success : grade))}>
            {success ?? grade ?? '?'}
          </span>
          <span className="text-2xs uppercase tracking-wider text-muted-foreground font-semibold mt-1">Success</span>
        </div>
      </div>

      {grade && (
        <div className="mb-3 p-3 rounded-lg border bg-muted/30">
          <div className="flex items-center gap-2 mb-2">
            <Target className="w-4 h-4 text-primary" />
            <span className="text-xs font-semibold">Letter Grade</span>
          </div>
          <span className={cn("text-2xl font-black", getScoreColor(grade))}>{grade}</span>
        </div>
      )}

      {match && (
        <div className="mb-3 p-3 rounded-lg border bg-muted/30">
          <div className="flex items-center gap-2 mb-2">
            <ChartBar className="w-4 h-4 text-primary" />
            <span className="text-xs font-semibold">Match</span>
          </div>
          <span className={cn("inline-flex items-center px-2 py-0.5 rounded text-sm font-bold border", getMatchClass(match))}>{match}</span>
        </div>
      )}

      {fit != null && success != null && (
        <div className="mb-3 p-3 rounded-lg border bg-muted/30">
          <div className="flex items-center gap-2 mb-2">
            <Scales className="w-4 h-4 text-primary" />
            <span className="text-xs font-semibold">Score Breakdown</span>
          </div>
          <div className="space-y-2">
            <div>
              <div className="flex justify-between text-2xs text-muted-foreground mb-0.5">
                <span>Technical Fit</span>
                <span>{fit}/100</span>
              </div>
              <div className="h-2 rounded-full bg-muted overflow-hidden">
                <div className={cn("h-full rounded-full transition-all", getScoreColor(fit))} style={{ width: `${fit}%` }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-2xs text-muted-foreground mb-0.5">
                <span>Success Probability</span>
                <span>{success}/100</span>
              </div>
              <div className="h-2 rounded-full bg-muted overflow-hidden">
                <div className={cn("h-full rounded-full transition-all", getScoreColor(success))} style={{ width: `${success}%` }} />
              </div>
            </div>
          </div>
        </div>
      )}

      {job.stack && (
        <div className="mb-3">
          <TabHeader title="Stack" icon={<Stack className="w-4 h-4" />} className="mb-2" />
          <p className="text-sm text-muted-foreground">{job.stack}</p>
        </div>
      )}
    </div>
  )
}
