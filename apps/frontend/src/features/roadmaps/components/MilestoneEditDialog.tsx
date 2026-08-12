'use client'

import { useEffect, useState } from 'react'
import { PencilSimple, Plus } from '@phosphor-icons/react'
import { toast } from 'sonner'
import {
  useUpdateMilestoneMutation,
  useDeleteMilestoneMutation,
} from '@/entities/roadmap/hooks'
import type { MilestoneStatus, NodePriority, RoadmapMilestone } from '@/entities/roadmap/types'
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

export const PRIORITY_OPTIONS: { value: NodePriority; label: string }[] = [
  { value: 'CRITICAL', label: 'Critical' },
  { value: 'HIGH', label: 'High' },
  { value: 'MEDIUM', label: 'Medium' },
  { value: 'LOW', label: 'Low' },
]

export const MILESTONE_STATUS_OPTIONS: { value: MilestoneStatus; label: string }[] = [
  { value: 'NOT_STARTED', label: 'Not started' },
  { value: 'IN_PROGRESS', label: 'In progress' },
  { value: 'COMPLETED', label: 'Completed' },
]

export function MilestoneEditDialog({
  open,
  onOpenChange,
  milestone,
  onSubmit,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  milestone?: RoadmapMilestone | null
  onSubmit?: (input: { title: string; description: string; priority: NodePriority }) => void
}) {
  const updateMilestone = useUpdateMilestoneMutation()
  const deleteMilestone = useDeleteMilestoneMutation()

  const isEdit = !!milestone
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [priority, setPriority] = useState<NodePriority>('MEDIUM')
  const [status, setStatus] = useState<MilestoneStatus>('NOT_STARTED')

  useEffect(() => {
    if (open) {
      setTitle(milestone?.title ?? '')
      setDescription(milestone?.description ?? '')
      setPriority(milestone?.priority ?? 'MEDIUM')
      setStatus(milestone?.status ?? 'NOT_STARTED')
    }
  }, [open, milestone])

  const close = () => onOpenChange(false)

  const handleSubmit = () => {
    if (isEdit) {
      updateMilestone.mutate(
        { milestoneId: milestone.id, input: { title, description, priority, status } },
        {
          onSuccess: () => {
            toast.success('Milestone updated')
            close()
          },
          onError: () => toast.error('Failed to update milestone'),
        },
      )
    } else {
      onSubmit?.({ title, description, priority })
    }
  }

  const handleDelete = () => {
    if (!milestone) return
    deleteMilestone.mutate(milestone.id, {
      onSuccess: () => {
        toast.success('Milestone deleted')
        close()
      },
      onError: () => toast.error('Failed to delete milestone'),
    })
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {isEdit ? <PencilSimple className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
            {isEdit ? 'Edit Milestone' : 'Add Milestone'}
          </DialogTitle>
          <DialogDescription>
            {isEdit ? 'Update milestone details.' : 'Add a new milestone to this journey.'}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          <div className="space-y-1">
            <Label htmlFor="me-title">Title</Label>
            <Input id="me-title" value={title} onChange={(e) => setTitle(e.target.value)} />
          </div>
          <div className="space-y-1">
            <Label htmlFor="me-description">Description</Label>
            <Textarea id="me-description" value={description} onChange={(e) => setDescription(e.target.value)} rows={3} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <Label htmlFor="me-priority">Priority</Label>
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
                <Label htmlFor="me-status">Status</Label>
                <Select value={status} onValueChange={(v) => setStatus(v as MilestoneStatus)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Status" />
                  </SelectTrigger>
                  <SelectContent>
                    {MILESTONE_STATUS_OPTIONS.map((o) => (
                      <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>
        </div>
        <DialogFooter>
          {isEdit && (
            <Button variant="ghost" className="text-destructive hover:text-destructive mr-auto" onClick={handleDelete}>
              Delete
            </Button>
          )}
          <Button onClick={handleSubmit} disabled={!title.trim() || updateMilestone.isPending}>
            {isEdit ? 'Save' : 'Add'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}