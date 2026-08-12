'use client'

import { useEffect, useState } from 'react'
import { PencilSimple } from '@phosphor-icons/react'
import { toast } from 'sonner'
import { useUpdateRoadmapMutation } from '@/entities/roadmap/hooks'
import type { RoadmapSummary, RoadmapStatus } from '@/entities/roadmap/types'
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

export function RoadmapEditDialog({
  roadmap,
  open,
  onOpenChange,
}: {
  roadmap: RoadmapSummary | null
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const updateRoadmap = useUpdateRoadmapMutation()
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [status, setStatus] = useState<RoadmapStatus>('ACTIVE')

  useEffect(() => {
    if (open && roadmap) {
      setTitle(roadmap.title)
      setDescription(roadmap.description)
      setStatus(roadmap.status)
    }
  }, [open, roadmap])

  const handleSubmit = () => {
    updateRoadmap.mutate(
      { roadmapId: roadmap!.id, input: { title, description, status } },
      {
        onSuccess: () => {
          toast.success('Roadmap updated')
          onOpenChange(false)
        },
        onError: () => toast.error('Failed to update roadmap'),
      },
    )
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <PencilSimple className="w-4 h-4" />
            Edit Roadmap
          </DialogTitle>
          <DialogDescription>Update roadmap details and status.</DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          <div className="space-y-1">
            <Label htmlFor="re-title">Title</Label>
            <Input id="re-title" value={title} onChange={(e) => setTitle(e.target.value)} />
          </div>
          <div className="space-y-1">
            <Label htmlFor="re-description">Description</Label>
            <Textarea id="re-description" value={description} onChange={(e) => setDescription(e.target.value)} rows={3} />
          </div>
          <div className="space-y-1">
            <Label>Status</Label>
            <Select value={status} onValueChange={(v) => setStatus(v as RoadmapStatus)}>
              <SelectTrigger>
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ACTIVE">Active</SelectItem>
                <SelectItem value="COMPLETED">Completed</SelectItem>
                <SelectItem value="ARCHIVED">Archived</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
        <DialogFooter>
          <Button onClick={handleSubmit} disabled={!title.trim() || updateRoadmap.isPending}>
            Save
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}