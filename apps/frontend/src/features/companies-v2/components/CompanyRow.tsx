import type { CompanyListItem } from '@/entities/company/types'
import { ScoreBadge } from '@/features/jobs-v2/components/ScoreBadge'
import { StatusBadge } from '@/features/jobs-v2/components/StatusBadge'
import type { ProcessingStatus } from '@/entities/job/types'
import { Badge } from '@/shared/ui/badge'
import DateTime from '@/shared/components/DateTime'
import { GradeBadge } from '@/shared/components/GradeBadge'
import { gradeForScore } from '@/shared/lib/grade'
import { PinButton } from '@/shared/components/PinButton'
import { buildCompanyGridTemplate } from './companiesColumns'
import { CompanyActions } from './CompanyActions'

interface CompanyRowProps {
  company: CompanyListItem
  onViewDetails: (id: string) => void
  onReprocess: (id: string) => void
  onEdit: (id: string) => void
  onDelete: (id: string) => void
  onTogglePinned: (id: string, pinned: boolean) => void
  showPinnedColumn?: boolean
  showRowNumberColumn?: boolean
  rowNumber?: number
}

const RECRUITER_TYPES = ['RECRUITING_AGENCY', 'STAFFING_COMPANY']

function isRecruiterType(type: string | null | undefined) {
  return RECRUITER_TYPES.includes(type ?? '')
}

export function CompanyRow({
  company, onViewDetails, onReprocess, onEdit, onDelete, onTogglePinned,
  showPinnedColumn = true, showRowNumberColumn = false, rowNumber,
}: CompanyRowProps) {
  const grade = company.scores?.overall_grade ?? (company.scores?.overall != null ? gradeForScore(company.scores.overall) : null)
  const processingStatus = (company.processing?.status ?? null) as ProcessingStatus | null
  const recruiter = isRecruiterType(company.company_type)
  const listedJobs = recruiter ? company.recruiter_job_count : company.job_count
  const listedLabel = recruiter
    ? `${listedJobs} ${listedJobs === 1 ? 'job' : 'jobs'} listed for clients`
    : `${listedJobs} ${listedJobs === 1 ? 'job' : 'jobs'}`

  return (
    <div
      className="grid border-b border-border/40 hover:bg-muted/50 hover:ring-1 hover:ring-inset hover:ring-border/60 focus-within:bg-muted/50 cursor-pointer transition-colors items-center"
      style={{ gridTemplateColumns: buildCompanyGridTemplate(showRowNumberColumn, showPinnedColumn) }}
      onClick={() => onViewDetails(company.id)}
    >
      {showRowNumberColumn && (
        <div className="py-2 px-3 flex items-center justify-center">
          <span className="text-2xs text-muted-foreground tabular-nums">{rowNumber ?? ''}</span>
        </div>
      )}
      {showPinnedColumn && (
        <div className="py-2 px-2 flex items-center justify-center" onClick={e => e.stopPropagation()}>
          <PinButton pinned={company.pinned} onToggle={() => onTogglePinned(company.id, !company.pinned)} entityLabel="company" />
        </div>
      )}
      <div className="py-2 px-3 flex items-center">
        <div className="flex items-center gap-2 min-w-0">
          {company.logo_url && (
            <img src={company.logo_url} alt="" className="w-4 h-4 rounded shrink-0" />
          )}
          <span className="text-xs font-medium text-foreground truncate">{company.name}</span>
          {company.is_alias && (
            <Badge variant="secondary" className="shrink-0 h-4 px-1.5 text-2xs text-muted-foreground">
              alias
            </Badge>
          )}
        </div>
      </div>
      <div className="py-2 px-3 flex items-center">
        <span className="text-xs text-muted-foreground truncate block">{company.industry || 'Unknown'}</span>
      </div>
      <div className="py-2 px-3 flex items-center">
        <span className="text-xs text-muted-foreground truncate block">
          {[company.city, company.country].filter(Boolean).join(', ') || 'Unknown'}
        </span>
      </div>
      <div className="py-2 px-3 flex items-center">
        <span className="text-xs text-muted-foreground truncate block">{company.company_size || '—'}</span>
      </div>
      <div className="py-2 px-3 flex items-center">
        <span className="text-xs text-muted-foreground" title={listedJobs > 0 ? listedLabel : undefined}>
          {listedJobs > 0 ? listedJobs : '—'}
        </span>
      </div>
      <div className="py-2 px-3 flex items-center">
        <div className="flex items-center gap-2 whitespace-nowrap">
          <GradeBadge grade={grade} className="w-7 h-5 text-2xs" />
          <ScoreBadge label="F" value={company.scores?.fit ?? null} />
          <ScoreBadge label="S" value={company.scores?.success ?? null} />
          <ScoreBadge label="O" value={company.scores?.overall ?? null} />
        </div>
      </div>
      <div className="py-2 px-3 flex items-center">
        <StatusBadge status={processingStatus} />
      </div>
      <div className="py-2 px-3 flex items-center">
        <DateTime value={company.updated_at} format="relative" className="text-2xs text-muted-foreground" />
      </div>
      <div className="py-2 px-3 flex items-center">
        <DateTime value={company.created_at} format="relative" className="text-2xs text-muted-foreground" />
      </div>
      <div className="py-2 px-3 flex items-center justify-end" onClick={e => e.stopPropagation()}>
        <CompanyActions
          onViewDetails={() => onViewDetails(company.id)}
          onReprocess={() => onReprocess(company.id)}
          onEdit={() => onEdit(company.id)}
          onDelete={() => onDelete(company.id)}
        />
      </div>
    </div>
  )
}
