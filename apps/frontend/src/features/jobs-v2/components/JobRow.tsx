import type { JobListItem } from '@/entities/job/types'
import type { ProcessingStatus as PStatus } from '@/entities/job/types'
import { ScoreBadge } from './ScoreBadge'
import { ProcessingStatus } from './ProcessingStatus'
import { JobActions } from './JobActions'
import DateTime from '@/shared/components/DateTime'
import { COLUMN_GRID_TEMPLATE } from './jobsColumns'

interface JobRowProps {
  job: JobListItem
  onProcessV2: (id: string) => void
  onViewDetails: (id: string) => void
  onEdit: (id: string) => void
  onDelete: (id: string) => void
  onRetry?: (id: string) => void
  onCancel?: (id: string) => void
  onOpenCompany?: (id: string) => void
}

export function JobRow({
  job, onProcessV2, onViewDetails, onEdit, onDelete, onRetry, onCancel,
}: JobRowProps) {
  const processingStatus: PStatus | null = job.latest_processing_execution?.status ?? null

  return (
    <div
      className="grid border-b border-border/40 hover:bg-muted/30 cursor-pointer transition-colors items-center"
      style={{ gridTemplateColumns: COLUMN_GRID_TEMPLATE }}
      onClick={() => onViewDetails(job.id)}
    >
      <div className="py-2 px-3 flex items-center">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-xs font-medium text-foreground truncate">
            {job.title || 'Untitled'}
          </span>
        </div>
      </div>
      <div className="py-2 px-3 flex items-center">
        <span className="text-xs text-muted-foreground truncate block">
          {job.company_name || 'Unknown'}
        </span>
      </div>
      <div className="py-2 px-3 flex items-center">
        <div className="flex items-center gap-1.5 min-w-0">
          <span className="text-xs text-muted-foreground truncate">
            {job.location || 'Unknown'}
          </span>
          {job.remote && (
            <span className="text-2xs px-1 py-0.5 rounded bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 whitespace-nowrap">
              Remote
            </span>
          )}
          {job.visa_sponsorship && (
            <span className="text-2xs px-1 py-0.5 rounded bg-blue-500/10 text-blue-500 border border-blue-500/20 whitespace-nowrap">
              Visa
            </span>
          )}
        </div>
      </div>
      <div className="py-2 px-3 flex items-center">
        <div className="flex items-center gap-2 whitespace-nowrap">
          <ScoreBadge label="O" value={job.scores?.overall ?? null} />
          <ScoreBadge label="F" value={job.scores?.fit ?? null} />
          <ScoreBadge label="S" value={job.scores?.success ?? null} />
        </div>
      </div>
      <div className="py-2 px-3 flex items-center">
        <ProcessingStatus status={processingStatus} />
      </div>
      <div className="py-2 px-3 flex items-center">
        <DateTime value={job.updated_at} format="relative" className="text-2xs text-muted-foreground" />
      </div>
      <div className="py-2 px-3 flex items-center">
        <DateTime value={job.created_at} format="relative" className="text-2xs text-muted-foreground" />
      </div>
      <div className="py-2 px-3 flex items-center justify-end" onClick={e => e.stopPropagation()}>
        <JobActions
          processingStatus={processingStatus}
          onProcessV2={() => onProcessV2(job.id)}
          onViewDetails={() => onViewDetails(job.id)}
          onEdit={() => onEdit(job.id)}
          onDelete={() => onDelete(job.id)}
          onRetry={() => onRetry?.(job.id)}
          onCancel={() => onCancel?.(job.id)}
        />
      </div>
    </div>
  )
}
