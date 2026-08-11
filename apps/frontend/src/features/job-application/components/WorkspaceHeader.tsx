'use client'

import Link from 'next/link'
import { ArrowLeft, LinkSimple } from '@phosphor-icons/react'
import type { JobDetail } from '@/entities/job/types'
import { GradeBadge } from '@/shared/components/GradeBadge'
import { gradeForScore, scoreColor } from '@/shared/lib/grade'
import { RecommendationBadge } from '@/features/jobs-v2/components/RecommendationBadge'
import { ApplicationStatusBadge } from './ApplicationStatusBadge'
import type { ApplicationStatus } from '@/entities/application/types'

interface WorkspaceHeaderProps {
  job: JobDetail
  applicationStatus: ApplicationStatus
}

function ScoreCard({ label, value }: { label: string; value: number | null }) {
  return (
    <div className="flex flex-col items-center">
      <div className={`text-lg font-bold ${scoreColor(value)}`}>{value ?? '—'}</div>
      <div className="text-2xs uppercase tracking-wider text-muted-foreground font-semibold">
        {label}
      </div>
    </div>
  )
}

export function WorkspaceHeader({ job, applicationStatus }: WorkspaceHeaderProps) {
  return (
    <div className="border-b border-border/40 pb-4">
      <div className="flex items-center justify-between gap-4 mb-3">
        <Link
          href={`/jobs?job=${job.id}`}
          className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to Job
        </Link>
        {job.url && (
          <a
            href={job.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-xs text-blue-500 hover:underline"
          >
            <LinkSimple className="w-3.5 h-3.5" /> Open job posting
          </a>
        )}
      </div>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h1 className="text-lg font-semibold text-foreground">
            {job.title || job.role || 'Untitled'}
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            {job.company_name || 'Unknown company'}
            {job.location ? ` · ${job.location}` : ''}
          </p>
          <div className="flex items-center gap-2 mt-2">
            <ApplicationStatusBadge status={applicationStatus} />
            <RecommendationBadge recommendation={job.analysis?.recommendation ?? null} />
          </div>
        </div>
        <div className="flex items-center gap-4 shrink-0">
          <GradeBadge
            grade={gradeForScore(job.scores?.overall ?? null)}
            className="w-10 h-8 text-sm"
          />
          <ScoreCard label="Fit" value={job.scores?.fit ?? null} />
          <ScoreCard label="Success" value={job.scores?.success ?? null} />
          <ScoreCard label="Overall" value={job.scores?.overall ?? null} />
        </div>
      </div>
    </div>
  )
}
