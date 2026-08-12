'use client'

import { useState } from 'react'
import { Flag, PencilSimple, Trash, X } from '@phosphor-icons/react'
import { toast } from 'sonner'
import {
  useUpdateTaskMutation,
  useDeleteTaskMutation,
  useRemoveSkillLinkMutation,
} from '@/entities/roadmap/hooks'
import type { RoadmapTask, RoadmapSkillLink, TaskStatus } from '@/entities/roadmap/types'
import { Button } from '@/shared/ui/button'
import { Badge } from '@/shared/ui/badge'
import { Checkbox } from '@/shared/ui/checkbox'
import { TaskEditDialog } from './TaskEditDialog'
import { SkillLinkPopover } from './SkillLinkPopover'

const TASK_STATUS_CYCLE: TaskStatus[] = ['NOT_STARTED', 'IN_PROGRESS', 'COMPLETED', 'SKIPPED']

const PRIORITY_COLORS: Record<string, string> = {
  CRITICAL: 'text-red-500 bg-red-500/10',
  HIGH: 'text-orange-500 bg-orange-500/10',
  MEDIUM: 'text-yellow-600 bg-yellow-500/10',
  LOW: 'text-muted-foreground bg-muted',
}

function TaskSkillChip({
  link,
  roadmapId,
}: {
  link: RoadmapSkillLink
  roadmapId: string
}) {
  const removeSkillLink = useRemoveSkillLinkMutation()
  const handleRemove = () =>
    removeSkillLink.mutate(link.id, {
      onSuccess: () => toast.success('Skill unlinked'),
      onError: () => toast.error('Failed to unlink skill'),
    })
  return (
    <span className="inline-flex items-center gap-1 rounded-sm border border-border/60 bg-muted/40 px-1.5 py-0.5 text-2xs">
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

export function RoadmapTaskRow({
  task,
  roadmapId,
}: {
  task: RoadmapTask
  roadmapId: string
}) {
  const updateTask = useUpdateTaskMutation()
  const deleteTask = useDeleteTaskMutation()
  const [editOpen, setEditOpen] = useState(false)

  const cycleStatus = () => {
    const next = TASK_STATUS_CYCLE[(TASK_STATUS_CYCLE.indexOf(task.status) + 1) % TASK_STATUS_CYCLE.length]
    updateTask.mutate(
      { taskId: task.id, input: { status: next } },
      {
        onSuccess: () => toast.success(`Task marked ${next.replace('_', ' ').toLowerCase()}`),
        onError: () => toast.error('Failed to update task'),
      },
    )
  }

  const handleDelete = () => {
    deleteTask.mutate(task.id, {
      onSuccess: () => toast.success('Task deleted'),
      onError: () => toast.error('Failed to delete task'),
    })
  }

  const isDone = task.status === 'COMPLETED' || task.status === 'SKIPPED'

  return (
    <div className="rounded-md border border-border/40 bg-card/50 px-3 py-2 space-y-2">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-start gap-2 min-w-0">
          <Checkbox checked={isDone} onCheckedChange={cycleStatus} className="mt-0.5" />
          <div className="min-w-0 space-y-0.5">
            <p className={`text-xs font-medium ${isDone ? 'line-through text-muted-foreground' : ''}`}>
              {task.title}
            </p>
            {task.description && (
              <p className="text-2xs text-muted-foreground leading-relaxed">{task.description}</p>
            )}
            <div className="flex flex-wrap items-center gap-1.5 pt-0.5">
              <Badge variant="secondary" className={`text-2xs ${PRIORITY_COLORS[task.priority] ?? ''}`}>
                <Flag className="w-2.5 h-2.5" /> {task.priority}
              </Badge>
              {task.estimated_effort && <span className="text-2xs text-muted-foreground">{task.estimated_effort}</span>}
              <Badge variant="secondary" className="text-2xs">{task.status.replace('_', ' ')}</Badge>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-0.5 shrink-0">
          <SkillLinkPopover task={task} roadmapId={roadmapId} />
          <Button size="icon" variant="ghost" className="h-6 w-6" title="Edit task" onClick={() => setEditOpen(true)}>
            <PencilSimple className="w-3 h-3" />
          </Button>
          <Button
            size="icon"
            variant="ghost"
            className="h-6 w-6 text-destructive hover:text-destructive"
            title="Delete task"
            onClick={handleDelete}
          >
            <Trash className="w-3 h-3" />
          </Button>
        </div>
      </div>

      {task.success_criteria && (
        <p className="pl-6 text-2xs text-muted-foreground flex items-start gap-1">
          <Flag className="w-3 h-3 mt-0.5 shrink-0" /> {task.success_criteria}
        </p>
      )}

      {task.skills.length > 0 && (
        <div className="pl-6 flex flex-wrap gap-1">
          {task.skills.map((skill) => (
            <TaskSkillChip key={skill.id} link={skill} roadmapId={roadmapId} />
          ))}
        </div>
      )}

      <TaskEditDialog task={task} open={editOpen} onOpenChange={setEditOpen} />
    </div>
  )
}