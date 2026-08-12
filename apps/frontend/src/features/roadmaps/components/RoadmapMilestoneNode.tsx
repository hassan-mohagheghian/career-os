'use client'

import { useState } from 'react'
import { CaretDown, Link, Plus, PencilSimple, Trash, X } from '@phosphor-icons/react'
import { toast } from 'sonner'
import {
  useRemoveSkillLinkMutation,
  useDeleteMilestoneMutation,
} from '@/entities/roadmap/hooks'
import type { RoadmapMilestone, RoadmapNote, RoadmapResource, RoadmapSkillLink } from '@/entities/roadmap/types'
import { Button } from '@/shared/ui/button'
import { Progress } from '@/shared/ui/progress'
import ConfirmDialog, { useConfirmDialog } from '@/shared/components/ConfirmDialog'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/shared/ui/collapsible'
import { RoadmapTaskRow } from './RoadmapTaskRow'
import { TaskEditDialog } from './TaskEditDialog'
import { NotesSection } from './NotesSection'
import { ResourcesSection } from './ResourcesSection'
import { SkillLinkPopover } from './SkillLinkPopover'

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

function MilestoneSkillChip({ link }: { link: RoadmapSkillLink }) {
  const removeSkillLink = useRemoveSkillLinkMutation()
  const handleRemove = () =>
    removeSkillLink.mutate(link.id, {
      onSuccess: () => toast.success('Skill unlinked'),
      onError: () => toast.error('Failed to unlink skill'),
    })
  return (
    <span className="inline-flex items-center gap-1 rounded-sm border border-border/60 bg-muted/40 px-1.5 py-0.5 text-2xs">
      <Link className="w-2.5 h-2.5" />
      {link.skill_name}
      <button
        type="button"
        title={`Unlink ${link.skill_name}`}
        onClick={handleRemove}
        className="text-muted-foreground hover:text-destructive"
      >
        <X className="w-2.5 h-2.5" />
      </button>
    </span>
  )
}

function MilestoneBadge({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <span className={`inline-flex items-center gap-1 rounded-sm px-1.5 py-0.5 text-2xs font-medium ${className ?? 'bg-muted text-muted-foreground'}`}>
      {children}
    </span>
  )
}

export function RoadmapMilestoneNode({
  milestone,
  roadmapId,
  index,
  onEdit,
  notes,
  resources,
}: {
  milestone: RoadmapMilestone
  roadmapId: string
  index: number
  onEdit: () => void
  notes: RoadmapNote[]
  resources: RoadmapResource[]
}) {
  const deleteMilestone = useDeleteMilestoneMutation()
  const { dialog: confirmDialog, showConfirm, onClose: closeConfirm } = useConfirmDialog()
  const [open, setOpen] = useState(true)
  const [addTaskOpen, setAddTaskOpen] = useState(false)

  const done = milestone.tasks.filter((t) => t.status === 'COMPLETED' || t.status === 'SKIPPED').length
  const total = milestone.tasks.length
  const percent = total === 0 ? 0 : Math.round((done / total) * 100)

  const handleDelete = async () => {
    const ok = await showConfirm(
      'Delete Milestone',
      `Permanently delete "${milestone.title}" and all its tasks?`,
      'Delete',
    )
    if (!ok) return
    deleteMilestone.mutate(milestone.id, {
      onSuccess: () => toast.success('Milestone deleted'),
      onError: () => toast.error('Failed to delete milestone'),
    })
  }

  return (
    <div className="rounded-lg border border-border/40 bg-muted/5 overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-1 border-b border-border/40 justify-end">
        <Button size="sm" variant="ghost" className="h-6 gap-1 text-2xs" onClick={() => setAddTaskOpen(true)}>
          <Plus className="w-3 h-3" /> Task
        </Button>
        <Button size="sm" variant="ghost" className="h-6 gap-1 text-2xs" onClick={onEdit}>
          <PencilSimple className="w-3 h-3" /> Edit
        </Button>
        <Button
          size="sm"
          variant="ghost"
          className="h-6 gap-1 text-2xs text-destructive hover:text-destructive"
          onClick={handleDelete}
        >
          <Trash className="w-3 h-3" /> Delete
        </Button>
      </div>

      <Collapsible open={open} onOpenChange={setOpen}>
        <CollapsibleTrigger asChild>
          <button
            type="button"
            className="w-full flex items-center justify-between gap-2 px-4 py-3 text-left hover:bg-muted/10"
          >
            <div className="flex items-center gap-3 min-w-0">
              <span className="flex items-center justify-center w-6 h-6 rounded-full bg-emerald-500/15 text-emerald-600 text-2xs font-semibold shrink-0">
                {index + 1}
              </span>
              <div className="min-w-0 space-y-0.5">
                <p className="text-xs font-semibold truncate">{milestone.title}</p>
                {milestone.description && (
                  <p className="text-2xs text-muted-foreground line-clamp-1">{milestone.description}</p>
                )}
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <span className="text-2xs text-muted-foreground hidden sm:inline-flex">
                {done}/{total} · {percent}%
              </span>
              <div className="w-20">
                <Progress value={percent} />
              </div>
              <CaretDown className={`w-4 h-4 text-muted-foreground transition-transform ${open ? 'rotate-180' : ''}`} />
            </div>
          </button>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <div className="px-4 pb-3 space-y-3">
            <div className="flex flex-wrap items-center gap-1.5">
              <MilestoneBadge className={MILESTONE_STATUS_COLORS[milestone.status]}>
                {milestone.status.replace('_', ' ')}
              </MilestoneBadge>
              <MilestoneBadge className={MILESTONE_PRIORITY_COLORS[milestone.priority]}>
                {milestone.priority}
              </MilestoneBadge>
              {milestone.skills.map((skill) => (
                <MilestoneSkillChip key={skill.id} link={skill} />
              ))}
              <SkillLinkPopover milestone={milestone} roadmapId={roadmapId} />
            </div>

            <div className="space-y-2">
              {milestone.tasks
                .slice()
                .sort((a, b) => a.position - b.position)
                .map((task) => (
                  <RoadmapTaskRow key={task.id} task={task} roadmapId={roadmapId} />
                ))}
              {milestone.tasks.length === 0 && (
                <p className="text-2xs text-muted-foreground">No tasks in this milestone yet.</p>
              )}
            </div>

            <NotesSection roadmapId={roadmapId} notes={notes} milestoneId={milestone.id} />
            <ResourcesSection roadmapId={roadmapId} resources={resources} milestoneId={milestone.id} />
          </div>
        </CollapsibleContent>
      </Collapsible>

      <TaskEditDialog
        milestoneId={milestone.id}
        open={addTaskOpen}
        onOpenChange={setAddTaskOpen}
      />
      <ConfirmDialog dialog={confirmDialog} onClose={closeConfirm} />
    </div>
  )
}