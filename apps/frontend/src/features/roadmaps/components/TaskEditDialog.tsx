'use client'

import { useEffect, useState } from 'react'
import { ListChecks, PencilSimple, Plus, Trash } from '@phosphor-icons/react'
import { toast } from 'sonner'
import {
  useUpdateTaskMutation,
  useDeleteTaskMutation,
  useAddTaskMutation,
} from '@/entities/roadmap/hooks'
import type { NodePriority, RoadmapTask, TaskStatus } from '@/entities/roadmap/types'
import { Button } from '@/shared/ui/button'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { Textarea } from '@/shared/ui/textarea'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/shared/ui/dialog'
import { PRIORITY_OPTIONS } from './MilestoneEditDialog'

const TASK_STATUS_OPTIONS: { value: TaskStatus; label: string }[] = [
  { value: 'NOT_STARTED', label: 'Not started' },
  { value: 'IN_PROGRESS', label: 'In progress' },
  { value: 'COMPLETED', label: 'Completed' },
  { value: 'SKIPPED', label: 'Skipped' },
]

export function TaskEditDialog({
  task,
  milestoneId,
  open,
  onOpenChange,
}: {
  task?: RoadmapTask | null
  milestoneId?: string
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const updateTask = useUpdateTaskMutation()
  const deleteTask = useDeleteTaskMutation()
  const addTask = useAddTaskMutation()

  const isEdit = !!task
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [priority, setPriority] = useState<NodePriority>('MEDIUM')
  const [status, setStatus] = useState<TaskStatus>('NOT_STARTED')
  const [estimatedEffort, setEstimatedEffort] = useState('')
  const [successCriteria, setSuccessCriteria] = useState('')

  useEffect(() => {
    if (open) {
      setTitle(task?.title ?? '')
      setDescription(task?.description ?? '')
      setPriority(task?.priority ?? 'MEDIUM')
      setStatus(task?.status ?? 'NOT_STARTED')
      setEstimatedEffort(task?.estimated_effort ?? '')
      setSuccessCriteria(task?.success_criteria ?? '')
    }
  }, [open, task])

  const close = () => onOpenChange(false)

  const handleSubmit = () => {
    const common = {
      title,
      description,
      priority,
      estimated_effort: estimatedEffort || null,
      success_criteria: successCriteria || null,
    }
    if (isEdit) {
      updateTask.mutate(
        { taskId: task.id, input: { ...common, status } },
        {
          onSuccess: () => {
            toast.success('Task updated')
            close()
          },
          onError: () => toast.error('Failed to update task'),
        },
      )
    } else if (milestoneId) {
      addTask.mutate(
        { milestoneId, input: common },
        {
          onSuccess: () => {
            toast.success('Task added')
            close()
          },
          onError: () => toast.error('Failed to add task'),
        },
      )
    }
  }

  const handleDelete = () => {
    if (!task) return
    deleteTask.mutate(task.id, {
      onSuccess: () => {
        toast.success('Task deleted')
        close()
      },
      onError: () => toast.error('Failed to delete task'),
    })
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {isEdit ? <PencilSimple className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
            {isEdit ? 'Edit Task' : 'Add Task'}
          </DialogTitle>
          <DialogDescription>
            {isEdit ? 'Update task details.' : 'Add a new task to this milestone.'}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          <div className="space-y-1">
            <Label htmlFor="te-title">Title</Label>
            <Input id="te-title" value={title} onChange={(e) => setTitle(e.target.value)} />
          </div>
          <div className="space-y-1">
            <Label htmlFor="te-description">Description</Label>
            <Textarea id="te-description" value={description} onChange={(e) => setDescription(e.target.value)} rows={3} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <Label htmlFor="te-priority">Priority</Label>
              <Select value={priority} onValueChange={(v) => setPriority(v as NodePriority)}>
                <SelectTrigger>
                  <SelectValue placeholder="Priority" />
                </SelectTrigger>
                <SelectContent>
                  {PRIORITY_OPTIONS.map((o) => (
                    <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {isEdit && (
              <div className="space-y-1">
                <Label htmlFor="te-status">Status</Label>
                <Select value={status} onValueChange={(v) => setStatus(v as TaskStatus)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Status" />
                  </SelectTrigger>
                  <SelectContent>
                    {TASK_STATUS_OPTIONS.map((o) => (
                      <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>
          <div className="space-y-1">
            <Label htmlFor="te-effort">Estimated effort</Label>
            <Input id="te-effort"
              value={estimatedEffort}
              onChange={(e) => setEstimatedEffort(e.target.value)}
              placeholder="e.g. 3 hours"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="te-criteria">Success criteria</Label>
            <Textarea id="te-criteria" value={successCriteria} onChange={(e) => setSuccessCriteria(e.target.value)} rows={2} />
          </div>
        </div>
        <DialogFooter>
          {isEdit && (
            <Button variant="ghost" className="text-destructive hover:text-destructive mr-auto" onClick={handleDelete}>
              <Trash className="w-3 h-3" /> Delete
            </Button>
          )}
          <Button onClick={handleSubmit} disabled={!title.trim() || updateTask.isPending || addTask.isPending}>
            <ListChecks className="w-3.5 h-3.5" />
            {isEdit ? 'Save' : 'Add'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}