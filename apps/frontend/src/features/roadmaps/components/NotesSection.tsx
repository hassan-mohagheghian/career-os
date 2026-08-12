'use client'

import { useState } from 'react'
import { Note, Plus, Trash } from '@phosphor-icons/react'
import { toast } from 'sonner'
import { useAddNoteMutation, useDeleteNoteMutation } from '@/entities/roadmap/hooks'
import type { RoadmapNote } from '@/entities/roadmap/types'
import { Button } from '@/shared/ui/button'
import { Label } from '@/shared/ui/label'
import { Textarea } from '@/shared/ui/textarea'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/shared/ui/dialog'

export function AddNoteDialog({
  open,
  onOpenChange,
  onSubmit,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSubmit: (content: string) => void
}) {
  const [content, setContent] = useState('')
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Plus className="w-4 h-4" /> Add Note
          </DialogTitle>
          <DialogDescription>Add a note to this milestone.</DialogDescription>
        </DialogHeader>
        <div className="space-y-1">
          <Label htmlFor="note-content">Note</Label>
          <Textarea id="note-content" value={content} onChange={(e) => setContent(e.target.value)} rows={4} />
        </div>
        <DialogFooter>
          <Button
            onClick={() => onSubmit(content)}
            disabled={!content.trim()}
          >
            Add
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// NotesSection scoped to a roadmap subtree (milestone or task). Parent filters
// roadmap.notes by milestone_id / task_id and passes the matching subset.
export function NotesSection({
  roadmapId,
  notes,
  milestoneId,
  taskId,
}: {
  roadmapId: string
  notes: RoadmapNote[]
  milestoneId?: string
  taskId?: string
}) {
  const addNote = useAddNoteMutation()
  const deleteNote = useDeleteNoteMutation()
  const [open, setOpen] = useState(false)

  const handleAdd = (content: string) => {
    addNote.mutate(
      { roadmapId, input: { content, milestone_id: milestoneId ?? null, task_id: taskId ?? null } },
      {
        onSuccess: () => {
          toast.success('Note added')
          setOpen(false)
        },
        onError: () => toast.error('Failed to add note'),
      },
    )
  }

  const handleDelete = (noteId: string) => {
    deleteNote.mutate(noteId, {
      onSuccess: () => toast.success('Note deleted'),
      onError: () => toast.error('Failed to delete note'),
    })
  }

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <p className="text-2xs font-medium text-muted-foreground uppercase tracking-wide inline-flex items-center gap-1">
          <Note className="w-3 h-3" /> Notes ({notes.length})
        </p>
        <Button size="sm" variant="ghost" className="h-6 gap-1 text-2xs" onClick={() => setOpen(true)}>
          <Plus className="w-3 h-3" /> Add
        </Button>
      </div>
      {notes.length === 0 && <p className="text-2xs text-muted-foreground">No notes yet.</p>}
      {notes.map((note) => (
        <div
          key={note.id}
          className="flex items-start justify-between gap-2 rounded-sm border border-border/40 bg-card/50 px-2 py-1.5"
        >
          <p className="text-2xs text-foreground/80 leading-relaxed">{note.content}</p>
          <Button
            size="icon"
            variant="ghost"
            className="h-5 w-5 shrink-0 text-destructive hover:text-destructive"
            title="Delete note"
            onClick={() => handleDelete(note.id)}
          >
            <Trash className="w-3 h-3" />
          </Button>
        </div>
      ))}
      <AddNoteDialog open={open} onOpenChange={setOpen} onSubmit={handleAdd} />
    </div>
  )
}