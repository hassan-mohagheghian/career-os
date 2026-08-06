'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/shared/ui/sheet'
import { ScrollArea } from '@/shared/ui/scroll-area'
import { CircleNotch, Clock, CheckCircle, XCircle, LinkSimple, MapPin, Briefcase, Clock as ClockIcon, PencilSimple } from '@phosphor-icons/react'
import { jobApi } from '@/entities/job/api'
import type { JobDetail, JobDetailWorkflowStep } from '@/entities/job/types'
import DateTime from '@/shared/components/DateTime'
import NotesLinksReadOnly from '@/shared/components/NotesLinksReadOnly'
import { GradeBadge } from '@/shared/components/GradeBadge'
import { gradeForScore } from '@/shared/lib/grade'
import { RecommendationBadge } from './RecommendationBadge'
import { CompanyPicker } from './CompanyPicker'
import { Button } from '@/shared/ui/button'

interface JobDetailDrawerProps {
  jobId: string | null
  onOpenChange: (jobId: string | null) => void
  onEdit?: (id: string) => void
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
    <div className="min-w-0">
      <div className="flex items-start gap-2 p-1 min-w-0" style={{ paddingLeft: `${depth * 16}px` }}>
        {stepIcon(step.status)}
        <div className="flex-1 min-w-0 overflow-hidden">
          <p className="text-2xs font-medium text-foreground min-w-0 break-words">{step.title}</p>
          {step.error && <p className="text-2xs text-red-500 break-words">{step.error.message}</p>}
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

function Badge({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center rounded-md border border-border/60 px-2 py-0.5 text-2xs font-medium text-foreground">
      {children}
    </span>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-border/40 bg-muted/10 p-3">
      <p className="text-2xs font-medium text-muted-foreground uppercase tracking-wide mb-2">{title}</p>
      {children}
    </div>
  )
}

function AnalysisSection({ analysis }: { analysis: NonNullable<JobDetail['analysis']> }) {
  return (
    <div className="space-y-4">
      <Section title="AI Analysis">
        {analysis.generated_at && (
          <span className="text-2xs text-muted-foreground">
            Generated <DateTime value={analysis.generated_at} />
          </span>
        )}
        {analysis.insights && analysis.insights.length > 0 && (
          <ul className="mt-2 space-y-1">
            {analysis.insights.map((insight, i) => (
              <li key={i} className="text-xs text-muted-foreground flex gap-1.5">
                <span className="shrink-0">•</span>
                <span className="break-words">{insight}</span>
              </li>
            ))}
          </ul>
        )}
      </Section>

      {analysis.scores_explanation && (
        <Section title="Scores Explanation">
          {analysis.scores_explanation.fit_factors.length > 0 && (
            <p className="text-2xs font-medium text-muted-foreground uppercase mb-1">Why it fits</p>
          )}
          <ul className="mb-2 space-y-1">
            {analysis.scores_explanation.fit_factors.map((f, i) => (
              <li key={i} className="text-xs text-foreground flex gap-1.5">
                <span className="shrink-0">•</span>
                <span className="break-words">{f}</span>
              </li>
            ))}
          </ul>
          {analysis.scores_explanation.success_factors.length > 0 && (
            <p className="text-2xs font-medium text-muted-foreground uppercase mb-1">Chance of success</p>
          )}
          <ul className="mb-2 space-y-1">
            {analysis.scores_explanation.success_factors.map((f, i) => (
              <li key={i} className="text-xs text-foreground flex gap-1.5">
                <span className="shrink-0">•</span>
                <span className="break-words">{f}</span>
              </li>
            ))}
          </ul>
          {analysis.scores_explanation.concerns.length > 0 && (
            <p className="text-2xs font-medium text-muted-foreground uppercase mb-1">Concerns</p>
          )}
          <ul className="space-y-1">
            {analysis.scores_explanation.concerns.map((c, i) => (
              <li key={i} className="text-xs text-red-500/90 flex gap-1.5">
                <span className="shrink-0">•</span>
                <span className="break-words">{c}</span>
              </li>
            ))}
          </ul>
        </Section>
      )}

      {analysis.summary && (analysis.summary.summary || analysis.summary.resume_fit || analysis.summary.note) && (
        <Section title="Summary">
          {analysis.summary.summary && (
            <p className="text-xs text-foreground whitespace-pre-wrap mb-2">{analysis.summary.summary}</p>
          )}
          {analysis.summary.resume_fit && (
            <p className="text-xs text-muted-foreground whitespace-pre-wrap mb-2">
              <span className="font-medium text-foreground">Resume fit: </span>{analysis.summary.resume_fit}
            </p>
          )}
          {analysis.summary.note && (
            <p className="text-xs text-muted-foreground whitespace-pre-wrap">{analysis.summary.note}</p>
          )}
        </Section>
      )}

      {analysis.skills && analysis.skills.length > 0 && (
        <Section title="Tagged Skills">
          <div className="flex flex-wrap gap-1.5">
            {analysis.skills.map((skill, i) => (
              <Badge key={i}>
                {skill.name}
                {skill.level != null && <span className="text-muted-foreground"> · L{skill.level}</span>}
                {skill.category && <span className="text-muted-foreground"> · {skill.category}</span>}
              </Badge>
            ))}
          </div>
        </Section>
      )}
    </div>
  )
}

function JobDetailContent({ detail }: { detail: JobDetail }) {
  const exec = detail.latest_processing_execution
  const steps = exec?.workflow?.steps ?? []
  const queryClient = useQueryClient()
  const setCompany = useMutation({
    mutationFn: (companyId: string | null) => jobApi.setCompany(detail.id, companyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['job-detail', detail.id] })
      queryClient.invalidateQueries({ queryKey: ['jobs'] })
    },
  })

  return (
    <div className="space-y-4 px-4 py-4 min-w-0">
      <div>
        <h2 className="text-base font-semibold text-foreground">{detail.title || detail.role || 'Untitled'}</h2>
        {detail.company_id ? (
          <a
            href={`/companies?company=${detail.company_id}`}
            className="text-sm text-primary hover:underline"
          >
            {detail.company_name || 'Linked Company'}
          </a>
        ) : (
          <p className="text-sm text-muted-foreground">{detail.company_name || 'Unknown'}</p>
        )}
        <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
          {detail.location && <span className="flex items-center gap-1"><MapPin className="w-3.5 h-3.5" />{detail.location}</span>}
          {detail.work_types && detail.work_types.length > 0 && <span className="flex items-center gap-1"><Briefcase className="w-3.5 h-3.5" />{detail.work_types.join(', ')}</span>}
          {detail.employment_types && detail.employment_types.length > 0 && <span className="flex items-center gap-1"><ClockIcon className="w-3.5 h-3.5" />{detail.employment_types.join(', ')}</span>}
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

      <div className="grid grid-cols-4 gap-2">
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
        <div className="rounded-lg border border-border/40 bg-muted/10 p-3 text-center">
          <div className="flex items-center justify-center min-h-6">
            <GradeBadge grade={gradeForScore(detail.scores?.overall ?? null)} />
          </div>
          <p className="text-2xs text-muted-foreground">Grade</p>
        </div>
      </div>

      {detail.analysis?.recommendation && (
        <div className="rounded-lg border border-border/40 bg-muted/10 p-3">
          <p className="text-2xs font-medium text-muted-foreground uppercase tracking-wide mb-2">Recommendation</p>
          <div className="flex items-center gap-2 mb-2">
            <RecommendationBadge recommendation={detail.analysis.recommendation} />
            {detail.analysis.generated_at && (
              <span className="text-2xs text-muted-foreground">
                <DateTime value={detail.analysis.generated_at} />
              </span>
            )}
          </div>
          {detail.analysis.apply_reason && (
            <p className="text-xs text-foreground whitespace-pre-wrap">{detail.analysis.apply_reason}</p>
          )}
        </div>
      )}

      <div className="rounded-lg border border-border/40 bg-muted/10 p-3">
        <p className="text-2xs font-medium text-muted-foreground uppercase tracking-wide mb-1">Details</p>
        <DetailRow label="Role" value={detail.role} />
        <div className="flex items-start justify-between gap-4 py-1.5">
          <span className="text-2xs text-muted-foreground uppercase tracking-wide shrink-0">Company</span>
          <CompanyPicker
            companyId={detail.company_id ?? null}
            companyName={detail.company_name ?? null}
            onSelect={(id) => setCompany.mutate(id)}
            pending={setCompany.isPending}
          />
        </div>
        <DetailRow label="Status" value={detail.status} />
        <DetailRow label="Salary" value={detail.salary} />
        <DetailRow label="Visa" value={detail.visa} />
        <DetailRow label="Created" value={<DateTime value={detail.created_at} />} />
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

      {detail.analysis && <AnalysisSection analysis={detail.analysis} />}

      {detail.description && (
        <div className="rounded-lg border border-border/40 bg-muted/10 p-3">
          <p className="text-2xs font-medium text-muted-foreground uppercase tracking-wide mb-1">Description</p>
          <p className="text-xs text-foreground whitespace-pre-wrap">{detail.description}</p>
        </div>
      )}
      {detail.notes && detail.notes.length > 0 && (
        <NotesLinksReadOnly notes={detail.notes} links={[]} heading="Notes" />
      )}
      {detail.links && detail.links.length > 0 && (
        <NotesLinksReadOnly notes={[]} links={detail.links} heading="Links" />
      )}
    </div>
  )
}

export function JobDetailDrawer({ jobId, onOpenChange, onEdit }: JobDetailDrawerProps) {
  const { data: detail, isLoading, isError } = useQuery<JobDetail>({
    queryKey: ['job-detail', jobId],
    queryFn: () => jobApi.getDetail(jobId!),
    enabled: !!jobId,
  })

  return (
    <Sheet open={!!jobId} onOpenChange={(open) => { if (!open) onOpenChange(null) }}>
      <SheetContent side="right" className="job-drawer w-[400px] sm:w-[480px] p-0 flex flex-col">
        <SheetHeader className="flex flex-row items-center justify-between px-4 py-3 border-b border-border/40 shrink-0">
          <SheetTitle className="text-sm font-semibold">Job Details</SheetTitle>
          {onEdit && jobId && (
            <Button
              variant="ghost"
              size="sm"
              className="h-7 gap-1 text-xs text-muted-foreground"
              onClick={() => onEdit(jobId)}
              aria-label="Edit job"
            >
              <PencilSimple className="w-3.5 h-3.5" /> Edit
            </Button>
          )}
        </SheetHeader>
        <ScrollArea className="flex-1 min-h-0 min-w-0">
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
