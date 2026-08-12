'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { MapTrifold, Plus, Trash, PencilSimple } from '@phosphor-icons/react'
import { toast } from 'sonner'
import {
  useRoadmapsQuery,
  useDeleteRoadmapMutation,
} from '@/entities/roadmap/hooks'
import type { RoadmapSummary } from '@/entities/roadmap/types'
import { PageHeader } from '@/shared/components/PageHeader'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Badge } from '@/shared/ui/badge'
import { Progress } from '@/shared/ui/progress'
import ConfirmDialog, { useConfirmDialog } from '@/shared/components/ConfirmDialog'
import { RoadmapCreateDialog } from './RoadmapCreateDialog'
import { RoadmapEditDialog } from './RoadmapEditDialog'

const SOURCE_COLORS: Record<string, string> = {
  APPLICATION: 'bg-blue-500/10 text-blue-600 dark:text-blue-400',
  AI_GENERATED: 'bg-purple-500/10 text-purple-600 dark:text-purple-400',
  MANUAL: 'bg-muted text-muted-foreground',
}

export function RoadmapCard({
  roadmap,
  onOpen,
  onEdit,
  onDelete,
}: {
  roadmap: RoadmapSummary
  onOpen: (id: string) => void
  onEdit: () => void
  onDelete: () => void
}) {
  return (
    <Card className="p-4 space-y-3 hover:ring-foreground/30 transition-shadow">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 space-y-1">
          <div className="flex items-center gap-2">
            <MapTrifold className="w-4 h-4 text-emerald-500 shrink-0" />
            <p className="font-medium text-sm truncate">{roadmap.title}</p>
          </div>
          {roadmap.goal_type && (
            <p className="text-xs text-muted-foreground">Goal: {roadmap.goal_type}</p>
          )}
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          <Badge variant="outline" className={SOURCE_COLORS[roadmap.source]}>
            {roadmap.source}
          </Badge>
          <Badge variant="secondary">{roadmap.status}</Badge>
        </div>
      </div>
      <div className="space-y-1">
        <Progress value={roadmap.progress.overall_percent} />
        <div className="flex items-center justify-between text-2xs text-muted-foreground">
          <span>
            {roadmap.progress.completed_tasks}/{roadmap.progress.total_tasks} tasks done
          </span>
          <span>{roadmap.progress.overall_percent}%</span>
        </div>
      </div>
      <div className="flex items-center gap-1.5">
        <Button size="sm" variant="outline" className="h-7 gap-1 text-xs" onClick={() => onOpen(roadmap.id)}>
          <MapTrifold className="w-3.5 h-3.5" />
          Open
        </Button>
        <Button size="icon" variant="ghost" className="h-7 w-7" onClick={onEdit} title="Edit">
          <PencilSimple className="w-3.5 h-3.5" />
        </Button>
        <Button
          size="icon"
          variant="ghost"
          className="h-7 w-7 text-destructive hover:text-destructive"
          onClick={onDelete}
          title="Delete"
        >
          <Trash className="w-3.5 h-3.5" />
        </Button>
      </div>
    </Card>
  )
}

export function MyRoadmapsPage() {
  const router = useRouter()
  const { data = [], isLoading, isError, refetch } = useRoadmapsQuery()
  const deleteRoadmap = useDeleteRoadmapMutation()
  const { dialog: confirmDialog, showConfirm, onClose: closeConfirm } = useConfirmDialog()

  const [createOpen, setCreateOpen] = useState(false)
  const [editing, setEditing] = useState<RoadmapSummary | null>(null)

  const handleDelete = async (roadmap: RoadmapSummary) => {
    const ok = await showConfirm(
      'Delete Roadmap',
      `Permanently delete "${roadmap.title}" and all its milestones and tasks?`,
      'Delete',
    )
    if (!ok) return
    deleteRoadmap.mutate(roadmap.id, {
      onSuccess: () => toast.success('Roadmap deleted'),
      onError: () => toast.error('Failed to delete roadmap'),
    })
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64 text-muted-foreground">
        Loading roadmaps...
      </div>
    )
  }

  if (isError) {
    return (
      <div className="space-y-4">
        <PageHeader title="My Roadmaps" />
        <div className="flex flex-col items-center justify-center py-16 text-center space-y-3">
          <p className="text-sm text-red-500">Failed to load roadmaps.</p>
          <Button size="sm" variant="outline" onClick={() => refetch()}>Retry</Button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4 p-6">
      <PageHeader title="My Roadmaps">
        <Button size="sm" className="gap-1" onClick={() => setCreateOpen(true)}>
          <Plus className="w-3.5 h-3.5" />
          New Roadmap
        </Button>
      </PageHeader>

      {data.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-24 text-center space-y-3">
          <MapTrifold className="w-10 h-10 text-muted-foreground/50" />
          <div className="space-y-1">
            <p className="text-sm font-medium">No roadmaps yet</p>
            <p className="text-xs text-muted-foreground">
              Create your first learning roadmap or generate one from a job application.
            </p>
          </div>
          <Button size="sm" className="gap-1" onClick={() => setCreateOpen(true)}>
            <Plus className="w-3.5 h-3.5" />
            New Roadmap
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {data.map((roadmap) => (
            <RoadmapCard
              key={roadmap.id}
              roadmap={roadmap}
              onOpen={(id) => router.push(`/roadmaps/${id}`)}
              onEdit={() => setEditing(roadmap)}
              onDelete={() => handleDelete(roadmap)}
            />
          ))}
        </div>
      )}

      <RoadmapCreateDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
      />
      <RoadmapEditDialog
        roadmap={editing}
        open={!!editing}
        onOpenChange={(open) => !open && setEditing(null)}
      />
      <ConfirmDialog dialog={confirmDialog} onClose={closeConfirm} />
    </div>
  )
}