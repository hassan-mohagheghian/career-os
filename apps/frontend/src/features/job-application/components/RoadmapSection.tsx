'use client'

import { useCallback, useState } from 'react'
import { useRouter } from 'next/navigation'
import { CircleNotch, MapTrifold } from '@phosphor-icons/react'
import { toast } from 'sonner'
import { Button } from '@/shared/ui/button'
import { Progress } from '@/shared/ui/progress'
import { Badge } from '@/shared/ui/badge'
import ConfirmDialog, { useConfirmDialog } from '@/shared/components/ConfirmDialog'
import { ApiError } from '@/shared/api'
import {
  useDeleteRoadmapMutation,
  useRoadmapByApplicationQuery,
} from '@/entities/roadmap/hooks'
import {
  useGenerateRoadmapMutation,
} from '@/entities/application/hooks'
import type { RoadmapDetail, RoadmapMilestone } from '@/entities/roadmap/types'

interface RoadmapSectionProps {
  applicationId: string
  generating: boolean
  onGenerate: () => void
}

const MILESTONE_STATUS_COLORS: Record<string, string> = {
  COMPLETED: 'text-green-600 bg-green-500/10',
  IN_PROGRESS: 'text-blue-600 bg-blue-500/10',
  NOT_STARTED: 'text-muted-foreground bg-muted',
}

const MILESTONE_PRIORITY_COLORS: Record<string, string> = {
  CRITICAL: 'text-red-500 bg-red-500/10',
  HIGH: 'text-orange-500 bg-orange-500/10',
  MEDIUM: 'text-yellow-600 bg-yellow-500/10',
  LOW: 'text-muted-foreground bg-muted',
}

function OverviewBadge({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <span
      className={`inline-flex items-center rounded-sm px-1.5 py-0.5 text-2xs font-medium shrink-0 ${className ?? 'bg-muted text-muted-foreground'}`}
    >
      {children}
    </span>
  )
}

function RoadmapMilestoneOverviewRow({ milestone, index }: { milestone: RoadmapMilestone; index: number }) {
  const done = milestone.tasks.filter((t) => t.status === 'COMPLETED' || t.status === 'SKIPPED').length
  const total = milestone.tasks.length
  const percent = total === 0 ? 0 : Math.round((done / total) * 100)
  return (
    <div className="flex items-center gap-2 py-1.5">
      <span className="flex items-center justify-center w-5 h-5 rounded-full bg-emerald-500/15 text-emerald-600 text-2xs font-semibold shrink-0">
        {index + 1}
      </span>
      <div className="flex items-center gap-1.5 min-w-0 flex-1">
        <p className="text-xs font-medium truncate">{milestone.title}</p>
        <OverviewBadge className={MILESTONE_STATUS_COLORS[milestone.status]}>
          {milestone.status.replace('_', ' ')}
        </OverviewBadge>
        <OverviewBadge className={MILESTONE_PRIORITY_COLORS[milestone.priority]}>
          {milestone.priority}
        </OverviewBadge>
      </div>
      <span className="text-2xs text-muted-foreground shrink-0">{done}/{total}</span>
      <div className="w-16 shrink-0">
        <Progress value={percent} />
      </div>
    </div>
  )
}

function RoadmapReadyCard({ roadmap, onView, onRegenerate, onDelete, deleting, regenerating }: {
  roadmap: RoadmapDetail
  onView: () => void
  onRegenerate: () => void
  onDelete: () => void
  deleting: boolean
  regenerating: boolean
}) {
  const goalTitle = roadmap.goal?.title ?? roadmap.title
  const milestones = roadmap.milestones.slice().sort((a, b) => a.position - b.position)
  return (
    <div className="space-y-3">
      <div className="rounded-lg border border-border/40 bg-muted/10 p-3 space-y-2">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 space-y-1">
            <p className="text-xs font-semibold text-foreground truncate">{roadmap.title}</p>
            {goalTitle && goalTitle !== roadmap.title && (
              <p className="text-2xs text-muted-foreground">Goal: {goalTitle}</p>
            )}
          </div>
          <div className="flex items-center gap-1.5 shrink-0">
            <Badge variant="secondary" className="text-2xs">{roadmap.status}</Badge>
          </div>
        </div>
        <div className="space-y-1">
          <Progress value={roadmap.progress.overall_percent} />
          <div className="flex items-center justify-between text-2xs text-muted-foreground">
            <span>{roadmap.progress.completed_tasks}/{roadmap.progress.total_tasks} tasks done</span>
            <span>{roadmap.progress.overall_percent}%</span>
          </div>
        </div>

        {milestones.length > 0 && (
          <div className="border-t border-border/40 pt-2">
            <p className="text-2xs font-medium text-muted-foreground uppercase tracking-wide pb-1">
              Milestones
            </p>
            <div className="divide-y divide-border/40">
              {milestones.slice(0, 5).map((milestone, index) => (
                <RoadmapMilestoneOverviewRow key={milestone.id} milestone={milestone} index={index} />
              ))}
            </div>
            {milestones.length > 5 && (
              <p className="pt-2 text-2xs text-muted-foreground">
                +{milestones.length - 5} more milestone{milestones.length - 5 > 1 ? 's' : ''}
              </p>
            )}
          </div>
        )}
      </div>
      <div className="flex items-center gap-2">
        <Button size="sm" variant="outline" className="h-7 gap-1 text-xs" onClick={onView}>
          <MapTrifold className="w-3.5 h-3.5" />
          View roadmap
        </Button>
        <Button size="sm" variant="outline" className="h-7 gap-1 text-xs" onClick={onRegenerate} disabled={regenerating}>
          {regenerating ? <CircleNotch className="w-3.5 h-3.5 animate-spin" /> : <MapTrifold className="w-3.5 h-3.5" />}
          Regenerate
        </Button>
        <Button
          size="sm"
          variant="ghost"
          className="h-7 text-xs text-destructive hover:text-destructive"
          onClick={onDelete}
          disabled={deleting}
        >
          Delete
        </Button>
      </div>
    </div>
  )
}

export function RoadmapSection({ applicationId, generating, onGenerate }: RoadmapSectionProps) {
  const router = useRouter()
  const { dialog: confirmDialog, showConfirm, onClose: closeConfirm } = useConfirmDialog()
  const [deleting, setDeleting] = useState(false)

  const roadmapQuery = useRoadmapByApplicationQuery(applicationId)
  const deleteRoadmap = useDeleteRoadmapMutation()

  const roadmap = roadmapQuery.isSuccess ? roadmapQuery.data : null
  const notFound = roadmapQuery.isError &&
    roadmapQuery.error instanceof ApiError &&
    roadmapQuery.error.status === 404

  const handleDelete = useCallback(async () => {
    const ok = await showConfirm(
      'Delete Roadmap',
      'Permanently delete this roadmap and all its milestones and tasks?',
      'Delete',
    )
    if (!ok) return
    setDeleting(true)
    deleteRoadmap.mutate(roadmap.id, {
      onSuccess: () => {
        setDeleting(false)
        toast.success('Roadmap deleted')
      },
      onError: () => {
        setDeleting(false)
        toast.error('Failed to delete roadmap')
      },
    })
  }, [showConfirm, deleteRoadmap, roadmap])

  if (notFound || !roadmapQuery.data || roadmap === null) {
    return (
      <div className="flex items-start justify-between gap-2">
        <p className="pt-2 text-xs text-muted-foreground">
          No roadmap yet. Generate a step-by-step job-preparation roadmap from the job analysis and your profile.
        </p>
        <Button size="sm" variant="outline" className="h-7 gap-1 text-xs" onClick={onGenerate} disabled={generating}>
          {generating ? <CircleNotch className="w-3.5 h-3.5 animate-spin" /> : <MapTrifold className="w-3.5 h-3.5" />}
          Generate roadmap
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <RoadmapReadyCard
        roadmap={roadmap}
        onView={() => router.push(`/roadmaps/${roadmap.id}`)}
        onRegenerate={onGenerate}
        onDelete={handleDelete}
        deleting={deleting}
        regenerating={generating}
      />
      <ConfirmDialog dialog={confirmDialog} onClose={closeConfirm} />
    </div>
  )
}