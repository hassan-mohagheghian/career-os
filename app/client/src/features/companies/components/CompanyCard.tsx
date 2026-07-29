import {
  Buildings, MapPin, Globe, Users, Briefcase
} from '@phosphor-icons/react'
import { cn } from '@/shared/lib/utils'
import { Card } from '@/shared/ui/card'
import { Button } from '@/shared/ui/button'
import CardActions from '@/shared/components/CardActions'

const PRIORITY_STYLES: Record<string, { bg: string; text: string; border: string }> = {
  'A++': { bg: 'rgba(16,185,129,0.2)', text: '#10b981', border: 'border-emerald-400/30' },
  'A+': { bg: 'rgba(16,185,129,0.15)', text: '#34d399', border: 'border-emerald-500/30' },
  'A': { bg: 'rgba(34,197,94,0.12)', text: '#22c55e', border: 'border-green-500/30' },
  'A-': { bg: 'rgba(34,197,94,0.1)', text: '#4ade80', border: 'border-green-400/30' },
  'B+': { bg: 'rgba(59,130,246,0.15)', text: '#60a5fa', border: 'border-blue-400/30' },
  'B': { bg: 'rgba(59,130,246,0.12)', text: '#3b82f6', border: 'border-blue-500/30' },
  'C': { bg: 'rgba(234,179,8,0.12)', text: '#eab308', border: 'border-yellow-500/30' },
  'D': { bg: 'rgba(239,68,68,0.12)', text: '#ef4444', border: 'border-red-500/30' },
}

export default function CompanyCard({ company, onClick, onDelete, onReprocess, onProcess }: {
  company: any
  onClick: () => void
  onDelete?: (id: number) => void
  onReprocess?: (id: number) => void
  onProcess?: (id: number) => void
}) {
  const scores = company.scores || {}
  const fitScore = scores.company_fit_score ?? null
  const successScore = scores.company_success_score ?? null
  const overallScore = scores.company_overall_score ?? null
  const overallGrade = scores.overall_grade || scores.fit_grade || '—'
  const ps = PRIORITY_STYLES[overallGrade] || PRIORITY_STYLES['B']

  const processHandler = (onProcess || onReprocess) ? () => (onProcess || onReprocess)?.(company.id) : undefined
  const deleteHandler = onDelete ? () => onDelete(company.id) : undefined

  return (
    <Card className={cn("group/card p-3 transition hover:shadow-lg hover:-translate-y-0.5 border-l-[3px] w-full min-w-0 overflow-hidden box-border")}
      style={{ borderLeftColor: ps.text }}>
      {/* Row 1: Grade + Scores */}
      <div className="flex items-center gap-2 mb-1.5">
        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-2xs font-black border"
          style={{ background: ps.bg, color: ps.text, borderColor: ps.border }}>
          {overallGrade}
        </span>
        {fitScore != null && <ScoreBadge label="Fit" value={fitScore} />}
        {successScore != null && <ScoreBadge label="Success" value={successScore} />}
        {overallScore != null && <ScoreBadge label="Overall" value={overallScore} />}
        <div className="flex items-center gap-0.5 shrink-0 ml-auto opacity-0 group-hover/card:opacity-100 transition-opacity">
          <CardActions
            status="processed"
            size="md"
            onProcess={processHandler}
            onDelete={deleteHandler}
          />
        </div>
      </div>

      {/* Row 2: Company name + Job count */}
      <div onClick={onClick} className="cursor-pointer text-sm font-bold truncate mb-0.5 flex items-center gap-1.5">
        {company.logo_url && <img src={company.logo_url} alt="" className="w-4 h-4 rounded inline-block align-middle" />}
        <span className="truncate">{company.name || 'Unknown Company'}</span>
        {company.job_count > 0 && (
          <span className="inline-flex items-center gap-0.5 px-1 py-0.5 rounded text-2xs font-bold bg-blue-500/15 text-blue-400 shrink-0">
            <Briefcase className="w-2 h-2" />{company.job_count}
          </span>
        )}
      </div>

      {/* Row 3: Industry + Location */}
      <div className="flex flex-wrap gap-1 mb-1.5">
        {company.industry && (
          <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-2xs font-semibold bg-primary/10 text-primary">
            <Buildings className="w-2.5 h-2.5" />{company.industry}
          </span>
        )}
        {(company.city || company.country) && (
          <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-2xs font-semibold bg-secondary text-secondary-foreground">
            <MapPin className="w-2.5 h-2.5" />{[company.city, company.country].filter(Boolean).join(', ')}
          </span>
        )}
        {company.company_size && (
          <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-2xs font-semibold bg-secondary text-secondary-foreground">
            <Users className="w-2.5 h-2.5" />{company.company_size}
          </span>
        )}
      </div>

      {/* Row 4: Description preview */}
      {company.description && (
        <div className="text-2xs text-muted-foreground truncate">{company.description}</div>
      )}

      {/* Row 5: Website */}
      {company.website && (
        <div className="flex items-center gap-1 mt-1 min-w-0">
          <Globe className="w-2.5 h-2.5 text-muted-foreground shrink-0" />
          <a href={company.website} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()}
            className="text-2xs text-primary hover:underline truncate">{company.website}</a>
        </div>
      )}
    </Card>
  )
}

function ScoreBadge({ label, value }: { label: string; value: number }) {
  if (value == null) return null
  const v = typeof value === 'number' ? value : parseInt(String(value))
  if (isNaN(v)) return null
  const bg = v >= 80 ? 'bg-emerald-500/15 text-emerald-400' :
    v >= 60 ? 'bg-blue-500/15 text-blue-400' :
    v >= 40 ? 'bg-yellow-500/15 text-yellow-400' :
    'bg-red-500/15 text-red-400'
  return (
    <span className={cn("inline-flex items-center px-1 py-0.5 rounded text-2xs font-bold", bg)} title={`${label}: ${v}`}>
      {label.slice(0, 3)}:{v}
    </span>
  )
}
