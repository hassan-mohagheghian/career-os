import {
  TrendUp, IdentificationCard, Users, HouseSimple, ArrowsClockwise,
  Buildings, FileText, Repeat, Trash, MapPin, LinkSimple, Copy, Clock, Calendar
} from '@phosphor-icons/react'
import { cn } from '@/lib/utils'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

const CITY_COLORS = {
  'Berlin': { bg: 'rgba(239,68,68,0.15)', text: '#ef4444' },
  'Hamburg': { bg: 'rgba(249,115,22,0.15)', text: '#f97316' },
  'Munich': { bg: 'rgba(234,179,8,0.15)', text: '#eab308' },
  'Germany': { bg: 'rgba(34,197,94,0.15)', text: '#22c55e' },
  'Heidelberg': { bg: 'rgba(59,130,246,0.15)', text: '#3b82f6' },
}
const DEFAULT_CITY_COLOR = { bg: 'hsl(var(--secondary))', text: 'hsl(var(--muted-foreground))' }

const VISA_STYLES = {
  'BEST': { bg: 'rgba(34,197,94,0.2)', text: '#22c55e', label: 'BEST' },
  'Strong': { bg: 'rgba(34,197,94,0.12)', text: '#4ade80', label: 'Strong' },
  'Good': { bg: 'rgba(234,179,8,0.12)', text: '#facc15', label: 'Good' },
  'Moderate': { bg: 'rgba(249,115,22,0.12)', text: '#fb923c', label: 'Moderate' },
  'High': { bg: 'rgba(59,130,246,0.12)', text: '#60a5fa', label: 'High' },
  'Uncertain': { bg: 'hsl(var(--secondary))', text: 'hsl(var(--muted-foreground))', label: '?' },
  'N/A': { bg: 'hsl(var(--secondary))', text: 'hsl(var(--muted-foreground))', label: 'N/A' },
}

const SCORE_RANK = { 'P': 0, 'E': 1, 'D': 2, 'C': 3, 'B': 4, 'A': 5, 'A+': 6, 'A++': 7 }

function getScoreColor(s) {
  switch (s) {
    case 'A++': return 'text-emerald-400'
    case 'A+': return 'text-emerald-500'
    case 'A': return 'text-green-500'
    case 'B': return 'text-blue-500'
    case 'C': return 'text-yellow-500'
    case 'D': return 'text-orange-500'
    case 'E': return 'text-red-500'
    default: return 'text-muted-foreground'
  }
}

function getScoreBorder(s) {
  switch (s) {
    case 'A++': return 'border-l-emerald-400'
    case 'A+': return 'border-l-emerald-500'
    case 'A': return 'border-l-green-500'
    case 'B': return 'border-l-blue-500'
    case 'C': return 'border-l-yellow-500'
    case 'D': return 'border-l-orange-500'
    case 'E': return 'border-l-red-500'
    default: return 'border-l-muted'
  }
}

function getScoreBadge(s) {
  switch (s) {
    case 'A++': return 'bg-emerald-500/15 text-emerald-400 border border-emerald-400/30'
    case 'A+': return 'bg-emerald-500/15 text-emerald-500 border border-emerald-500/30'
    case 'A': return 'bg-green-500/15 text-green-500 border border-green-500/30'
    case 'B': return 'bg-blue-500/15 text-blue-500 border border-blue-500/30'
    case 'C': return 'bg-yellow-500/15 text-yellow-500 border border-yellow-500/30'
    case 'D': return 'bg-orange-500/15 text-orange-500 border border-orange-500/30'
    case 'E': return 'bg-red-500/15 text-red-500 border border-red-500/30'
    default: return 'bg-muted text-muted-foreground'
  }
}

function scoreRank(s) { return SCORE_RANK[s] ?? 0 }

function getMatchClass(m) {
  return m === 'High' ? 'bg-green-500/15 text-green-500 border-green-500/30' :
         m === 'Medium' ? 'bg-yellow-500/15 text-yellow-500 border-yellow-500/30' :
         'bg-red-500/15 text-red-500 border-red-500/30'
}

function LocationBadge({ loc }) {
  const lcc = CITY_COLORS[loc] || DEFAULT_CITY_COLOR
  return (
    <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[0.55rem] font-semibold"
      style={{ background: lcc.bg, color: lcc.text }}>
      <MapPin className="w-2.5 h-2.5" />{loc}
    </span>
  )
}

function VisaBadge({ visa }) {
  const vs = VISA_STYLES[visa] || VISA_STYLES['Uncertain']
  return (
    <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[0.55rem] font-semibold"
      style={{ background: vs.bg, color: vs.text }}>
      <IdentificationCard className="w-2.5 h-2.5" />{vs.label}
    </span>
  )
}

function WorkTypeTag({ type }) {
  const icon = type === 'Remote' ? <HouseSimple className="w-2.5 h-2.5" /> :
               type === 'Hybrid' ? <ArrowsClockwise className="w-2.5 h-2.5" /> :
               <Buildings className="w-2.5 h-2.5" />
  return (
    <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[0.55rem] font-semibold bg-secondary text-secondary-foreground">
      {icon}{type}
    </span>
  )
}

export function CompactJobCard({ job, onClick }) {
  const locations = job.parsedLocations || (job.location ? [job.location] : [])
  const borderColor = getScoreBorder(job.score)

  return (
    <Card onClick={onClick} className={cn("p-3 cursor-pointer transition hover:shadow-lg hover:-translate-y-0.5 border-l-[3px]", borderColor)}>
      <div className="flex items-center gap-1.5 mb-1">
        <span className={cn("text-[0.65rem] font-bold px-1.5 py-0.5 rounded shrink-0", getScoreBadge(job.score))} title="Fit score">{job.score}</span>
        {job.success && (
          <span className={cn("text-[0.55rem] font-bold px-1 py-0.5 rounded shrink-0 opacity-80", getScoreBadge(job.success))} title="Success probability">{job.success}</span>
        )}
        <span className="text-sm font-bold truncate">{job.company}</span>
      </div>
      <div className="text-xs text-muted-foreground truncate mb-1.5">{job.role}</div>
      <div className="flex flex-wrap gap-1">
        {locations.slice(0, 2).map((loc, i) => <LocationBadge key={i} loc={loc} />)}
        {locations.length > 2 && <span className="text-[0.5rem] text-muted-foreground">+{locations.length - 2}</span>}
        <WorkTypeTag type={job.work_type} />
        <span className={cn("inline-flex items-center px-1.5 py-0.5 rounded text-[0.55rem] font-semibold border", getMatchClass(job.match))}>{job.match}</span>
        <VisaBadge visa={job.visa} />
      </div>
    </Card>
  )
}

export function JobCard({ job, rank, onClick, onRescore, onDelete, onRequeue, onViewWorkflow }) {
  const locations = job.parsedLocations || (job.location ? [job.location] : [])
  const hasLogs = job.workflow_log && JSON.parse(job.workflow_log).length > 0
  const isRescoring = job.rescoring === 1
  const borderColor = getScoreBorder(job.score)

  return (
    <Card className={cn("group/card p-3 transition hover:shadow-lg hover:-translate-y-0.5 border-l-[3px]", borderColor)}>
      {/* Row 1: Scores + Actions */}
      <div className="flex items-center gap-2 mb-1.5">
        <div className="flex items-baseline gap-1.5 shrink-0">
          <span onClick={onClick} className={cn("cursor-pointer text-xl font-black leading-none", getScoreColor(job.score))} title="Fit score">{job.score}</span>
          {job.success && (
            <span onClick={onClick} className={cn("cursor-pointer text-sm font-bold opacity-80 leading-none", getScoreColor(job.success))} title="Success probability">{job.success}</span>
          )}
        </div>
        <span onClick={onClick} className="cursor-pointer text-xs font-semibold text-muted-foreground shrink-0">#{rank}</span>
        <div className="flex items-center gap-0.5 shrink-0 ml-auto opacity-0 group-hover/card:opacity-100 transition-opacity">
          {isRescoring && <span className="text-[0.5rem] px-1.5 py-0.5 rounded bg-primary text-primary-foreground animate-pulse">Rescore</span>}
          {onRescore && (
            <Button variant="ghost" size="icon" className="h-3.5 w-3.5" onClick={(e) => { e.stopPropagation(); onRescore(job.num) }} title="Rescore">
              <TrendUp className="w-2 h-2" />
            </Button>
          )}
          {onRequeue && (
            <Button variant="ghost" size="icon" className="h-3.5 w-3.5 text-blue-500 hover:text-blue-500" onClick={(e) => { e.stopPropagation(); onRequeue(job.num) }} title="Reprocess">
              <Repeat className="w-2 h-2" />
            </Button>
          )}
          {onViewWorkflow && hasLogs && (
            <Button variant="ghost" size="icon" className="h-3.5 w-3.5" onClick={(e) => { e.stopPropagation(); onViewWorkflow({ id: job.num, workflow_log: job.workflow_log, company: job.company, job_num: job.num }) }}>
              <FileText className="w-2 h-2" />
            </Button>
          )}
          {onDelete && (
            <Button variant="ghost" size="icon" className="h-3.5 w-3.5 text-destructive hover:bg-destructive/10 hover:text-destructive" onClick={(e) => { e.stopPropagation(); onDelete(job.num) }} title="Delete">
              <Trash className="w-2 h-2" />
            </Button>
          )}
        </div>
      </div>

      {/* Row 2: Company */}
      <div onClick={onClick} className="cursor-pointer text-sm font-bold truncate mb-0.5">{job.company}</div>

      {/* Row 3: Role */}
      <div onClick={onClick} className="cursor-pointer text-xs text-muted-foreground truncate mb-1.5">{job.role}</div>
      <div className="flex gap-1 flex-wrap">
        {locations.slice(0, 2).map((loc, i) => <LocationBadge key={i} loc={loc} />)}
        {locations.length > 2 && <span className="text-[0.5rem] text-muted-foreground">+{locations.length - 2}</span>}
        <WorkTypeTag type={job.work_type} />
        <span className={cn("inline-flex items-center px-1.5 py-0.5 rounded text-[0.55rem] font-semibold border", getMatchClass(job.match))}>{job.match}</span>
        <VisaBadge visa={job.visa} />
        {job.applicants && job.applicants !== 'Not specified' && (
          <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[0.55rem] font-semibold bg-secondary text-secondary-foreground">
            <Users className="w-2.5 h-2.5" />{job.applicants}
          </span>
        )}
      </div>

      {/* Row 3: Stack */}
      {job.stack && (
        <div className="mt-1.5 text-[0.6rem] text-muted-foreground truncate" title={job.stack}>
          <b className="text-foreground/70">Stack:</b> {job.stack}
        </div>
      )}

      {/* Row 4: Timestamps */}
      {(job.adv_at || job.see_at) && (
        <div className="mt-1 flex gap-2 text-[0.5rem] text-muted-foreground">
          {job.adv_at && (
            <span className="inline-flex items-center gap-0.5" title={`Listed: ${job.adv_at}`}>
              <Calendar className="w-2 h-2" />{new Date(job.adv_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: '2-digit' })}
            </span>
          )}
          {job.see_at && (
            <span className="inline-flex items-center gap-0.5" title={`Seen: ${job.see_at}`}>
              <Clock className="w-2 h-2" />{new Date(job.see_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: '2-digit' })}
            </span>
          )}
        </div>
      )}
      {/* Row 4: URL */}
      {job.url && (
        <div className="flex items-center gap-1 mt-1.5 min-w-0 overflow-hidden">
          <LinkSimple className="w-2.5 h-2.5 text-muted-foreground shrink-0" />
          <span className="text-[0.55rem] truncate min-w-0 flex-1 text-primary" title={job.url}>
            <a href={job.url} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()}
              className="hover:underline">
              {job.url}
            </a>
          </span>
          <Button variant="ghost" size="icon" className="h-4 w-4 shrink-0" onClick={(e) => { e.stopPropagation(); navigator.clipboard.writeText(job.url) }} title="Copy URL">
            <Copy className="w-2.5 h-2.5" />
          </Button>
        </div>
      )}
    </Card>
  )
}

export { CITY_COLORS, DEFAULT_CITY_COLOR, VISA_STYLES, getScoreColor, getScoreBadge, getMatchClass, LocationBadge, VisaBadge, WorkTypeTag, scoreRank }
