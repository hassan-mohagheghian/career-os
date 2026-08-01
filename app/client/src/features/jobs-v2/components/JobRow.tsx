import type { JobListItem } from '@/entities/job/types'
import type { ProcessingStatus as PStatus } from '@/entities/job/types'
import { ScoreBadge } from './ScoreBadge'
import { ProcessingStatus } from './ProcessingStatus'
import { JobActions } from './JobActions'
import { formatTimeAgo } from '@/shared/lib/formatTimeAgo'

interface JobRowProps {
  job: JobListItem
  onProcessV2: (id: string) => void
  onLegacyProcess: (id: string) => void
  onViewDetails: (id: string) => void
  onRetry?: (id: string) => void
  onCancel?: (id: string) => void
  onOpenCompany?: (id: string) => void
}

export function JobRow({
  job, onProcessV2, onLegacyProcess, onViewDetails, onRetry, onCancel,
}: JobRowProps) {
  const processingStatus: PStatus | null = job.latest_processing_execution?.status ?? null

  return (
    <div
      className="flex border-b border-border/40 hover:bg-muted/30 cursor-pointer transition-colors"
      onClick={() => onViewDetails(job.id)}
    >
      <div className="flex-1 py-2 px-3 flex items-center">
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-foreground truncate max-w-[240px]">
            {job.title || 'Untitled'}
          </span>
        </div>
      </div>
      <div className="flex-1 py-2 px-3 flex items-center">
        <span className="text-xs text-muted-foreground truncate max-w-[140px] block">
          {job.company_name || 'Unknown'}
        </span>
      </div>
      <div className="flex-1 py-2 px-3 flex items-center">
        <div className="flex items-center gap-1.5">
          <span className="text-xs text-muted-foreground truncate max-w-[100px]">
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
      <div className="flex-1 py-2 px-3 flex items-center">
        <div className="flex items-center gap-2 whitespace-nowrap">
          <ScoreBadge label="O" value={job.scores?.overall ?? null} />
          <ScoreBadge label="F" value={job.scores?.fit ?? null} />
          <ScoreBadge label="S" value={job.scores?.success ?? null} />
        </div>
      </div>
      <div className="flex-1 py-2 px-3 flex items-center">
        <ProcessingStatus status={processingStatus} />
      </div>
      <div className="flex-1 py-2 px-3 flex items-center">
        <span className="text-2xs text-muted-foreground whitespace-nowrap">
          {job.updated_at ? formatTimeAgo(job.updated_at) : '—'}
        </span>
      </div>
      <div className="flex-1 py-2 px-3 flex items-center justify-end" onClick={e => e.stopPropagation()}>
        <JobActions
          processingStatus={processingStatus}
          onProcessV2={() => onProcessV2(job.id)}
          onLegacyProcess={() => onLegacyProcess(job.id)}
          onViewDetails={() => onViewDetails(job.id)}
          onRetry={() => onRetry?.(job.id)}
          onCancel={() => onCancel?.(job.id)}
        />
      </div>
    </div>
  )
}
