'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  ArrowLeft,
  MapTrifold,
  Plus,
  PencilSimple,
  Trash,
  ClockCounterClockwise,
} from '@phosphor-icons/react'
import { toast } from 'sonner'
import {
  useRoadmapQuery,
  useDeleteRoadmapMutation,
  useAddMilestoneMutation,
} from '@/entities/roadmap/hooks'
import type { RoadmapDetail, NodePriority } from '@/entities/roadmap/types'
import { Button } from '@/shared/ui/button'
import { Badge } from '@/shared/ui/badge'
import { Progress } from '@/shared/ui/progress'
import ConfirmDialog, { useConfirmDialog } from '@/shared/components/ConfirmDialog'
import { RoadmapMilestoneNode } from './RoadmapMilestoneNode'
import { RoadmapEditDialog } from './RoadmapEditDialog'
import { MilestoneEditDialog } from './MilestoneEditDialog'

export function RoadmapDetailPage({ roadmapId }: { roadmapId: string }) {
  const router = useRouter()
  const { data: roadmap, isLoading, isError, refetch } = useRoadmapQuery(roadmapId)
  const deleteRoadmap = useDeleteRoadmapMutation()
  const addMilestone = useAddMilestoneMutation()
  const { dialog: confirmDialog, showConfirm, onClose: closeConfirm } = useConfirmDialog()

  const [editOpen, setEditOpen] = useState(false)
  const [addMilestoneOpen, setAddMilestoneOpen] = useState(false)
  const [editingMilestone, setEditingMilestone] = useState<RoadmapDetail['milestones'][number] | null>(null)

  const handleDelete = async (roadmap: RoadmapDetail) => {
    const ok = await showConfirm(
      'Delete Roadmap',
      `Permanently delete "${roadmap.title}" and all its milestones and tasks?`,
      'Delete',
    )
    if (!ok) return
    deleteRoadmap.mutate(roadmap.id, {
      onSuccess: () => {
        toast.success('Roadmap deleted')
        router.push('/roadmaps')
      },
      onError: () => toast.error('Failed to delete roadmap'),
    })
  }

  const handleAddMilestone = (input: { title: string; description: string; priority: NodePriority }) => {
    addMilestone.mutate(
      { roadmapId, input },
      {
        onSuccess: () => {
          toast.success('Milestone added')
          setAddMilestoneOpen(false)
        },
        onError: () => toast.error('Failed to add milestone'),
      },
    )
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64 text-muted-foreground">
        Loading roadmap...
      </div>
    )
  }

  if (isError || !roadmap) {
    return (
      <div className="space-y-4 p-6">
        <div className="flex flex-col items-center justify-center py-16 text-center space-y-3">
          <p className="text-sm text-red-500">Failed to load roadmap.</p>
          <div className="flex items-center gap-2">
            <Button size="sm" variant="outline" onClick={() => refetch()}>Retry</Button>
            <Button size="sm" variant="ghost" onClick={() => router.push('/roadmaps')}>
              <ArrowLeft className="w-3.5 h-3.5" /> Back
            </Button>
          </div>
        </div>
      </div>
    )
  }

  const goal = roadmap.goal

  return (
    <div className="space-y-5 p-6">
      <div className="flex items-center gap-2">
        <Button size="sm" variant="ghost" className="h-7 gap-1 text-xs" onClick={() => router.push('/roadmaps')}>
          <ArrowLeft className="w-3.5 h-3.5" />
          My Roadmaps
        </Button>
      </div>

      <div className="rounded-lg border border-border/40 bg-muted/10 p-4 space-y-3">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 space-y-1">
            <div className="flex items-center gap-2">
              <MapTrifold className="w-5 h-5 text-emerald-500 shrink-0" />
              <h1 className="text-lg font-bold leading-tight truncate">{roadmap.title}</h1>
            </div>
            {roadmap.description && (
              <p className="text-xs text-muted-foreground leading-relaxed">{roadmap.description}</p>
            )}
            <div className="flex items-center gap-1.5 pt-1">
              <Badge variant="outline">{roadmap.source}</Badge>
              <Badge variant="secondary">{roadmap.status}</Badge>
              {goal?.type && <Badge variant="secondary">{goal.type}</Badge>}
            </div>
          </div>
          <div className="flex items-center gap-1.5 shrink-0">
            <Button size="sm" variant="outline" className="h-7 gap-1 text-xs" onClick={() => setEditOpen(true)}>
              <PencilSimple className="w-3.5 h-3.5" />
              Edit
            </Button>
            <Button size="sm" variant="outline" className="h-7 gap-1 text-xs" disabled title="Version history (Phase 2)">
              <ClockCounterClockwise className="w-3.5 h-3.5" />
              History
            </Button>
            <Button
              size="sm"
              variant="ghost"
              className="h-7 gap-1 text-xs text-destructive hover:text-destructive"
              onClick={() => handleDelete(roadmap)}
            >
              <Trash className="w-3.5 h-3.5" />
              Delete
            </Button>
          </div>
        </div>

        {goal && (
          <div className="space-y-1 border-t border-border/40 pt-3">
            <p className="text-xs font-medium text-muted-foreground">
              Goal: {goal.type}
              {goal.target_job_id && ` · Job`}
              {goal.target_company_id && ` · Company`}
              {goal.target_skill_id && ` · Skill`}
            </p>
            <p className="text-sm font-medium">{goal.title}</p>
            {goal.description && <p className="text-xs text-muted-foreground">{goal.description}</p>}
          </div>
        )}

        <div className="space-y-1 border-t border-border/40 pt-3">
          <Progress value={roadmap.progress.overall_percent} />
          <div className="flex items-center justify-between text-2xs text-muted-foreground">
            <span>
              {roadmap.progress.completed_tasks}/{roadmap.progress.total_tasks} tasks done
            </span>
            <span>{roadmap.progress.overall_percent}%</span>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Journey</p>
        <Button size="sm" variant="outline" className="h-7 gap-1 text-xs" onClick={() => setAddMilestoneOpen(true)}>
          <Plus className="w-3.5 h-3.5" />
          Add Milestone
        </Button>
      </div>

      {roadmap.milestones.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-center space-y-3">
          <MapTrifold className="w-8 h-8 text-muted-foreground/50" />
          <p className="text-xs text-muted-foreground">
            No milestones yet. Add your first milestone to start the journey.
          </p>
          <Button size="sm" className="gap-1" onClick={() => setAddMilestoneOpen(true)}>
            <Plus className="w-3.5 h-3.5" />
            Add Milestone
          </Button>
        </div>
      ) : (
        <div className="space-y-4">
          {roadmap.milestones
            .slice()
            .sort((a, b) => a.position - b.position)
            .map((milestone, index) => (
              <RoadmapMilestoneNode
                key={milestone.id}
                milestone={milestone}
                roadmapId={roadmap.id}
                index={index}
                onEdit={() => setEditingMilestone(milestone)}
                notes={roadmap.notes.filter((n) => n.milestone_id === milestone.id && !n.task_id)}
                resources={roadmap.resources.filter((r) => r.milestone_id === milestone.id && !r.task_id)}
              />
            ))}
        </div>
      )}

      <RoadmapEditDialog roadmap={roadmap} open={editOpen} onOpenChange={setEditOpen} />
      <MilestoneEditDialog
        open={addMilestoneOpen}
        onOpenChange={setAddMilestoneOpen}
        onSubmit={handleAddMilestone}
      />
      <MilestoneEditDialog
        open={!!editingMilestone}
        onOpenChange={(open) => !open && setEditingMilestone(null)}
        milestone={editingMilestone}
      />
      <ConfirmDialog dialog={confirmDialog} onClose={closeConfirm} />
    </div>
  )
}