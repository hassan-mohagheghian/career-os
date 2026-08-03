'use client'

import { useQuery } from '@tanstack/react-query'
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/shared/ui/sheet'
import { ScrollArea } from '@/shared/ui/scroll-area'
import { CircleNotch, Clock, CheckCircle, XCircle, LinkSimple, MapPin, Briefcase, Clock as ClockIcon } from '@phosphor-icons/react'
import { jobApi } from '@/entities/job/api'
import type { JobDetail, JobDetailWorkflowStep } from '@/entities/job/types'

interface JobDetailDrawerProps {
  jobId: string | null
  onOpenChange: (jobId: string | null) => void
}

function stepIcon(status: JobDetailWorkflowStep['status']) {
  switch (status) {
    case 'processing': return <CircleNotch className="w-3.5 h-3.5 text-emerald-500 animate-spin shrink-0" />
    case 'completed': return <CheckCircle className="w-3.5 h-3.5 text-green-500 shrink-0" />
    case 'failed': return <XCircle className="w-3.5 h-3.5 text-red-500 shrink-0" />
    case 'skipped': return <Clock className="w-3.5 h-3.5 text-muted-foreground/50 shrink-0" />
    default: return <Clock className="w-3.5 h-3.5 text-blue-500 shrink-0" />
  }
}

function StepItem({ step, depth }: { step: JobDetailWorkflowStep; depth: number }) {
  return (
    <div>
      <div className="flex items-start gap-2 p-1" style={{ paddingLeft: `${depth * 16}px` }}>
        {stepIcon(step.status)}
        <div className="flex-1 min-w-0">
          <p className="text-2xs font-medium text-foreground truncate">{step.title}</p>
          {step.error && <p className="text-2xs text-red-500">{step.error.message}</p>}
        </div>
        {step.progress !== null && step.progress !== undefined && (
          <span className="text-2xs text-muted-foreground shrink-0">{Math.round(step.progress)}%</span>
        )}
      </div>
      {step.children.map(child => (
        <StepItem key={child.id} step={child} depth={depth + 1} />
      ))}
    </div>
  )
}

function DetailRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-4 py-1.5">
      <span className="text-2xs text-muted-foreground uppercase tracking-wide shrink-0">{label}</span>
      <span className="text-xs text-foreground text-right break-words">{value ?? '—'}</span>
    </div>
  )
}

function JobDetailContent({ detail }: { detail: JobDetail }) {
  const exec = detail.latest_processing_execution
  const steps = exec?.workflow?.steps ?? []

  return (
    <div className="space-y-4 px-4 py-4">
      <div>
        <h2 className="text-base font-semibold text-foreground">{detail.title || detail.role || 'Untitled'}</h2>
        <p className="text-sm text-muted-foreground">{detail.company_name || 'Unknown'}</p>
        <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
          {detail.location && <span className="flex items-center gap-1"><MapPin className="w-3.5 h-3.5" />{detail.location}</span>}
          {detail.work_type && <span className="flex items-center gap-1"><Briefcase className="w-3.5 h-3.5" />{detail.work_type}</span>}
          {detail.employment_type && <span className="flex items-center gap-1"><ClockIcon className="w-3.5 h-3.5" />{detail.employment_type}</span>}
        </div>
        {detail.url && (
          <a
            href={detail.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-xs text-blue-500 hover:underline mt-2"
          >
            <LinkSimple className="w-3.5 h-3.5" /> Open job posting
          </a>
        )}
      </div>

      <div className="grid grid-cols-3 gap-2">
        <div className="rounded-lg border border-border/40 bg-muted/10 p-3 text-center">
          <p className="text-lg font-semibold text-foreground">{detail.scores?.overall ?? '—'}</p>
          <p className="text-2xs text-muted-foreground">Overall</p>
        </div>
        <div className="rounded-lg border border-border/40 bg-muted/10 p-3 text-center">
          <p className="text-lg font-semibold text-foreground">{detail.scores?.fit ?? '—'}</p>
          <p className="text-2xs text-muted-foreground">Fit</p>
        </div>
        <div className="rounded-lg border border-border/40 bg-muted/10 p-3 text-center">
          <p className="text-lg font-semibold text-foreground">{detail.scores?.success ?? '—'}</p>
          <p className="text-2xs text-muted-foreground">Success</p>
        </div>
      </div>

      <div className="rounded-lg border border-border/40 bg-muted/10 p-3">
        <p className="text-2xs font-medium text-muted-foreground uppercase tracking-wide mb-1">Details</p>
        <DetailRow label="Role" value={detail.role} />
        <DetailRow label="Status" value={detail.status} />
        <DetailRow label="Salary" value={detail.salary} />
        <DetailRow label="Visa" value={detail.visa} />
        <DetailRow label="Created" value={detail.created_at ? new Date(detail.created_at).toLocaleString() : null} />
      </div>

      <div className="rounded-lg border border-border/40 bg-muted/10 p-3">
        <p className="text-2xs font-medium text-muted-foreground uppercase tracking-wide mb-1">Processing</p>
        <DetailRow label="Execution" value={exec?.execution_id} />
        <DetailRow label="Status" value={exec?.status} />
        <DetailRow label="Current Step" value={exec?.current_step} />
        {exec?.error && <p className="text-2xs text-red-500 pt-1">{exec.error.message}</p>}
        {steps.length > 0 && (
          <div className="mt-2">
            {steps.map(step => <StepItem key={step.id} step={step} depth={0} />)}
          </div>
        )}
      </div>

      {detail.description && (
        <div className="rounded-lg border border-border/40 bg-muted/10 p-3">
          <p className="text-2xs font-medium text-muted-foreground uppercase tracking-wide mb-1">Description</p>
          <p className="text-xs text-foreground whitespace-pre-wrap">{detail.description}</p>
        </div>
      )}
      {detail.notes && detail.notes.length > 0 && (
        <div className="rounded-lg border border-border/40 bg-muted/10 p-3">
          <p className="text-2xs font-medium text-muted-foreground uppercase tracking-wide mb-1">Notes</p>
          <div className="space-y-1.5">
            {detail.notes.map((n, i) => (
              <div key={i} className="text-xs text-foreground whitespace-pre-wrap">
                {n.title && <span className="font-medium">{n.title}: </span>}
                {n.content}
              </div>
            ))}
          </div>
        </div>
      )}
      {detail.links && detail.links.length > 0 && (
        <div className="rounded-lg border border-border/40 bg-muted/10 p-3">
          <p className="text-2xs font-medium text-muted-foreground uppercase tracking-wide mb-1">Links</p>
          <div className="space-y-1.5">
            {detail.links.map((l, i) => (
              <a key={i} href={l.url} target="_blank" rel="noreferrer" className="text-xs text-primary hover:underline break-all">
                {l.title || l.url}
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export function JobDetailDrawer({ jobId, onOpenChange }: JobDetailDrawerProps) {
  const { data: detail, isLoading, isError } = useQuery<JobDetail>({
    queryKey: ['job-detail', jobId],
    queryFn: () => jobApi.getDetail(jobId!),
    enabled: !!jobId,
  })

  return (
    <Sheet open={!!jobId} onOpenChange={(open) => { if (!open) onOpenChange(null) }}>
      <SheetContent side="right" className="w-[400px] sm:w-[480px] p-0">
        <SheetHeader className="flex flex-row items-center justify-between px-4 py-3 border-b border-border/40">
          <SheetTitle className="text-sm font-semibold">Job Details</SheetTitle>
        </SheetHeader>
        <ScrollArea className="flex-1 h-[calc(100vh-60px)]">
          {isLoading && (
            <div className="flex items-center justify-center h-40">
              <CircleNotch className="w-6 h-6 text-muted-foreground animate-spin" />
            </div>
          )}
          {isError && (
            <div className="flex items-center justify-center h-40">
              <p className="text-sm text-red-500">Unable to load job details.</p>
            </div>
          )}
          {detail && !isLoading && <JobDetailContent detail={detail} />}
        </ScrollArea>
      </SheetContent>
    </Sheet>
  )
}
