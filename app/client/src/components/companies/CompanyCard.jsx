import {
  Buildings, MapPin, Trash, Repeat, Globe, Users
} from '@phosphor-icons/react'
import { cn } from '@/lib/utils'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

const PRIORITY_STYLES = {
  'A++': { bg: 'rgba(16,185,129,0.2)', text: '#10b981', border: 'border-emerald-400/30' },
  'A+': { bg: 'rgba(16,185,129,0.15)', text: '#34d399', border: 'border-emerald-500/30' },
  'A': { bg: 'rgba(34,197,94,0.12)', text: '#22c55e', border: 'border-green-500/30' },
  'B': { bg: 'rgba(59,130,246,0.12)', text: '#3b82f6', border: 'border-blue-500/30' },
  'C': { bg: 'rgba(234,179,8,0.12)', text: '#eab308', border: 'border-yellow-500/30' },
}

export default function CompanyCard({ company, onClick, onDelete, onReprocess }) {
  const scores = company.scores || {}
  const priority = scores.priority || 'B'
  const ps = PRIORITY_STYLES[priority] || PRIORITY_STYLES['B']

  return (
    <Card className={cn("group/card p-3 transition hover:shadow-lg hover:-translate-y-0.5 border-l-[3px]", `border-l-[${ps.text}]`)}
      style={{ borderLeftColor: ps.text }}>
      {/* Row 1: Priority + Scores */}
      <div className="flex items-center gap-2 mb-1.5">
        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[0.6rem] font-black border"
          style={{ background: ps.bg, color: ps.text, borderColor: ps.border }}>
          {priority}
        </span>
        {scores.visa_score != null && <ScoreBadge label="Visa" value={scores.visa_score} />}
        {scores.tech_match != null && <ScoreBadge label="Tech" value={scores.tech_match} />}
        {scores.career_score != null && <ScoreBadge label="Career" value={scores.career_score} />}
        <div className="flex items-center gap-0.5 shrink-0 ml-auto opacity-0 group-hover/card:opacity-100 transition-opacity">
          {onReprocess && (
            <Button variant="ghost" size="icon" className="h-3.5 w-3.5 text-blue-500" onClick={(e) => { e.stopPropagation(); onReprocess(company.id) }} title="Reprocess">
              <Repeat className="w-2 h-2" />
            </Button>
          )}
          {onDelete && (
            <Button variant="ghost" size="icon" className="h-3.5 w-3.5 text-destructive hover:bg-destructive/10" onClick={(e) => { e.stopPropagation(); onDelete(company.id) }} title="Delete">
              <Trash className="w-2 h-2" />
            </Button>
          )}
        </div>
      </div>

      {/* Row 2: Company name */}
      <div onClick={onClick} className="cursor-pointer text-sm font-bold truncate mb-0.5">
        {company.logo_url && <img src={company.logo_url} alt="" className="w-4 h-4 rounded inline-block mr-1.5 align-middle" />}
        {company.name || 'Unknown Company'}
      </div>

      {/* Row 3: Industry + Location */}
      <div className="flex flex-wrap gap-1 mb-1.5">
        {company.industry && (
          <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[0.55rem] font-semibold bg-primary/10 text-primary">
            <Buildings className="w-2.5 h-2.5" />{company.industry}
          </span>
        )}
        {(company.city || company.country) && (
          <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[0.55rem] font-semibold bg-secondary text-secondary-foreground">
            <MapPin className="w-2.5 h-2.5" />{[company.city, company.country].filter(Boolean).join(', ')}
          </span>
        )}
        {company.company_size && (
          <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[0.55rem] font-semibold bg-secondary text-secondary-foreground">
            <Users className="w-2.5 h-2.5" />{company.company_size}
          </span>
        )}
      </div>

      {/* Row 4: Description preview */}
      {company.description && (
        <div className="text-[0.6rem] text-muted-foreground truncate">{company.description}</div>
      )}

      {/* Row 5: Website */}
      {company.website && (
        <div className="flex items-center gap-1 mt-1 min-w-0">
          <Globe className="w-2.5 h-2.5 text-muted-foreground shrink-0" />
          <a href={company.website} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()}
            className="text-[0.55rem] text-primary hover:underline truncate">{company.website}</a>
        </div>
      )}
    </Card>
  )
}

function ScoreBadge({ label, value }) {
  if (value == null) return null
  const v = typeof value === 'number' ? value : parseInt(value)
  if (isNaN(v)) return null
  const bg = v >= 80 ? 'bg-emerald-500/15 text-emerald-400' :
             v >= 60 ? 'bg-blue-500/15 text-blue-400' :
             v >= 40 ? 'bg-yellow-500/15 text-yellow-400' :
             'bg-red-500/15 text-red-400'
  return (
    <span className={cn("inline-flex items-center px-1 py-0.5 rounded text-[0.55rem] font-bold", bg)} title={`${label}: ${v}`}>
      {label.slice(0, 1)}:{v}
    </span>
  )
}
