'use client'

import { useState } from 'react'
import { BookmarkSimple, Plus, Trash, Link as LinkIcon } from '@phosphor-icons/react'
import { toast } from 'sonner'
import { useAddResourceMutation, useDeleteResourceMutation, useUpdateResourceMutation } from '@/entities/roadmap/hooks'
import type { ResourceStatus, ResourceType, RoadmapResource } from '@/entities/roadmap/types'
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

export function AddResourceDialog({
  open,
  onOpenChange,
  onSubmit,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSubmit: (input: { title: string; url: string; description: string; type: ResourceType }) => void
}) {
  const [title, setTitle] = useState('')
  const [url, setUrl] = useState('')
  const [description, setDescription] = useState('')
  const [type, setType] = useState<ResourceType>('ARTICLE')

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Plus className="w-4 h-4" /> Add Resource
          </DialogTitle>
          <DialogDescription>Add a learning resource to this milestone.</DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          <div className="space-y-1">
            <Label>Title</Label>
            <Input value={title} onChange={(e) => setTitle(e.target.value)} />
          </div>
          <div className="space-y-1">
            <Label>URL</Label>
            <Input value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://..." />
          </div>
          <div className="space-y-1">
            <Label>Type</Label>
            <Select value={type} onValueChange={(v) => setType(v as ResourceType)}>
              <SelectTrigger>
                <SelectValue placeholder="Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ARTICLE">Article</SelectItem>
                <SelectItem value="VIDEO">Video</SelectItem>
                <SelectItem value="COURSE">Course</SelectItem>
                <SelectItem value="BOOK">Book</SelectItem>
                <SelectItem value="DOCUMENTATION">Documentation</SelectItem>
                <SelectItem value="PROJECT">Project</SelectItem>
                <SelectItem value="OTHER">Other</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1">
            <Label>Description</Label>
            <Textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={2} />
          </div>
        </div>
        <DialogFooter>
          <Button onClick={() => onSubmit({ title, url, description, type })} disabled={!title.trim()}>
            Add
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export function ResourcesSection({
  roadmapId,
  resources,
  milestoneId,
  taskId,
}: {
  roadmapId: string
  resources: RoadmapResource[]
  milestoneId?: string
  taskId?: string
}) {
  const addResource = useAddResourceMutation()
  const updateResource = useUpdateResourceMutation()
  const deleteResource = useDeleteResourceMutation()
  const [open, setOpen] = useState(false)

  const handleAdd = (input: { title: string; url: string; description: string; type: ResourceType }) => {
    addResource.mutate(
      { roadmapId, input: { ...input, milestone_id: milestoneId ?? null, task_id: taskId ?? null } },
      {
        onSuccess: () => {
          toast.success('Resource added')
          setOpen(false)
        },
        onError: () => toast.error('Failed to add resource'),
      },
    )
  }

  const cycleStatus = (resource: RoadmapResource) => {
    const next: Record<ResourceStatus, ResourceStatus> = {
      PLANNED: 'IN_PROGRESS',
      IN_PROGRESS: 'COMPLETED',
      COMPLETED: 'PLANNED',
    }
    updateResource.mutate(
      { resourceId: resource.id, input: { status: next[resource.status] } },
      {
        onSuccess: () => toast.success('Resource status updated'),
        onError: () => toast.error('Failed to update resource'),
      },
    )
  }

  const handleDelete = (resourceId: string) => {
    deleteResource.mutate(resourceId, {
      onSuccess: () => toast.success('Resource deleted'),
      onError: () => toast.error('Failed to delete resource'),
    })
  }

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <p className="text-2xs font-medium text-muted-foreground uppercase tracking-wide inline-flex items-center gap-1">
          <BookmarkSimple className="w-3 h-3" /> Resources ({resources.length})
        </p>
        <Button size="sm" variant="ghost" className="h-6 gap-1 text-2xs" onClick={() => setOpen(true)}>
          <Plus className="w-3 h-3" /> Add
        </Button>
      </div>
      {resources.length === 0 && <p className="text-2xs text-muted-foreground">No resources yet.</p>}
      {resources.map((resource) => (
        <div key={resource.id} className="flex items-center justify-between gap-2 rounded-sm border border-border/40 bg-card/50 px-2 py-1.5">
          <div className="min-w-0 space-y-0.5">
            <div className="flex items-center gap-1.5">
              <LinkIcon className="w-3 h-3 text-muted-foreground shrink-0" />
              <a href={resource.url || undefined} target="_blank" rel="noreferrer" className="text-2xs font-medium truncate hover:underline">
                {resource.title}
              </a>
              <span className="text-2xs text-muted-foreground shrink-0">{resource.type}</span>
            </div>
            {resource.description && (
              <p className="text-2xs text-muted-foreground line-clamp-1">{resource.description}</p>
            )}
          </div>
          <div className="flex items-center gap-1 shrink-0">
            <button
              type="button"
              className="text-2xs text-muted-foreground hover:text-foreground"
              onClick={() => cycleStatus(resource)}
              title="Cycle status"
            >
              {resource.status.replace('_', ' ')}
            </button>
            <Button
              size="icon"
              variant="ghost"
              className="h-5 w-5 text-destructive hover:text-destructive"
              title="Delete resource"
              onClick={() => handleDelete(resource.id)}
            >
              <Trash className="w-3 h-3" />
            </Button>
          </div>
        </div>
      ))}
      <AddResourceDialog open={open} onOpenChange={setOpen} onSubmit={handleAdd} />
    </div>
  )
}