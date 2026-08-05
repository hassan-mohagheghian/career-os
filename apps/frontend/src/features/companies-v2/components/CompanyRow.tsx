import type { CompanyListItem } from '@/entities/company/types'
import { ScoreBadge } from '@/features/jobs-v2/components/ScoreBadge'
import DateTime from '@/shared/components/DateTime'
import { COMPANY_GRID_TEMPLATE } from './companiesColumns'
import { CompanyGradeBadge } from './CompanyGradeBadge'
import { CompanyProcessingBadge } from './CompanyProcessingBadge'
import { CompanyActions } from './CompanyActions'

interface CompanyRowProps {
  company: CompanyListItem
  onViewDetails: (id: string) => void
  onReprocess: (id: string) => void
  onEdit: (id: string) => void
  onDelete: (id: string) => void
}

export function CompanyRow({
  company, onViewDetails, onReprocess, onEdit, onDelete,
}: CompanyRowProps) {
  const grade = company.scores?.overall_grade ?? null
  const processingStatus = company.processing?.status ?? null

  return (
    <div
      className="grid border-b border-border/40 hover:bg-muted/30 cursor-pointer transition-colors items-center"
      style={{ gridTemplateColumns: COMPANY_GRID_TEMPLATE }}
      onClick={() => onViewDetails(company.id)}
    >
      <div className="py-2 px-2 flex items-center justify-center">
        <CompanyGradeBadge grade={grade} />
      </div>
      <div className="py-2 px-3 flex items-center">
        <div className="flex items-center gap-2 min-w-0">
          {company.logo_url && (
            <img src={company.logo_url} alt="" className="w-4 h-4 rounded shrink-0" />
          )}
          <span className="text-xs font-medium text-foreground truncate">{company.name}</span>
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
        <span className="text-xs text-muted-foreground">
          {company.job_count > 0 ? company.job_count : '—'}
        </span>
      </div>
      <div className="py-2 px-3 flex items-center">
        <div className="flex items-center gap-2 whitespace-nowrap">
          <ScoreBadge label="F" value={company.scores?.fit ?? null} />
          <ScoreBadge label="S" value={company.scores?.success ?? null} />
          <ScoreBadge label="O" value={company.scores?.overall ?? null} />
        </div>
      </div>
      <div className="py-2 px-3 flex items-center">
        <CompanyProcessingBadge status={processingStatus} />
      </div>
      <div className="py-2 px-3 flex items-center">
        <DateTime value={company.updated_at} format="relative" className="text-2xs text-muted-foreground" />
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
